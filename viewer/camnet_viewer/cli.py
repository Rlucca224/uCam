"""Parseo de argumentos de línea de comandos."""

from __future__ import annotations

import argparse
import os
import sys

from .models import CameraConfig


def parse_cameras() -> list[CameraConfig]:
    """Obtiene cámaras desde --camera o CAMNET_RTSP_URL. Si no hay, retorna vacío."""
    cameras: list[CameraConfig] = []

    parser = argparse.ArgumentParser(description="CamNet — Visor nativo GTK4")
    parser.add_argument(
        "--camera",
        action="append",
        default=[],
        metavar="NOMBRE=URL",
        help="Cámara en formato nombre=rtsp://... (puede repetirse)",
    )
    parser.add_argument("--verbose", action="store_true")
    args, _ = parser.parse_known_args()

    for spec in args.camera:
        if "=" not in spec:
            print(
                f"Error: formato inválido '{spec}'. Usá NOMBRE=rtsp://...",
                file=sys.stderr,
            )
            sys.exit(1)
        name, url = spec.split("=", 1)
        cameras.append(CameraConfig(name=name, rtsp_url=url))

    if not cameras:
        env_url = os.environ.get("CAMNET_RTSP_URL")
        if env_url:
            cameras.append(CameraConfig(name="Camera", rtsp_url=env_url))

    return cameras
