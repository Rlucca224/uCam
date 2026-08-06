"""Camera list row widget for list view."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, GLib, Gio  # noqa: E402

from ..models import CameraConfig, CameraStatus
from ..recorder import RecordingController
from .camera_player import CameraPlayer
from .helpers import popup_at_pointer


class CameraListRow(Gtk.Box):
    __gtype_name__ = "CameraListRow"

    def __init__(
        self,
        camera: CameraConfig,
        player: CameraPlayer | None = None,
        on_delete: object = None,
        on_config: object = None,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.camera = camera
        self._on_delete = on_delete
        self._on_config = on_config
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_size_request(-1, 155)
        self.set_overflow(Gtk.Overflow.HIDDEN)

        self.add_css_class("camera-list-row")

        self._own_player = player is None
        self._player = player or CameraPlayer(camera)
        self._recorder = RecordingController(camera.name, camera.rtsp_url)
        self._recording = False
        self._player.add_status_listener(self._update_status_ui)
        self._player.add_paintable_listener(self._on_paintable)
        self._player.add_info_listener(self._update_info)
        self._uptime_source: int | None = None
        self._build_ui()
        self._setup_context_menu()
        if self._own_player:
            self._player.start()

    def _setup_context_menu(self) -> None:
        if self._on_delete is None and self._on_config is None:
            return

        self._menu = Gio.Menu()
        if self._on_config is not None:
            self._menu.append("Config", "row.config")
        self._menu.append("Record", "row.record")
        if self._on_delete is not None:
            self._menu.append("Delete", "row.delete")

        popover = Gtk.PopoverMenu.new_from_model(self._menu)
        popover.set_parent(self)
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_halign(Gtk.Align.START)

        def on_action(action_name: str, _param):
            if action_name == "delete" and self._on_delete is not None:
                self._on_delete(self.camera)
            elif action_name == "config" and self._on_config is not None:
                self._on_config(self.camera)
            elif action_name == "record":
                self._toggle_recording()

        group = Gio.SimpleActionGroup()
        for name in ("delete", "config", "record"):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda a, p, n=name: on_action(n, p))
            group.add_action(action)
        self.insert_action_group("row", group)

        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect(
            "pressed",
            popup_at_pointer(popover, on_before_popup=self._before_menu),
        )
        self.add_controller(gesture)

    def _before_menu(self) -> None:
        label = "Stop" if self._recorder.is_recording else "Record"
        self._menu.remove(1)
        self._menu.insert(1, label, "row.record")

    def _toggle_recording(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
        else:
            self._recorder.start()
        self._recording = self._recorder.is_recording
        self._update_status_ui(self._player.state.status)

    def _build_ui(self) -> None:
        # --- Left: preview ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.set_size_request(320, -1)
        left_box.set_hexpand(False)
        left_box.set_vexpand(False)
        left_box.add_css_class("camera-list-preview-box")
        self.append(left_box)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_bar.set_margin_start(4)
        top_bar.set_margin_end(4)
        top_bar.set_margin_top(4)
        top_bar.set_margin_bottom(2)
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
        main_child.set_size_request(290, 130)
        overlay.set_child(main_child)

        self._picture = Gtk.Picture()
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.COVER)
        self._picture.add_css_class("camera-video")
        self._picture.set_halign(Gtk.Align.FILL)
        self._picture.set_valign(Gtk.Align.FILL)
        overlay.add_overlay(self._picture)

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
        detail.set_margin_start(4)
        detail.set_margin_end(6)
        detail.set_margin_top(4)
        detail.set_margin_bottom(4)
        self.append(detail)

        self._detail_name = Gtk.Label(label=self.camera.name)
        self._detail_name.add_css_class("camera-list-detail-title")
        self._detail_name.set_halign(Gtk.Align.START)
        detail.append(self._detail_name)

        self._detail_url = Gtk.Label(label=self.camera.rtsp_url)
        self._detail_url.add_css_class("camera-list-detail-subtitle")
        self._detail_url.set_halign(Gtk.Align.START)
        self._detail_url.set_ellipsize(2)
        self._detail_url.set_margin_bottom(2)
        detail.append(self._detail_url)

        spacer_top = Gtk.Box()
        spacer_top.set_vexpand(True)
        spacer_top.set_size_request(-1, 2)
        detail.append(spacer_top)

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

    def _on_paintable(self, paintable: object) -> None:
        self._picture.set_paintable(paintable)

    def _update_status_ui(self, status: CameraStatus) -> None:
        if self._recording:
            status = CameraStatus.RECORDING
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
        self._picture.set_paintable(None)
        self._recorder.stop()
        if self._uptime_source is not None:
            GLib.source_remove(self._uptime_source)
            self._uptime_source = None
        if self._own_player:
            self._player.stop()
