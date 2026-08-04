"""Pipeline GStreamer para reproducir streams RTSP en GTK4."""

from __future__ import annotations

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)


def build_pipeline(camera_name: str, rtsp_url: str) -> Gst.Pipeline:
    pipeline = Gst.Pipeline.new(f"cam-{camera_name}")

    src = Gst.ElementFactory.make("rtspsrc", "src")
    if src is None:
        raise RuntimeError("rtspsrc no disponible — instalá gst-plugins-good")

    depay = Gst.ElementFactory.make("rtph264depay", "depay")
    if depay is None:
        raise RuntimeError("rtph264depay no disponible — instalá gst-plugins-good")

    capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
    caps = Gst.Caps.from_string("video/x-h264,stream-format=avc,alignment=au")
    capsfilter.set_property("caps", caps)

    decoder = Gst.ElementFactory.make("avdec_h264", "decoder")
    if decoder is None:
        raise RuntimeError("avdec_h264 no disponible — instalá gst-libav")

    convert = Gst.ElementFactory.make("videoconvert", "convert")
    sink = Gst.ElementFactory.make("gtk4paintablesink", "sink")
    if sink is None:
        raise RuntimeError("gtk4paintablesink no disponible — instalá gst-plugin-gtk4")

    src.set_property("location", rtsp_url)
    src.set_property("latency", 200)
    src.set_property("timeout", 10_000_000)
    src.set_property("protocols", 4)

    pipeline.add(src)
    pipeline.add(depay)
    pipeline.add(capsfilter)
    pipeline.add(decoder)
    pipeline.add(convert)
    pipeline.add(sink)

    depay.link(capsfilter)
    capsfilter.link(decoder)
    decoder.link(convert)
    convert.link(sink)

    def on_pad_added(_rtspsrc: Gst.Element, pad: Gst.Pad) -> None:
        caps = pad.get_current_caps() or pad.query_caps()
        if caps is None:
            return
        struct = caps.get_structure(0)
        if not struct.get_name().startswith("application/x-rtp"):
            return
        media_type = struct.get_string("media")
        if media_type != "video":
            return
        if not depay.get_static_pad("sink").is_linked():
            pad.link(depay.get_static_pad("sink"))

    src.connect("pad-added", on_pad_added)

    return pipeline
