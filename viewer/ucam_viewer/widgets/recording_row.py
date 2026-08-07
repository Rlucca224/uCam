"""Recording list row widget."""

from __future__ import annotations

import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Gdk, Gio, GLib  # noqa: E402

from ..recordings import (
    RecordingInfo,
    discover_duration,
    format_datetime,
    format_duration,
    generate_thumbnail,
    human_size,
    thumbnail_for,
)
from .helpers import icon_button


class RecordingRow(Gtk.Box):
    __gtype_name__ = "RecordingRow"

    def __init__(
        self,
        recording: RecordingInfo,
        on_play: object = None,
        on_open_folder: object = None,
        on_delete: object = None,
        on_select: object = None,
        select_mode: bool = False,
        is_active: bool = False,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.recording = recording
        self._on_play = on_play
        self._on_open_folder = on_open_folder
        self._on_delete = on_delete
        self._on_select = on_select
        self._select_mode = select_mode
        self._selected = False
        self.is_active = is_active
        self.set_hexpand(True)
        self.set_hexpand_set(True)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_bottom(8)
        self.add_css_class("recording-row")

        gesture = Gtk.GestureClick()
        gesture.connect("released", self._on_row_clicked)
        self.add_controller(gesture)

        self._build_ui()
        self._load_thumb()
        self._load_duration()

    def set_select_mode(self, mode: bool) -> None:
        self._select_mode = mode
        self._check.set_visible(mode)

    def set_selected(self, selected: bool) -> None:
        if self._check.get_active() != selected:
            self._check.set_active(selected)
        else:
            self._update_selected_ui()

    def _update_selected_ui(self) -> None:
        self._selected = self._check.get_active()
        if self._selected:
            self.add_css_class("recording-row-selected")
        else:
            self.remove_css_class("recording-row-selected")

    def _on_row_clicked(self, _gesture, _n_press: int, x: float, y: float) -> None:
        if not self._select_mode:
            return
        picked = self.pick(x, y, Gtk.PickFlags.DEFAULT)
        node = picked
        while node is not None and node is not self:
            if node is self._check or node is self._actions or isinstance(node, Gtk.Button):
                return
            node = node.get_parent()
        self.set_selected(not self._check.get_active())

    def _on_toggled(self, _check) -> None:
        self._update_selected_ui()
        if self._on_select is not None:
            self._on_select(self.recording, self._selected)

    def _build_ui(self) -> None:
        self._check = Gtk.CheckButton()
        self._check.add_css_class("recording-check")
        self._check.set_visible(self._select_mode)
        self._check.set_valign(Gtk.Align.CENTER)
        self._check.connect("toggled", self._on_toggled)
        self.append(self._check)

        thumb_box = Gtk.Overlay()
        thumb_box.add_css_class("recording-thumb")
        thumb_box.set_size_request(160, 90)

        self._thumb_picture = Gtk.Picture()
        self._thumb_picture.set_size_request(160, 90)
        self._thumb_picture.set_can_shrink(True)
        self._thumb_picture.set_content_fit(Gtk.ContentFit.COVER)
        thumb_box.set_child(self._thumb_picture)

        self._thumb_icon = Gtk.Label(label="video_library")
        self._thumb_icon.add_css_class("material-icon")
        self._thumb_icon.add_css_class("recording-thumb-icon")
        self._thumb_icon.set_valign(Gtk.Align.CENTER)
        thumb_box.add_overlay(self._thumb_icon)
        self.append(thumb_box)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_hexpand(True)
        info.set_hexpand_set(True)
        info.set_valign(Gtk.Align.CENTER)
        self.append(info)

        self._name_label = Gtk.Label(label=self.recording.camera_name)
        self._name_label.add_css_class("recording-name")
        self._name_label.set_halign(Gtk.Align.START)
        info.append(self._name_label)

        ts = Gtk.Label(label=format_datetime(self.recording.timestamp))
        ts.add_css_class("recording-meta")
        ts.set_halign(Gtk.Align.START)
        info.append(ts)

        self._meta_label = Gtk.Label(
            label=f"{human_size(self.recording.size)} · {format_duration(None)}"
        )
        self._meta_label.add_css_class("recording-meta")
        self._meta_label.set_halign(Gtk.Align.START)
        info.append(self._meta_label)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        actions.set_valign(Gtk.Align.CENTER)
        self._actions = actions
        self.append(actions)

        play = icon_button("play_arrow", "Play", "recording-action-btn")
        play.connect("clicked", lambda _b: self._on_play(self.recording))
        actions.append(play)

        folder = icon_button("folder_open", "Folder", "recording-action-btn")
        folder.connect("clicked", lambda _b: self._on_open_folder(self.recording))
        actions.append(folder)

        delete = icon_button("delete", "Delete", "recording-action-btn-danger")
        delete.connect("clicked", lambda _b: self._on_delete(self.recording))
        delete.set_sensitive(not self.is_active)
        actions.append(delete)

    def _load_thumb(self) -> None:
        cached = thumbnail_for(self.recording.path)
        if cached is not None:
            GLib.idle_add(self._apply_thumb, cached)
            return

        path = self.recording.path

        def work() -> None:
            t = generate_thumbnail(path)
            GLib.idle_add(self._apply_thumb, t)

        threading.Thread(target=work, daemon=True).start()

    def _apply_thumb(self, thumb: Path) -> None:
        if self.get_root() is None:
            return
        try:
            texture = Gdk.Texture.new_from_file(
                Gio.File.new_for_path(str(thumb))
            )
        except GLib.Error:
            return
        self._thumb_icon.set_visible(False)
        self._thumb_picture.set_paintable(texture)

    def _load_duration(self) -> None:
        path = self.recording.path

        def work() -> None:
            duration = discover_duration(path)
            if duration is not None:
                self.recording.duration = duration
                GLib.idle_add(self._apply_duration, duration)

        threading.Thread(target=work, daemon=True).start()

    def _apply_duration(self, duration: float) -> None:
        if self.get_root() is None:
            return
        self._meta_label.set_label(
            f"{human_size(self.recording.size)} · {format_duration(duration)}"
        )
