"""Camera grid widget that switches between grid and list layouts."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from ..models import CameraConfig
from .camera_card import CameraCard
from .camera_list_row import CameraListRow
from .camera_player import CameraPlayer


class CameraGrid(Gtk.Box):
    __gtype_name__ = "CameraGrid"

    def __init__(self, cameras: list[CameraConfig]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._cameras = list(cameras)
        self._players: dict[str, CameraPlayer] = {}
        self._cards: list[CameraCard] = []
        self._rows: list[CameraListRow] = []
        self._layout = ""
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

        self._list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._list_box.set_margin_start(12)
        self._list_box.set_margin_end(12)
        self._list_box.set_margin_top(8)
        self._list_box.set_margin_bottom(12)
        self._list_box.set_hexpand(True)
        self._list_box.set_vexpand(False)
        self._list_box.set_valign(Gtk.Align.START)
        self._list_box.set_halign(Gtk.Align.FILL)
        self._list_box.add_css_class("camera-list-container")

        for cam in self._cameras:
            player = CameraPlayer(cam)
            self._players[cam.rtsp_url] = player

        self._build_grid()
        self._build_list()
        self._show_layout("grid")

        for player in self._players.values():
            player.start()

    def _build_grid(self) -> None:
        for card in self._cards:
            self._flow.remove(card)
        self._cards.clear()
        for cam in self._cameras:
            player = self._players[cam.rtsp_url]
            card = CameraCard(cam, player=player)
            self._cards.append(card)
            self._flow.append(card)

    def _build_list(self) -> None:
        for row in self._rows:
            self._list_box.remove(row)
        self._rows.clear()
        for cam in self._cameras:
            player = self._players[cam.rtsp_url]
            row = CameraListRow(cam, player=player)
            self._rows.append(row)
            self._list_box.append(row)

    def _show_layout(self, layout: str) -> None:
        if layout == self._layout:
            return
        if layout == "grid":
            self._scrolled.set_child(self._flow)
        else:
            self._scrolled.set_child(self._list_box)
        self._layout = layout

    def set_layout(self, layout: str) -> None:
        if layout not in ("grid", "list"):
            return
        self._show_layout(layout)

    def add_camera(self, camera: CameraConfig) -> None:
        self._cameras.append(camera)
        player = CameraPlayer(camera)
        self._players[camera.rtsp_url] = player

        card = CameraCard(camera, player=player)
        self._cards.append(card)
        self._flow.append(card)

        row = CameraListRow(camera, player=player)
        self._rows.append(row)
        self._list_box.append(row)

        player.start()

    def shutdown(self) -> None:
        for card in self._cards:
            card.stop()
        for row in self._rows:
            row.stop()
        for player in self._players.values():
            player.stop()
