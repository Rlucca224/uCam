"""Widgets GTK4 del visor de cámaras."""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst  # noqa: E402

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
# Tarjeta de cámara
# ---------------------------------------------------------------------------


class CameraCard(Gtk.Box):
    __gtype_name__ = "CameraCard"

    def __init__(self, camera: CameraConfig):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.camera = camera
        self.state = CameraState(config=camera)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(320, 180)
        self.set_overflow(Gtk.Overflow.HIDDEN)

        self.add_css_class("camera-card")

        self._build_ui()
        self._start_stream()

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

        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.COVER)
        self._picture.add_css_class("camera-video")
        self._picture.set_halign(Gtk.Align.FILL)
        self._picture.set_valign(Gtk.Align.FILL)
        overlay.add_overlay(self._picture)

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

    def _start_stream(self) -> None:
        try:
            pipeline = build_pipeline(self.camera.name, self.camera.rtsp_url)
        except RuntimeError as exc:
            self._update_status_ui(CameraStatus.ERROR)
            logger.error("[%s] %s", self.camera.name, exc)
            return

        sink = pipeline.get_by_name("sink")
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)
            self._no_signal.set_visible(False)

        sink.connect("notify::paintable", self._on_paintable_notify)

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_bus_error)
        bus.connect("message::state-changed", self._on_bus_state_changed)
        bus.connect("message::eos", self._on_bus_eos)

        self.state.pipeline = pipeline
        pipeline.set_state(Gst.State.PLAYING)

    def _on_paintable_notify(self, sink, _pspec) -> None:
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)
            self._no_signal.set_visible(False)
            self._update_status_ui(CameraStatus.LIVE)

    def _on_bus_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        logger.error("[%s] %s", self.camera.name, err.message)
        self._update_status_ui(CameraStatus.ERROR)

    def _on_bus_eos(self, _bus: Gst.Bus, _msg: Gst.Message) -> None:
        logger.info("[%s] End of stream", self.camera.name)
        self._update_status_ui(CameraStatus.NO_SIGNAL)

    def _on_bus_state_changed(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        if msg.src != self.state.pipeline:
            return
        _old, new, _pending = msg.parse_state_changed()
        if new == Gst.State.PLAYING:
            self._update_status_ui(CameraStatus.LIVE)
        elif new == Gst.State.NULL:
            self._update_status_ui(CameraStatus.NO_SIGNAL)

    def stop(self) -> None:
        if self.state.pipeline is not None:
            self.state.pipeline.set_state(Gst.State.NULL)
            self.state.pipeline = None


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
            ("event", "Events", False),
            ("linked_camera", "Camera Management", False),
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


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------


    def set_camera_count(self, count: int) -> None:
        s = "s" if count != 1 else ""
        self._camera_count_label.set_label(f"{count} Camera{s} Online")


class TopBar(Gtk.Box):
    __gtype_name__ = "TopBar"

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("topbar")
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

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

        grid_btn = Gtk.Button(label="grid_view")
        grid_btn.add_css_class("layout-btn-active")
        grid_btn.add_css_class("material-icon")
        toggle_box.append(grid_btn)

        split_btn = Gtk.Button(label="splitscreen")
        split_btn.add_css_class("layout-btn-inactive")
        split_btn.add_css_class("material-icon")
        toggle_box.append(split_btn)

        layout_row.append(toggle_box)
        self.append(layout_row)


# ---------------------------------------------------------------------------
# Grid de cámaras
# ---------------------------------------------------------------------------


class CameraGrid(Gtk.Box):
    __gtype_name__ = "CameraGrid"

    def __init__(self, cameras: list[CameraConfig]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._cards: list[CameraCard] = []
        self.add_css_class("camera-grid-container")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_has_frame(False)
        self.append(scrolled)

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
        scrolled.set_child(self._flow)

        for cam in cameras:
            card = CameraCard(cam)
            self._cards.append(card)
            self._flow.append(card)

    def add_camera(self, camera: CameraConfig) -> None:
        card = CameraCard(camera)
        self._cards.append(card)
        self._flow.append(card)

    def shutdown(self) -> None:
        for card in self._cards:
            card.stop()
