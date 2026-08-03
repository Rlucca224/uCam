"""Descubrimiento de perfiles ONVIF y sus URLs RTSP."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger("camnet.viewer")


try:
    from onvif import ONVIFCamera
    import onvif as _onvif_pkg

    _ONVIF_DIR = os.path.dirname(_onvif_pkg.__file__)
    _WSDL_DIR = os.path.join(os.path.dirname(_ONVIF_DIR), "wsdl")
    if not os.path.isdir(_WSDL_DIR):
        _WSDL_DIR = os.path.join(_ONVIF_DIR, "wsdl")
except Exception as exc:  # pragma: no cover - se detecta en runtime
    logger.warning("onvif-zeep no disponible: %s", exc)
    ONVIFCamera = None
    _WSDL_DIR = ""


@dataclass
class StreamProfile:
    """Perfil de streaming ONVIF."""

    name: str
    token: str
    resolution: str
    url: str
    encoding: str = ""
    fps: int = 0


def _parse_endpoint(endpoint: str) -> tuple[str, int]:
    """Extrae host y puerto de un endpoint ONVIF."""
    parsed = urlparse(endpoint)
    host = parsed.hostname or endpoint.split(":")[0].replace("http://", "").replace("https://", "")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _extract_profile(p) -> StreamProfile | None:
    """Convierte un perfil ONVIF en StreamProfile."""
    try:
        token = p.token
        name = getattr(p, "Name", token)

        # Resolución
        width = height = 0
        enc = getattr(p, "VideoEncoderConfiguration", None)
        if enc is not None:
            res = getattr(enc, "Resolution", None)
            if res is not None:
                width = getattr(res, "Width", 0)
                height = getattr(res, "Height", 0)
        resolution = f"{width}x{height}" if width and height else "--"

        # Codec y FPS
        encoding = ""
        fps = 0
        if enc is not None:
            encoding = getattr(enc, "Encoding", "")
            rate = getattr(enc, "RateControl", None)
            if rate is not None:
                fps = getattr(rate, "FrameRateLimit", 0)

        return StreamProfile(
            name=str(name),
            token=str(token),
            resolution=resolution,
            url="",
            encoding=str(encoding).upper(),
            fps=int(fps),
        )
    except Exception as exc:
        logger.warning("ONVIF: no se pudo parsear perfil: %s", exc)
        return None


def discover_onvif_streams(
    endpoint: str,
    user: str,
    password: str,
    timeout: int = 10,
) -> list[StreamProfile]:
    """Descubre perfiles RTSP disponibles en una cámara ONVIF."""
    if ONVIFCamera is None:
        raise RuntimeError("onvif-zeep no está instalado")

    host, port = _parse_endpoint(endpoint)
    logger.info("ONVIF: conectando a %s:%d", host, port)

    wsdl_dir = _WSDL_DIR if _WSDL_DIR and os.path.isdir(_WSDL_DIR) else None
    cam = ONVIFCamera(host, port, user, password, wsdl_dir=wsdl_dir)
    cam.update_xaddrs()
    media = cam.create_media_service()

    profiles = media.GetProfiles()
    if not profiles:
        return []

    stream_setup = {
        "Stream": "RTP-Unicast",
        "Transport": {"Protocol": "RTSP"},
    }

    results: list[StreamProfile] = []
    for p in profiles:
        profile = _extract_profile(p)
        if profile is None:
            continue

        try:
            uri = media.GetStreamUri(
                {"ProfileToken": profile.token, "StreamSetup": stream_setup}
            )
            profile.url = str(uri.Uri)
        except Exception as exc:
            logger.warning(
                "ONVIF: no se pudo obtener URI para %s: %s", profile.token, exc
            )
            continue

        results.append(profile)

    return results
