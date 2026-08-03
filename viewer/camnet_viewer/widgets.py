"""Widgets GTK4 del visor de cámaras."""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, GLib  # noqa: E402

from .models import CameraConfig, CameraStatus, CameraState
from .pipeline import build_pipeline

logger = logging.getLogger("camnet.viewer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def icon_button(icon_name: str, label: str, css_class: str) -> Gtk.Button:
    """Botón GTK con icono Material Symbols + texto."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box.set_halign(Gtk.Align.START)

    icon = Gtk.Label(label=icon_name)
    icon.add_css_class("material-icon")
    box.append(icon)

    text = Gtk.Label(label=label)
    text.add_css_class("button-text")
    box.append(text)

    btn = Gtk.Button()
    btn.set_child(box)
    btn.set_halign(Gtk.Align.FILL)
    btn.add_css_class(css_class)
    return btn


# ---------------------------------------------------------------------------
# Reproductor de cámara (pipeline GStreamer compartido)
# ---------------------------------------------------------------------------


class CameraPlayer:
    """Maneja el pipeline GStreamer de una cámara y expone su Gtk.Picture."""

    def __init__(
        self,
        camera: CameraConfig,
        on_status: object | None = None,
        on_info: object | None = None,
    ) -> None:
        self.camera = camera
        self.state = CameraState(config=camera)
        self._on_status = on_status
        self._on_info = on_info

        self._reconnect_delay = 1
        self._reconnect_max_delay = 30
        self._reconnect_source: int | None = None

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
        if w[0] and h[0]:
            self._resolution = f"{w[1]}x{h[1]}"
        fps_num = structure.get_fraction("framerate")
        if fps_num[0]:
            num, denom = fps_num[1].numerator, fps_num[1].denominator
            if denom > 0:
                self._fps_str = f"{num / denom:.0f}"
        encoder = structure.get_string("encoding-name")
        if encoder[0]:
            self._codec = encoder[1]

    def _on_decodebin_pad_added(
        self, _decodebin: Gst.Element, pad: Gst.Pad
    ) -> None:
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
        if self._on_status is not None:
            self._on_status(status)

    def _start_stream(self) -> None:
        try:
            pipeline = build_pipeline(self.camera.name, self.camera.rtsp_url)
        except RuntimeError as exc:
            self._notify_status(CameraStatus.ERROR)
            logger.error("[%s] %s", self.camera.name, exc)
            return

        decodebin = pipeline.get_by_name("decode")
        if decodebin is not None:
            decodebin.connect("pad-added", self._on_decodebin_pad_added)

        sink = pipeline.get_by_name("sink")
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)

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

    def _on_bus_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        logger.warning("[%s] %s", self.camera.name, err.message)
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
            bus = self.state.pipeline.get_bus()
            bus.remove_signal_watch()
            self.state.pipeline.set_state(Gst.State.NULL)
            self.state.pipeline = None
        self._start_time = None

    def stop(self) -> None:
        if self._reconnect_source is not None:
            GLib.source_remove(self._reconnect_source)
            self._reconnect_source = None
        self._stop_pipeline()


# ---------------------------------------------------------------------------
# Tarjeta de cámara
# ---------------------------------------------------------------------------


class CameraCard(Gtk.Box):
    __gtype_name__ = "CameraCard"

    def __init__(self, camera: CameraConfig):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.camera = camera
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(320, 180)
        self.set_overflow(Gtk.Overflow.HIDDEN)

        self.add_css_class("camera-card")

        self._player = CameraPlayer(camera, on_status=self._update_status_ui)
        self._build_ui()
        self._player.start()

    def _build_ui(self) -> None:
        overlay = Gtk.Overlay()
        overlay.add_css_class("camera-feed")
        overlay.set_overflow(Gtk.Overflow.HIDDEN)
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        self.append(overlay)

        main_child = Gtk.Box()
        main_child.set_hexpand(False)
        main_child.set_vexpand(False)
        main_child.set_size_request(320, 180)
        overlay.set_child(main_child)

        overlay.add_overlay(self._player.picture)

        gradient_box = Gtk.Box()
        gradient_box.add_css_class("camera-gradient-top")
        gradient_box.set_valign(Gtk.Align.START)
        gradient_box.set_halign(Gtk.Align.FILL)
        overlay.add_overlay(gradient_box)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_bar.set_margin_start(8)
        top_bar.set_margin_end(8)
        top_bar.set_margin_top(8)
        top_bar.set_valign(Gtk.Align.START)
        top_bar.set_halign(Gtk.Align.FILL)
        overlay.add_overlay(top_bar)

        self._name_label = Gtk.Label(label=self.camera.name)
        self._name_label.add_css_class("camera-name")
        self._name_label.set_halign(Gtk.Align.START)
        self._name_label.set_valign(Gtk.Align.CENTER)
        top_bar.append(self._name_label)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)

        self._status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._status_box.add_css_class("camera-status-tag")
        self._status_box.set_halign(Gtk.Align.END)
        self._status_box.set_valign(Gtk.Align.CENTER)

        self._status_dot = Gtk.Label(label="●")
        self._status_dot.add_css_class("status-dot")
        self._status_dot.set_valign(Gtk.Align.CENTER)
        self._status_box.append(self._status_dot)

        self._status_label = Gtk.Label(label="CON")
        self._status_label.add_css_class("camera-status-text")
        self._status_label.set_valign(Gtk.Align.CENTER)
        self._status_box.append(self._status_label)

        top_bar.append(self._status_box)

        self._no_signal = Gtk.Box()
        self._no_signal.add_css_class("no-signal-overlay")
        self._no_signal.set_valign(Gtk.Align.CENTER)
        self._no_signal.set_halign(Gtk.Align.CENTER)
        self._no_signal.set_visible(True)
        ns_label = Gtk.Label(label="Conectando…")
        ns_label.add_css_class("no-signal-text")
        self._no_signal.append(ns_label)
        overlay.add_overlay(self._no_signal)

    def _update_status_ui(self, status: CameraStatus) -> None:
        color_map = {
            CameraStatus.CONNECTING: "status-connecting",
            CameraStatus.LIVE: "status-live",
            CameraStatus.RECORDING: "status-recording",
            CameraStatus.NO_SIGNAL: "status-no-signal",
            CameraStatus.ERROR: "status-error",
        }
        text_map = {
            CameraStatus.CONNECTING: "CON",
            CameraStatus.LIVE: "LIVE",
            CameraStatus.RECORDING: "REC",
            CameraStatus.NO_SIGNAL: "OFF",
            CameraStatus.ERROR: "ERR",
        }
        css_class = color_map.get(status, "status-connecting")

        for cls in color_map.values():
            self._status_dot.remove_css_class(cls)

        self._status_dot.add_css_class(css_class)
        self._status_label.set_label(text_map.get(status, "---"))
        self._no_signal.set_visible(
            status in (CameraStatus.CONNECTING, CameraStatus.NO_SIGNAL, CameraStatus.ERROR)
        )

    def stop(self) -> None:
        self._player.stop()


# ---------------------------------------------------------------------------
# Fila de cámara (vista de lista)
# ---------------------------------------------------------------------------


class CameraListRow(Gtk.Box):
    __gtype_name__ = "CameraListRow"

    def __init__(self, camera: CameraConfig):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.camera = camera
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_size_request(-1, 220)
        self.set_overflow(Gtk.Overflow.HIDDEN)

        self.add_css_class("camera-list-row")

        self._player = CameraPlayer(
            camera, on_status=self._update_status_ui, on_info=self._update_info
        )
        self._uptime_source: int | None = None
        self._build_ui()
        self._player.start()

    def _build_ui(self) -> None:

        # --- Left: preview ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.set_size_request(400, -1)
        left_box.set_hexpand(False)
        left_box.set_vexpand(False)
        left_box.add_css_class("camera-list-preview-box")
        self.append(left_box)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_bar.set_margin_start(8)
        top_bar.set_margin_end(8)
        top_bar.set_margin_top(8)
        top_bar.set_margin_bottom(6)
        top_bar.set_valign(Gtk.Align.START)
        top_bar.set_halign(Gtk.Align.FILL)
        left_box.append(top_bar)

        self._name_label_preview = Gtk.Label(label=self.camera.name)
        self._name_label_preview.add_css_class("camera-name")
        self._name_label_preview.set_halign(Gtk.Align.START)
        self._name_label_preview.set_valign(Gtk.Align.CENTER)
        top_bar.append(self._name_label_preview)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)

        self._status_box_preview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._status_box_preview.add_css_class("camera-status-tag")
        self._status_box_preview.set_halign(Gtk.Align.END)
        self._status_box_preview.set_valign(Gtk.Align.CENTER)

        self._status_dot_preview = Gtk.Label(label="●")
        self._status_dot_preview.add_css_class("status-dot")
        self._status_dot_preview.set_valign(Gtk.Align.CENTER)
        self._status_box_preview.append(self._status_dot_preview)

        self._status_label_preview = Gtk.Label(label="CON")
        self._status_label_preview.add_css_class("camera-status-text")
        self._status_label_preview.set_valign(Gtk.Align.CENTER)
        self._status_box_preview.append(self._status_label_preview)

        top_bar.append(self._status_box_preview)

        overlay = Gtk.Overlay()
        overlay.add_css_class("camera-list-feed")
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        overlay.set_overflow(Gtk.Overflow.HIDDEN)
        left_box.append(overlay)

        main_child = Gtk.Box()
        main_child.set_hexpand(True)
        main_child.set_vexpand(True)
        main_child.set_size_request(360, 180)
        overlay.set_child(main_child)

        overlay.add_overlay(self._player.picture)

        self._no_signal = Gtk.Box()
        self._no_signal.add_css_class("no-signal-overlay")
        self._no_signal.set_valign(Gtk.Align.CENTER)
        self._no_signal.set_halign(Gtk.Align.CENTER)
        self._no_signal.set_visible(True)
        ns_label = Gtk.Label(label="Conectando…")
        ns_label.add_css_class("no-signal-text")
        self._no_signal.append(ns_label)
        overlay.add_overlay(self._no_signal)

        # --- Right: detail panel ---
        detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        detail.set_hexpand(True)
        detail.set_vexpand(True)
        detail.add_css_class("camera-list-detail")
        detail.set_margin_start(8)
        detail.set_margin_end(8)
        detail.set_margin_top(10)
        detail.set_margin_bottom(10)
        self.append(detail)

        self._detail_name = Gtk.Label(label=self.camera.name)
        self._detail_name.add_css_class("camera-list-detail-title")
        self._detail_name.set_halign(Gtk.Align.START)
        detail.append(self._detail_name)

        self._detail_url = Gtk.Label(label=self.camera.rtsp_url)
        self._detail_url.add_css_class("camera-list-detail-subtitle")
        self._detail_url.set_halign(Gtk.Align.START)
        self._detail_url.set_ellipsize(2)
        self._detail_url.set_margin_bottom(12)
        detail.append(self._detail_url)

        spacer1 = Gtk.Box()
        spacer1.set_vexpand(True)
        spacer1.set_size_request(-1, 8)
        detail.append(spacer1)

        info_grid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_grid.add_css_class("camera-list-info-grid")
        detail.append(info_grid)

        items = [
            ("Resolution", "resolution", "-- x --"),
            ("FPS", "fps", "--"),
            ("Codec", "codec", "--"),
            ("Uptime", "uptime", "--"),
        ]
        self._info_labels: dict[str, Gtk.Label] = {}
        for label, key, default in items:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            l = Gtk.Label(label=f"{label}:")
            l.add_css_class("camera-list-info-label")
            l.set_halign(Gtk.Align.START)
            row.append(l)
            v = Gtk.Label(label=default)
            v.add_css_class("camera-list-info-value")
            v.set_halign(Gtk.Align.START)
            v.set_hexpand(True)
            row.append(v)
            self._info_labels[key] = v
            info_grid.append(row)

        spacer2 = Gtk.Box()
        spacer2.set_vexpand(True)
        spacer2.set_size_request(-1, 8)
        detail.append(spacer2)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        actions.set_valign(Gtk.Align.END)
        detail.append(actions)

        for label in ("Fullscreen", "Reconnect"):
            btn = Gtk.Button(label=label)
            btn.add_css_class("camera-list-action-btn")
            actions.append(btn)

    def _update_status_ui(self, status: CameraStatus) -> None:
        color_map = {
            CameraStatus.CONNECTING: "status-connecting",
            CameraStatus.LIVE: "status-live",
            CameraStatus.RECORDING: "status-recording",
            CameraStatus.NO_SIGNAL: "status-no-signal",
            CameraStatus.ERROR: "status-error",
        }
        text_map = {
            CameraStatus.CONNECTING: "CON",
            CameraStatus.LIVE: "LIVE",
            CameraStatus.RECORDING: "REC",
            CameraStatus.NO_SIGNAL: "OFF",
            CameraStatus.ERROR: "ERR",
        }
        css_class = color_map.get(status, "status-connecting")
        text = text_map.get(status, "---")

        for cls in color_map.values():
            self._status_dot_preview.remove_css_class(cls)
        self._status_dot_preview.add_css_class(css_class)
        self._status_label_preview.set_label(text)

        self._no_signal.set_visible(
            status
            in (CameraStatus.CONNECTING, CameraStatus.NO_SIGNAL, CameraStatus.ERROR)
        )

        if status == CameraStatus.LIVE:
            if self._uptime_source is None:
                self._uptime_source = GLib.timeout_add_seconds(
                    30, self._update_info
                )

    def _update_info(self) -> bool:
        p = self._player
        self._info_labels["resolution"].set_label(p.resolution)
        self._info_labels["fps"].set_label(p.fps)
        self._info_labels["codec"].set_label(p.codec)
        self._info_labels["uptime"].set_label(p.uptime)
        return True

    def stop(self) -> None:
        if self._uptime_source is not None:
            GLib.source_remove(self._uptime_source)
            self._uptime_source = None
        self._player.stop()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


class Sidebar(Gtk.Box):
    __gtype_name__ = "Sidebar"

    def __init__(self, on_add_device: object = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add_css_class("sidebar")
        self.set_size_request(256, -1)
        self._on_add_device = on_add_device

        self._build_header()
        self._build_nav()
        self._build_bottom()

    def _build_header(self) -> None:
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(12)
        header.set_margin_bottom(16)
        self.append(header)

        logo = Gtk.Label(label="uCam")
        logo.add_css_class("sidebar-logo")
        logo.set_halign(Gtk.Align.START)
        header.append(logo)

        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.append(status_row)

        dot = Gtk.Label(label="●")
        dot.add_css_class("status-dot")
        dot.add_css_class("status-live")
        dot.set_valign(Gtk.Align.CENTER)
        status_row.append(dot)

        status_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        st = Gtk.Label(label="System Active")
        st.add_css_class("sidebar-status-title")
        st.set_halign(Gtk.Align.START)
        status_text.append(st)
        ss = Gtk.Label(label="1 Camera Online")
        ss.add_css_class("sidebar-status-subtitle")
        ss.set_halign(Gtk.Align.START)
        self._camera_count_label = ss
        status_text.append(ss)
        status_row.append(status_text)

    def _build_nav(self) -> None:
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        nav.set_margin_start(8)
        nav.set_margin_end(8)
        nav.set_vexpand(True)
        self.append(nav)

        add_btn = icon_button("add_circle", "Add Device", "sidebar-add-btn")
        if self._on_add_device:
            add_btn.connect("clicked", lambda _b: self._on_add_device())
        nav.append(add_btn)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(12)
        sep.set_margin_bottom(8)
        sep.add_css_class("sidebar-separator")
        nav.append(sep)

        items = [
            ("dashboard", "Dashboard", False),
            ("videocam", "Cameras", True),
            ("video_library", "Recordings", False),
            ("warning", "Events", False),
            ("tune", "Camera Management", False),
        ]
        for icon, label, active in items:
            css = "nav-item-active" if active else "nav-item"
            btn = icon_button(icon, label, css)
            nav.append(btn)

    def _build_bottom(self) -> None:
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        bottom.set_margin_start(8)
        bottom.set_margin_end(8)
        bottom.set_margin_top(8)
        bottom.set_margin_bottom(16)
        bottom.set_vexpand(False)
        bottom.set_vexpand_set(True)
        bottom.set_size_request(-1, 100)
        bottom.add_css_class("sidebar-bottom")
        self.append(bottom)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        bottom.append(spacer)

        bottom_items = [
            ("settings", "Settings"),
            ("help", "Support"),
            ("logout", "Sign Out"),
        ]
        for icon, label in bottom_items:
            btn = icon_button(icon, label, "nav-item")
            bottom.append(btn)

    def set_camera_count(self, count: int) -> None:
        s = "s" if count != 1 else ""
        self._camera_count_label.set_label(f"{count} Camera{s} Online")


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------


class TopBar(Gtk.Box):
    __gtype_name__ = "TopBar"

    def __init__(self, on_layout_change: object | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("topbar")
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        self._on_layout_change = on_layout_change
        self._current_layout = "grid"

        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        all_btn = Gtk.Button(label="All Cameras")
        all_btn.add_css_class("tab-active")
        tabs.append(all_btn)
        fav_btn = Gtk.Button(label="Favorites")
        fav_btn.add_css_class("tab-inactive")
        tabs.append(fav_btn)
        self.append(tabs)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.append(spacer)

        layout_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        layout_label = Gtk.Label(label="Layout:")
        layout_label.add_css_class("layout-label")
        layout_row.append(layout_label)

        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        toggle_box.add_css_class("layout-toggle")

        self._grid_btn = Gtk.Button(label="grid_view")
        self._grid_btn.add_css_class("layout-btn-active")
        self._grid_btn.add_css_class("material-icon")
        self._grid_btn.connect("clicked", self._on_grid_clicked)
        toggle_box.append(self._grid_btn)

        self._list_btn = Gtk.Button(label="splitscreen")
        self._list_btn.add_css_class("layout-btn-inactive")
        self._list_btn.add_css_class("material-icon")
        self._list_btn.connect("clicked", self._on_list_clicked)
        toggle_box.append(self._list_btn)

        layout_row.append(toggle_box)
        self.append(layout_row)

    def _set_layout(self, layout: str) -> None:
        if layout == self._current_layout:
            return
        self._current_layout = layout
        if layout == "grid":
            self._grid_btn.remove_css_class("layout-btn-inactive")
            self._grid_btn.add_css_class("layout-btn-active")
            self._list_btn.remove_css_class("layout-btn-active")
            self._list_btn.add_css_class("layout-btn-inactive")
        else:
            self._list_btn.remove_css_class("layout-btn-inactive")
            self._list_btn.add_css_class("layout-btn-active")
            self._grid_btn.remove_css_class("layout-btn-active")
            self._grid_btn.add_css_class("layout-btn-inactive")
        if self._on_layout_change is not None:
            self._on_layout_change(layout)

    def _on_grid_clicked(self, _btn: Gtk.Button) -> None:
        self._set_layout("grid")

    def _on_list_clicked(self, _btn: Gtk.Button) -> None:
        self._set_layout("list")


# ---------------------------------------------------------------------------
# Grid de cámaras
# ---------------------------------------------------------------------------


class CameraGrid(Gtk.Box):
    __gtype_name__ = "CameraGrid"

    def __init__(self, cameras: list[CameraConfig]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._cameras = list(cameras)
        self._cards: list[CameraCard] = []
        self._rows: list[CameraListRow] = []
        self._layout = "grid"
        self.add_css_class("camera-grid-container")

        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.set_vexpand(True)
        self._scrolled.set_hexpand(True)
        self._scrolled.set_has_frame(False)
        self.append(self._scrolled)

        self._flow = Gtk.FlowBox()
        self._flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self._flow.set_max_children_per_line(10)
        self._flow.set_min_children_per_line(1)
        self._flow.set_row_spacing(8)
        self._flow.set_column_spacing(8)
        self._flow.set_margin_start(12)
        self._flow.set_margin_end(12)
        self._flow.set_margin_top(8)
        self._flow.set_margin_bottom(12)
        self._flow.set_homogeneous(False)
        self._flow.set_valign(Gtk.Align.START)
        self._flow.set_halign(Gtk.Align.START)
        self._flow.add_css_class("camera-flow")

        self._list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._list_box.set_margin_start(12)
        self._list_box.set_margin_end(12)
        self._list_box.set_margin_top(8)
        self._list_box.set_margin_bottom(12)
        self._list_box.set_hexpand(True)
        self._list_box.set_vexpand(False)
        self._list_box.set_valign(Gtk.Align.START)
        self._list_box.set_halign(Gtk.Align.FILL)
        self._list_box.add_css_class("camera-list-container")

        self._build_grid()
        self._build_list()
        self._show_layout("grid")

    def _build_grid(self) -> None:
        for card in self._cards:
            self._flow.remove(card)
        self._cards.clear()
        for cam in self._cameras:
            card = CameraCard(cam)
            self._cards.append(card)
            self._flow.append(card)

    def _build_list(self) -> None:
        for row in self._rows:
            self._list_box.remove(row)
        self._rows.clear()
        for cam in self._cameras:
            row = CameraListRow(cam)
            self._rows.append(row)
            self._list_box.append(row)

    def _show_layout(self, layout: str) -> None:
        self._layout = layout
        if layout == "grid":
            self._scrolled.set_child(self._flow)
        else:
            self._scrolled.set_child(self._list_box)

    def set_layout(self, layout: str) -> None:
        if layout == self._layout:
            return
        if layout not in ("grid", "list"):
            return
        self._show_layout(layout)

    def add_camera(self, camera: CameraConfig) -> None:
        self._cameras.append(camera)
        card = CameraCard(camera)
        self._cards.append(card)
        self._flow.append(card)
        row = CameraListRow(camera)
        self._rows.append(row)
        self._list_box.append(row)

    def shutdown(self) -> None:
        for card in self._cards:
            card.stop()
        for row in self._rows:
            row.stop()
