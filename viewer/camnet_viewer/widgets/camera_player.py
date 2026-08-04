"""GStreamer camera player widget."""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, GLib  # noqa: E402

from ..models import CameraConfig, CameraStatus, CameraState
from ..pipeline import build_pipeline

logger = logging.getLogger("camnet.viewer")


class CameraPlayer:
    """Handles the GStreamer pipeline for a camera and exposes its Gtk.Picture."""

    def __init__(self, camera: CameraConfig) -> None:
        self.camera = camera
        self.state = CameraState(config=camera)
        self._status_listeners: list = []
        self._paintable_listeners: list = []
        self._on_info: object | None = None

        self._reconnect_delay = 1
        self._reconnect_max_delay = 30
        self._reconnect_source: int | None = None

        self._use_decodebin3 = True
        self._switched_decodebin = False

        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.COVER)
        self._picture.add_css_class("camera-video")
        self._picture.set_halign(Gtk.Align.FILL)
        self._picture.set_valign(Gtk.Align.FILL)

        self._resolution = "--"
        self._fps_str = "--"
        self._codec = "--"
        self._start_time: float | None = None

    @property
    def picture(self) -> Gtk.Picture:
        return self._picture

    @property
    def resolution(self) -> str:
        return self._resolution

    @property
    def fps(self) -> str:
        return self._fps_str

    @property
    def codec(self) -> str:
        return self._codec

    @property
    def uptime_seconds(self) -> int:
        if self._start_time is None:
            return 0
        import time
        return int(time.time() - self._start_time)

    @property
    def uptime(self) -> str:
        secs = self.uptime_seconds
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        if mins < 60:
            return f"{mins}min"
        hours = mins // 60
        return f"{hours}h {mins % 60}min"

    def add_status_listener(self, cb: object) -> None:
        self._status_listeners.append(cb)

    def add_paintable_listener(self, cb: object) -> None:
        self._paintable_listeners.append(cb)

    def add_info_listener(self, cb: object) -> None:
        self._on_info = cb

    def start(self) -> None:
        self._start_stream()

    def _notify_info(self) -> None:
        if self._on_info is not None:
            self._on_info()

    def _extract_caps_info(self, caps: Gst.Caps) -> None:
        if caps.get_size() == 0:
            return
        structure = caps.get_structure(0)

        w = structure.get_int("width")
        h = structure.get_int("height")
        if w and h and w[0] and h[0]:
            self._resolution = f"{w[1]}x{h[1]}"

        fps_num = structure.get_fraction("framerate")
        if fps_num and fps_num[0]:
            f = fps_num[1]
            if f.denominator > 0:
                self._fps_str = f"{f.numerator / f.denominator:.0f}"

        name = structure.get_name()
        if name and "/" in name:
            self._codec = name.split("/")[-1].upper()

    def _on_decodebin_pad_added(self, _decodebin: Gst.Element, pad: Gst.Pad) -> None:
        caps = pad.get_current_caps()
        if caps is None:
            caps = pad.get_allowed_caps()
        if caps is not None:
            name = caps.to_string().split(",")[0] if caps.to_string() else ""
            if "video" in name:
                self._extract_caps_info(caps)
                self._notify_info()
        pad.add_probe(
            Gst.PadProbeType.EVENT_DOWNSTREAM, self._on_video_pad_probe, None
        )

    def _on_video_pad_probe(
        self,
        _pad: Gst.Pad,
        info: Gst.PadProbeInfo,
        _user_data: object,
    ) -> Gst.PadProbeReturn:
        evt = info.get_event()
        if evt is not None and evt.type == Gst.EventType.CAPS:
            caps = evt.parse_caps()
            self._extract_caps_info(caps)
            self._notify_info()
        return Gst.PadProbeReturn.OK

    def _notify_status(self, status: CameraStatus) -> None:
        self.state.status = status
        if status == CameraStatus.LIVE and self._start_time is None:
            import time
            self._start_time = time.time()
        for cb in self._status_listeners:
            cb(status)

    def _start_stream(self) -> None:
        try:
            pipeline = build_pipeline(
                self.camera.name, self.camera.rtsp_url, self._use_decodebin3
            )
        except RuntimeError as exc:
            self._notify_status(CameraStatus.ERROR)
            logger.error("[%s] %s", self.camera.name, exc)
            return

        decode = pipeline.get_by_name("decode")
        if decode is not None:
            decode.connect("pad-added", self._on_decodebin_pad_added)

        sink = pipeline.get_by_name("sink")
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)
            for cb in self._paintable_listeners:
                cb(paintable)

        sink.connect("notify::paintable", self._on_paintable_notify)

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_bus_error)
        bus.connect("message::state-changed", self._on_bus_state_changed)
        bus.connect("message::eos", self._on_bus_eos)

        self.state.pipeline = pipeline
        self._notify_status(CameraStatus.CONNECTING)
        pipeline.set_state(Gst.State.PLAYING)

    def _on_paintable_notify(self, sink, _pspec) -> None:
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)
            self._notify_status(CameraStatus.LIVE)
            for cb in self._paintable_listeners:
                cb(paintable)

    def _on_bus_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        logger.warning("[%s] %s", self.camera.name, err.message)
        if not self._switched_decodebin and self._use_decodebin3:
            msg_lower = err.message.lower()
            if "no caps set" in msg_lower or "broken bit stream" in msg_lower:
                self._use_decodebin3 = False
                self._switched_decodebin = True
                logger.info("[%s] Fallback to decodebin", self.camera.name)
                self._schedule_reconnect()
                return
        self._schedule_reconnect()

    def _on_bus_eos(self, _bus: Gst.Bus, _msg: Gst.Message) -> None:
        logger.info("[%s] End of stream", self.camera.name)
        self._schedule_reconnect()

    def _on_bus_state_changed(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        if msg.src != self.state.pipeline:
            return
        _old, new, _pending = msg.parse_state_changed()
        if new == Gst.State.PLAYING:
            self._notify_status(CameraStatus.LIVE)
            self._reconnect_delay = 1
        elif new == Gst.State.NULL:
            self._notify_status(CameraStatus.NO_SIGNAL)

    def _schedule_reconnect(self) -> None:
        if self._reconnect_source is not None:
            return
        if self._reconnect_delay >= self._reconnect_max_delay:
            self._notify_status(CameraStatus.ERROR)
            self._reconnect_delay = self._reconnect_max_delay
        else:
            self._notify_status(CameraStatus.CONNECTING)
        self._reconnect_source = GLib.timeout_add_seconds(
            self._reconnect_delay, self._do_reconnect
        )

    def _do_reconnect(self) -> bool:
        self._reconnect_source = None
        self._stop_pipeline()
        self._notify_status(CameraStatus.CONNECTING)
        self._reconnect_delay = min(self._reconnect_delay * 2, self._reconnect_max_delay)
        self._start_stream()
        return False

    def _stop_pipeline(self) -> None:
        if self.state.pipeline is not None:
            self._picture.set_paintable(None)
            self.state.pipeline.set_state(Gst.State.NULL)
            self.state.pipeline.get_state(Gst.SECOND)
            bus = self.state.pipeline.get_bus()
            bus.remove_signal_watch()
            self.state.pipeline = None
        self._start_time = None

    def stop(self) -> None:
        if self._reconnect_source is not None:
            GLib.source_remove(self._reconnect_source)
            self._reconnect_source = None
        self._stop_pipeline()

    def clear_picture(self) -> None:
        self._picture.set_paintable(None)
