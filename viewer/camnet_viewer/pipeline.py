"""Pipeline GStreamer para reproducir streams RTSP en GTK4."""

from __future__ import annotations

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)


def build_pipeline(camera_name: str, rtsp_url: str) -> Gst.Pipeline:
    """Construye el pipeline: rtspsrc -> decodebin -> videoconvert -> gtk4paintablesink."""
    pipeline = Gst.Pipeline.new(f"cam-{camera_name}")

    src = Gst.ElementFactory.make("rtspsrc", "src")
    if src is None:
        raise RuntimeError("rtspsrc no disponible — instalá gst-plugins-good")
    src.set_property("location", rtsp_url)
    src.set_property("latency", 200)
    src.set_property("timeout", 10_000_000)
    # Forzar TCP mejora compatibilidad con cámaras sin auth y firewalls
    src.set_property("protocols", Gst.RTSPLowerTrans.TCP)

    decode = Gst.ElementFactory.make("decodebin", "decode")
    convert = Gst.ElementFactory.make("videoconvert", "convert")
    sink = Gst.ElementFactory.make("gtk4paintablesink", "sink")
    if sink is None:
        raise RuntimeError("gtk4paintablesink no disponible — instalá gst-plugin-gtk4")

    pipeline.add(src)
    pipeline.add(decode)
    pipeline.add(convert)
    pipeline.add(sink)
    convert.link(sink)

    def on_rtsp_pad_added(_rtspsrc: Gst.Element, pad: Gst.Pad) -> None:
        caps = pad.get_current_caps() or pad.query_caps()
        if caps is None:
            return
        struct = caps.get_structure(0)
        name = struct.get_name()
        if not name.startswith("application/x-rtp"):
            return
        sinkpad = decode.get_static_pad("sink")
        if not sinkpad.is_linked():
            pad.link(sinkpad)

    def on_decode_pad_added(_decodebin: Gst.Element, pad: Gst.Pad) -> None:
        caps = pad.get_current_caps() or pad.query_caps()
        if caps is None:
            return
        struct = caps.get_structure(0)
        if struct.get_name().startswith("video/"):
            sinkpad = convert.get_static_pad("sink")
            if not sinkpad.is_linked():
                pad.link(sinkpad)

    src.connect("pad-added", on_rtsp_pad_added)
    decode.connect("pad-added", on_decode_pad_added)

    return pipeline
