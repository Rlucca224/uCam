"""Top bar widget for the camera viewer."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402


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
