"""Sidebar widget for the camera viewer."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from .helpers import icon_button


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
