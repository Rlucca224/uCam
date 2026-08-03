"""Camera card widget for grid view."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from ..models import CameraConfig, CameraStatus
from .camera_player import CameraPlayer


class CameraCard(Gtk.Box):
    __gtype_name__ = "CameraCard"

    def __init__(self, camera: CameraConfig, player: CameraPlayer | None = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.camera = camera
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(320, 180)
        self.set_overflow(Gtk.Overflow.HIDDEN)

        self.add_css_class("camera-card")

        self._own_player = player is None
        self._player = player or CameraPlayer(camera)
        self._player.add_status_listener(self._update_status_ui)
        self._player.add_paintable_listener(self._on_paintable)
        self._build_ui()
        if self._own_player:
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

    def _on_paintable(self, paintable: object) -> None:
        self._picture.set_paintable(paintable)

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
        self._picture.set_paintable(None)
        if self._own_player:
            self._player.stop()
