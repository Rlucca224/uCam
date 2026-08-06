"""Recordings section: toolbar + scrollable list of recorded clips."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gtk, Gio, GLib  # noqa: E402

from ..dialogs.player_dialog import PlayerDialog
from ..recordings import (
    RECORDINGS_DIR,
    RecordingInfo,
    human_size,
    scan_recordings,
)
from .recording_row import RecordingRow

logger = logging.getLogger("ucam.viewer")


class RecordingsView(Gtk.Box):
    __gtype_name__ = "RecordingsView"

    def __init__(self, parent_window: Gtk.Window, recordings_dir: Path | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self._parent_window = parent_window
        self._dir = recordings_dir or RECORDINGS_DIR
        self._recordings: list[RecordingInfo] = []
        self._filter_cameras: list[str] = []
        self._rows: list[RecordingRow] = []

        self._build_toolbar()
        self._build_list()

        self._setup_monitor()

    def _build_toolbar(self) -> None:
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        toolbar.add_css_class("recordings-toolbar")
        self.append(toolbar)

        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        heading.set_hexpand(True)
        heading.set_hexpand_set(True)
        toolbar.append(heading)

        title = Gtk.Label(label="Recordings")
        title.add_css_class("recordings-title")
        title.set_halign(Gtk.Align.START)
        heading.append(title)

        self._subtitle = Gtk.Label(label="")
        self._subtitle.add_css_class("recordings-subtitle")
        self._subtitle.set_halign(Gtk.Align.START)
        heading.append(self._subtitle)

        self._filter = Gtk.DropDown()
        self._filter.add_css_class("recordings-filter")
        self._filter.connect("notify::selected", self._on_filter_changed)
        toolbar.append(self._filter)

        refresh = Gtk.Button(label="Refresh")
        refresh.add_css_class("tab-active")
        refresh.add_css_class("recordings-refresh-btn")
        refresh.set_valign(Gtk.Align.CENTER)
        refresh.connect("clicked", lambda _b: self.refresh())
        toolbar.append(refresh)

    def _build_list(self) -> None:
        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scrolled.set_vexpand(True)
        self.append(self._scrolled)

        self._list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._list.set_vexpand(True)
        self._scrolled.set_child(self._list)

    def _empty_state(self) -> None:
        for row in self._rows:
            self._list.remove(row)
        self._rows = []

        empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        empty.set_valign(Gtk.Align.CENTER)
        empty.set_halign(Gtk.Align.CENTER)
        empty.set_vexpand(True)

        icon = Gtk.Label(label="video_library")
        icon.add_css_class("material-icon")
        icon.add_css_class("recordings-empty-icon")
        empty.append(icon)

        text = Gtk.Label(
            label="No recordings yet\nRight-click a camera and choose Record"
        )
        text.add_css_class("recordings-empty-text")
        text.set_justify(Gtk.Justification.CENTER)
        empty.append(text)

        self._list.append(empty)

    def refresh(self) -> None:
        self._recordings = scan_recordings(self._dir)
        self._update_filter_model()
        self._rebuild()

    def _update_filter_model(self) -> None:
        cameras = sorted({r.camera_name for r in self._recordings})
        if cameras == self._filter_cameras:
            return
        self._filter_cameras = cameras
        model = Gtk.StringList.new(["All Cameras", *cameras])
        self._filter.set_model(model)

    def _selected_camera(self) -> str | None:
        idx = self._filter.get_selected()
        if idx <= 0:
            return None
        if idx < len(self._filter_cameras) + 1:
            return self._filter_cameras[idx - 1]
        return None

    def _on_filter_changed(self, _dropdown, _pspec) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        for row in self._rows:
            self._list.remove(row)
        self._rows = []

        camera = self._selected_camera()
        filtered = [
            r for r in self._recordings if camera is None or r.camera_name == camera
        ]

        if not filtered:
            self._empty_state()
        else:
            for rec in filtered:
                row = RecordingRow(
                    rec,
                    on_play=self._on_play,
                    on_open_folder=self._on_open_folder,
                    on_delete=self._on_delete,
                )
                self._rows.append(row)
                self._list.append(row)

        total = sum(r.size for r in self._recordings)
        if filtered != self._recordings:
            shown = len(filtered)
            self._subtitle.set_label(
                f"{len(self._recordings)} recordings · {human_size(total)} · showing {shown}"
            )
        else:
            self._subtitle.set_label(
                f"{len(self._recordings)} recordings · {human_size(total)}"
            )

    def _setup_monitor(self) -> None:
        if not self._dir.exists():
            self._dir.mkdir(parents=True, exist_ok=True)
        try:
            file = Gio.File.new_for_path(str(self._dir))
            self._monitor = file.monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self._monitor.connect("changed", self._on_dir_changed)
        except GLib.Error as exc:
            logger.warning("Could not monitor %s: %s", self._dir, exc)
            self._monitor = None
        self._pending_refresh: int | None = None

    def _on_dir_changed(
        self, _monitor: Gio.FileMonitor, _file: Gio.File, _other: Gio.File, _etype, *_args
    ) -> None:
        if self._pending_refresh is not None:
            return
        self._pending_refresh = GLib.timeout_add(500, self._do_pending_refresh)

    def _do_pending_refresh(self) -> bool:
        self._pending_refresh = None
        self.refresh()
        return False

    # -- Actions --------------------------------------------------------

    def _on_play(self, recording: RecordingInfo) -> None:
        PlayerDialog(self._parent_window, recording).present()

    def _on_open_folder(self, recording: RecordingInfo) -> None:
        subprocess.Popen(["xdg-open", str(recording.path.parent)])

    def _on_delete(self, recording: RecordingInfo) -> None:
        dialog = Gtk.AlertDialog(
            modal=True,
            message=f"Delete recording from '{recording.camera_name}'?",
            detail=f"{recording.path.name} will be permanently removed.",
            buttons=["Cancel", "Delete"],
        )
        dialog.choose(self._parent_window, None, self._on_delete_response, recording)

    def _on_delete_response(
        self, _dialog: Gtk.AlertDialog, result: Gio.AsyncResult, recording: RecordingInfo
    ) -> None:
        try:
            if _dialog.choose_finish(result) == 1:
                recording.path.unlink()
                self.refresh()
        except GLib.Error as exc:
            logger.warning("Delete failed: %s", exc)
