"""Add camera dialog."""

from __future__ import annotations

import logging
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, GLib  # noqa: E402

from ..models import CameraConfig
from ..onvif_discovery import StreamProfile, discover_onvif_streams
from ..pipeline import build_pipeline

logger = logging.getLogger("camnet.viewer")
Gst.init(None)


class AddCameraDialog(Gtk.Window):
    __gtype_name__ = "AddCameraDialog"

    def __init__(self, parent: Gtk.Window, on_add: object) -> None:
        super().__init__(title="Add Camera", transient_for=parent)
        self.set_modal(True)
        self.set_default_size(400, -1)
        self.set_resizable(False)
        self._on_add = on_add

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        self.set_child(content)

        title = Gtk.Label(label="Add Camera")
        title.add_css_class("dialog-title")
        title.set_halign(Gtk.Align.START)
        content.append(title)

        # Connection type selector
        proto_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        proto_label = Gtk.Label(label="Connection Type")
        proto_label.set_halign(Gtk.Align.START)
        proto_label.add_css_class("dialog-label")
        proto_box.append(proto_label)

        self._proto_combo = Gtk.DropDown.new_from_strings(["RTSP", "ONVIF"])
        self._proto_combo.add_css_class("dialog-dropdown")
        self._proto_combo.connect("notify::selected", self._on_proto_changed)
        proto_box.append(self._proto_combo)
        content.append(proto_box)

        # Stack for protocol-specific fields
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        content.append(self._stack)

        # ---- RTSP page ----
        rtsp_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._stack.add_named(rtsp_page, "rtsp")

        rtsp_name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rtsp_name_label = Gtk.Label(label="Camera Name")
        rtsp_name_label.set_halign(Gtk.Align.START)
        rtsp_name_label.add_css_class("dialog-label")
        rtsp_name_box.append(rtsp_name_label)
        self._rtsp_name = Gtk.Entry()
        self._rtsp_name.set_placeholder_text("Entrance, Garage, Patio…")
        self._rtsp_name.add_css_class("dialog-entry")
        rtsp_name_box.append(self._rtsp_name)
        rtsp_page.append(rtsp_name_box)

        rtsp_url_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rtsp_url_label = Gtk.Label(label="RTSP URL")
        rtsp_url_label.set_halign(Gtk.Align.START)
        rtsp_url_label.add_css_class("dialog-label")
        rtsp_url_box.append(rtsp_url_label)
        self._rtsp_url = Gtk.Entry()
        self._rtsp_url.set_placeholder_text("rtsp://admin:pass@192.168.1.5:554/stream")
        self._rtsp_url.add_css_class("dialog-entry")
        rtsp_url_box.append(self._rtsp_url)
        rtsp_page.append(rtsp_url_box)

        # Preview button
        preview_btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        preview_btn_row.set_halign(Gtk.Align.CENTER)
        preview_btn_row.set_hexpand(False)
        self._preview_btn = Gtk.Button(label="Preview")
        self._preview_btn.add_css_class("dialog-btn-preview")
        self._preview_btn.connect("clicked", self._on_preview_clicked)
        self._preview_btn.set_visible(False)
        preview_btn_row.append(self._preview_btn)
        rtsp_page.append(preview_btn_row)

        self._rtsp_url.connect("notify::text", self._on_url_text_changed)

        # Preview area (hidden by default)
        self._preview_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._preview_area.add_css_class("preview-container")
        self._preview_area.set_visible(False)

        self._preview_picture = Gtk.Picture()
        self._preview_picture.set_size_request(320, 180)
        self._preview_picture.add_css_class("preview-video")
        self._preview_picture.set_hexpand(True)
        self._preview_area.append(self._preview_picture)

        preview_status = Gtk.Label(label="")
        preview_status.set_halign(Gtk.Align.CENTER)
        preview_status.add_css_class("preview-status")
        self._preview_status = preview_status
        self._preview_area.append(preview_status)

        rtsp_page.append(self._preview_area)

        self._preview_pipeline: Gst.Pipeline | None = None

        # ---- ONVIF page ----
        onvif_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._stack.add_named(onvif_page, "onvif")

        onvif_name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        onvif_name_label = Gtk.Label(label="Camera Name")
        onvif_name_label.set_halign(Gtk.Align.START)
        onvif_name_label.add_css_class("dialog-label")
        onvif_name_box.append(onvif_name_label)
        self._onvif_name = Gtk.Entry()
        self._onvif_name.set_placeholder_text("Entrance, Garage, Patio…")
        self._onvif_name.add_css_class("dialog-entry")
        onvif_name_box.append(self._onvif_name)
        onvif_page.append(onvif_name_box)

        onvif_url_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        onvif_url_label = Gtk.Label(label="ONVIF Endpoint")
        onvif_url_label.set_halign(Gtk.Align.START)
        onvif_url_label.add_css_class("dialog-label")
        onvif_url_box.append(onvif_url_label)
        self._onvif_endpoint = Gtk.Entry()
        self._onvif_endpoint.set_placeholder_text("http://192.168.1.3:8899/onvif/device_service")
        self._onvif_endpoint.add_css_class("dialog-entry")
        onvif_url_box.append(self._onvif_endpoint)
        onvif_page.append(onvif_url_box)

        onvif_creds = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        onvif_creds.set_homogeneous(True)

        onvif_user_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        onvif_user_label = Gtk.Label(label="Username")
        onvif_user_label.set_halign(Gtk.Align.START)
        onvif_user_label.add_css_class("dialog-label")
        onvif_user_box.append(onvif_user_label)
        self._onvif_user = Gtk.Entry()
        self._onvif_user.set_placeholder_text("admin")
        self._onvif_user.add_css_class("dialog-entry")
        onvif_user_box.append(self._onvif_user)
        onvif_creds.append(onvif_user_box)

        onvif_pass_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        onvif_pass_label = Gtk.Label(label="Password")
        onvif_pass_label.set_halign(Gtk.Align.START)
        onvif_pass_label.add_css_class("dialog-label")
        onvif_pass_box.append(onvif_pass_label)
        self._onvif_pass = Gtk.Entry()
        self._onvif_pass.set_placeholder_text("password")
        self._onvif_pass.add_css_class("dialog-entry")
        self._onvif_pass.set_visibility(False)
        onvif_pass_box.append(self._onvif_pass)
        onvif_creds.append(onvif_pass_box)
        onvif_page.append(onvif_creds)

        # Preview button (ONVIF)
        onvif_preview_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        onvif_preview_row.set_halign(Gtk.Align.CENTER)
        onvif_preview_row.set_hexpand(False)
        onvif_preview_btn = Gtk.Button(label="Preview")
        onvif_preview_btn.add_css_class("dialog-btn-preview")
        onvif_preview_btn.set_visible(False)
        onvif_preview_btn.connect("clicked", lambda _b: self._on_onvif_preview())
        self._onvif_preview_btn = onvif_preview_btn
        onvif_preview_row.append(onvif_preview_btn)
        onvif_page.append(onvif_preview_row)

        onvif_preview_msg = Gtk.Label(label="")
        onvif_preview_msg.set_halign(Gtk.Align.CENTER)
        onvif_preview_msg.add_css_class("preview-status")
        self._onvif_preview_msg = onvif_preview_msg
        onvif_page.append(onvif_preview_msg)

        # Profiles dropdown (initially hidden)
        profiles_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        profiles_box.set_visible(False)
        self._profiles_box = profiles_box
        onvif_page.append(profiles_box)

        profiles_label = Gtk.Label(label="Available Streams")
        profiles_label.set_halign(Gtk.Align.START)
        profiles_label.add_css_class("dialog-label")
        profiles_box.append(profiles_label)

        self._profiles_model = Gtk.StringList()
        self._profiles_dropdown = Gtk.DropDown()
        self._profiles_dropdown.set_model(self._profiles_model)
        self._profiles_dropdown.add_css_class("dialog-dropdown")
        self._profiles_dropdown.connect("notify::selected", self._on_profile_changed)
        profiles_box.append(self._profiles_dropdown)

        # Info grid
        info_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        info_grid.set_visible(False)
        self._onvif_info_grid = info_grid
        profiles_box.append(info_grid)

        self._onvif_res_label = Gtk.Label(label="Resolution: --")
        self._onvif_res_label.add_css_class("dialog-label")
        info_grid.append(self._onvif_res_label)

        self._onvif_codec_label = Gtk.Label(label="Codec: --")
        self._onvif_codec_label.add_css_class("dialog-label")
        info_grid.append(self._onvif_codec_label)

        self._onvif_fps_label = Gtk.Label(label="FPS: --")
        self._onvif_fps_label.add_css_class("dialog-label")
        info_grid.append(self._onvif_fps_label)

        # Preview area (ONVIF, hidden by default)
        self._onvif_preview_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._onvif_preview_area.add_css_class("preview-container")
        self._onvif_preview_area.set_visible(False)
        onvif_page.append(self._onvif_preview_area)

        self._onvif_preview_picture = Gtk.Picture()
        self._onvif_preview_picture.set_size_request(320, 180)
        self._onvif_preview_picture.add_css_class("preview-video")
        self._onvif_preview_picture.set_hexpand(True)
        self._onvif_preview_area.append(self._onvif_preview_picture)

        self._onvif_preview_status = Gtk.Label(label="")
        self._onvif_preview_status.set_halign(Gtk.Align.CENTER)
        self._onvif_preview_status.add_css_class("preview-status")
        self._onvif_preview_area.append(self._onvif_preview_status)

        self._onvif_endpoint.connect(
            "notify::text",
            lambda e, _p: self._onvif_preview_btn.set_visible(bool(e.get_text().strip())),
        )
        self._onvif_endpoint.connect("activate", self._on_onvif_preview)
        self._onvif_user.connect("activate", self._on_onvif_preview)
        self._onvif_pass.connect("activate", self._on_onvif_preview)

        self._onvif_profiles: list[StreamProfile] = []
        self._onvif_preview_pipeline: Gst.Pipeline | None = None
        self._onvif_start_id: int | None = None
        self._ignore_profile_changes: bool = False
        self._current_preview_idx: int = -1

        # Buttons
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buttons.set_halign(Gtk.Align.END)
        buttons.set_margin_top(4)
        content.append(buttons)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("dialog-btn-cancel")
        cancel_btn.connect("clicked", self._on_cancel)
        buttons.append(cancel_btn)

        add_btn = Gtk.Button(label="Add Camera")
        add_btn.add_css_class("dialog-btn-add")
        add_btn.connect("clicked", self._on_add_clicked)
        buttons.append(add_btn)

        # Enter key in RTSP URL
        self._rtsp_name.connect("activate", self._on_add_clicked)
        self._rtsp_url.connect("activate", self._on_add_clicked)
        self._onvif_name.connect("activate", self._on_add_clicked)
        self._onvif_endpoint.connect("activate", self._on_add_clicked)

    def _on_proto_changed(self, combo, _pspec) -> None:
        self._stop_preview()
        self._stop_onvif_preview()
        self._stack.set_visible_child_name("onvif" if combo.get_selected() == 1 else "rtsp")

    def _on_add_clicked(self, _widget: Gtk.Widget) -> None:
        self._stop_preview()
        self._stop_onvif_preview()

        is_onvif = self._proto_combo.get_selected() == 1

        if is_onvif:
            name = self._onvif_name.get_text().strip()
            if not name:
                return
            rtsp_url = self._selected_onvif_url()
            if not rtsp_url:
                return
        else:
            name = self._rtsp_name.get_text().strip()
            url = self._rtsp_url.get_text().strip()
            if not name or not url:
                return
            rtsp_url = url

        self._on_add(CameraConfig(name=name, rtsp_url=rtsp_url))
        self.close()

    def _on_cancel(self, _widget: Gtk.Widget) -> None:
        self._stop_preview()
        self._stop_onvif_preview()
        self.close()

    # -- Preview -------------------------------------------------------

    def _on_url_text_changed(self, entry, _pspec) -> None:
        text = entry.get_text().strip()
        if text:
            self._preview_btn.set_visible(True)
        else:
            self._stop_preview()
            self._preview_btn.set_visible(False)

    def _on_preview_clicked(self, _widget: Gtk.Widget) -> None:
        if self._preview_pipeline is not None:
            self._stop_preview()
            return

        url = self._rtsp_url.get_text().strip()
        if not url:
            return

        self._preview_status.set_label("Connecting…")
        self._preview_area.set_visible(True)
        self._preview_btn.set_label("Stop Preview")

        try:
            self._preview_pipeline = build_pipeline("_preview", url)
        except RuntimeError as exc:
            self._preview_status.set_label(f"Error: {exc}")
            self._preview_pipeline = None
            return

        sink = self._preview_pipeline.get_by_name("sink")
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._preview_picture.set_paintable(paintable)
            self._preview_status.set_label("Connected")
        else:
            sink.connect("notify::paintable", self._on_preview_paintable)

        bus = self._preview_pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_preview_error)
        bus.connect("message::state-changed", self._on_preview_state)

        self._preview_pipeline.set_state(Gst.State.PLAYING)

    def _on_preview_paintable(self, sink, _pspec) -> None:
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._preview_picture.set_paintable(paintable)
            self._preview_status.set_label("Connected")

    def _on_preview_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        self._preview_status.set_label(f"Error: {err.message}")

    def _on_preview_state(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        if msg.src != self._preview_pipeline:
            return
        _old, new, _pending = msg.parse_state_changed()
        if new == Gst.State.PLAYING:
            self._preview_status.set_label("Connected")
        elif new == Gst.State.NULL:
            self._preview_status.set_label("Disconnected")

    def _stop_preview(self) -> None:
        if self._preview_pipeline is not None:
            self._preview_picture.set_paintable(None)
            self._preview_pipeline.set_state(Gst.State.NULL)
            self._preview_pipeline.get_state(Gst.CLOCK_TIME_NONE)
            self._preview_pipeline = None
        self._preview_area.set_visible(False)
        self._preview_btn.set_label("Preview")
        self._preview_status.set_label("")

    def _on_onvif_preview(self) -> None:
        if self._onvif_preview_pipeline is not None:
            self._stop_onvif_preview()
            return

        endpoint = self._onvif_endpoint.get_text().strip()
        user = self._onvif_user.get_text().strip()
        password = self._onvif_pass.get_text().strip()
        if not endpoint:
            return

        self._onvif_preview_msg.set_label("Discovering ONVIF profiles…")
        self._onvif_preview_btn.set_sensitive(False)

        def discover() -> None:
            try:
                profiles = discover_onvif_streams(endpoint, user, password)
                GLib.idle_add(self._on_onvif_profiles_ready, profiles, None)
            except Exception as exc:
                logger.exception("ONVIF discovery failed")
                GLib.idle_add(self._on_onvif_profiles_ready, [], str(exc))

        threading.Thread(target=discover, daemon=True).start()

    def _on_onvif_profiles_ready(
        self, profiles: list[StreamProfile], error: str | None
    ) -> None:
        self._onvif_preview_btn.set_sensitive(True)
        self._onvif_profiles = profiles

        if error:
            self._onvif_preview_msg.set_label(f"Discovery error: {error}")
            return

        if not profiles:
            self._onvif_preview_msg.set_label("No streams found")
            return

        self._onvif_preview_msg.set_label(f"{len(profiles)} stream(s) found")

        self._ignore_profile_changes = True

        self._profiles_model.splice(0, self._profiles_model.get_n_items(), [])
        for p in profiles:
            label = f"{p.resolution} — {p.name}"
            self._profiles_model.append(label)

        self._profiles_box.set_visible(True)
        self._onvif_info_grid.set_visible(True)
        self._onvif_preview_area.set_visible(True)
        self._onvif_preview_btn.set_label("Stop Preview")

        self._profiles_dropdown.set_selected(0)
        self._update_onvif_info(0)
        self._onvif_start_id = GLib.idle_add(self._start_onvif_preview_with_profile, 0)

        self._ignore_profile_changes = False

    def _set_profile_without_signal(self, idx: int) -> None:
        self._ignore_profile_changes = True
        self._profiles_dropdown.set_selected(idx)
        self._ignore_profile_changes = False

    def _selected_onvif_url(self) -> str:
        idx = self._profiles_dropdown.get_selected()
        if 0 <= idx < len(self._onvif_profiles):
            return self._onvif_profiles[idx].url
        return ""

    def _on_profile_changed(self, dropdown, _pspec) -> None:
        if self._ignore_profile_changes:
            return
        idx = dropdown.get_selected()
        if idx < 0 or idx >= len(self._onvif_profiles):
            return
        self._cancel_onvif_preview_start()
        self._stop_onvif_preview_pipeline()
        self._update_onvif_info(idx)
        self._onvif_start_id = GLib.idle_add(self._start_onvif_preview_with_profile, idx)

    def _cancel_onvif_preview_start(self) -> None:
        if self._onvif_start_id is not None:
            GLib.source_remove(self._onvif_start_id)
            self._onvif_start_id = None

    def _update_onvif_info(self, idx: int) -> None:
        p = self._onvif_profiles[idx]
        self._onvif_res_label.set_label(f"Resolution: {p.resolution}")
        self._onvif_codec_label.set_label(f"Codec: {p.encoding or '--'}")
        self._onvif_fps_label.set_label(f"FPS: {p.fps or '--'}")

    def _start_onvif_preview_with_profile(self, idx: int) -> bool:
        self._onvif_start_id = None
        if not self._onvif_profiles or idx >= len(self._onvif_profiles):
            return False
        if self._onvif_preview_pipeline is not None and self._current_preview_idx == idx:
            logger.info("ONVIF preview: already playing idx %d, skip", idx)
            return False
        self._current_preview_idx = idx
        url = self._onvif_profiles[idx].url
        logger.info("ONVIF preview: start %s", url)
        self._onvif_preview_status.set_label("Connecting…")
        self._onvif_preview_area.set_visible(True)

        try:
            self._onvif_preview_pipeline = build_pipeline("_onvif_preview", url)
        except RuntimeError as exc:
            self._onvif_preview_status.set_label(f"Error: {exc}")
            self._onvif_preview_pipeline = None
            self._current_preview_idx = -1
            return False

        sink = self._onvif_preview_pipeline.get_by_name("sink")
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._onvif_preview_picture.set_paintable(paintable)
            self._onvif_preview_status.set_label("Connected")
        else:
            sink.connect("notify::paintable", self._on_onvif_preview_paintable)

        bus = self._onvif_preview_pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_onvif_preview_error)
        bus.connect("message::state-changed", self._on_onvif_preview_state)

        self._onvif_preview_pipeline.set_state(Gst.State.PLAYING)
        return False

    def _on_onvif_preview_paintable(self, sink, _pspec) -> None:
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._onvif_preview_picture.set_paintable(paintable)
            self._onvif_preview_status.set_label("Connected")

    def _on_onvif_preview_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        logger.warning("ONVIF preview error: %s", err.message)
        self._onvif_preview_status.set_label(f"Error: {err.message}")

    def _on_onvif_preview_state(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        if msg.src != self._onvif_preview_pipeline:
            return
        _old, new, _pending = msg.parse_state_changed()
        logger.info("ONVIF preview state: %s", new.value_name)
        if new == Gst.State.PLAYING:
            self._onvif_preview_status.set_label("Connected")
        elif new == Gst.State.NULL:
            self._onvif_preview_status.set_label("Disconnected")

    def _stop_onvif_preview(self) -> None:
        self._cancel_onvif_preview_start()
        self._stop_onvif_preview_pipeline()
        self._profiles_box.set_visible(False)
        self._onvif_info_grid.set_visible(False)
        self._onvif_preview_area.set_visible(False)
        self._onvif_preview_msg.set_label("")
        self._onvif_preview_btn.set_label("Preview")
        self._onvif_profiles = []
        self._current_preview_idx = -1
        self._profiles_model.splice(0, self._profiles_model.get_n_items(), [])

    def _stop_onvif_preview_pipeline(self) -> None:
        if self._onvif_preview_pipeline is not None:
            logger.info("ONVIF preview: stop")
            self._onvif_preview_picture.set_paintable(None)
            self._onvif_preview_pipeline.set_state(Gst.State.NULL)
            self._onvif_preview_pipeline.get_state(Gst.CLOCK_TIME_NONE)
            self._onvif_preview_pipeline = None
        self._current_preview_idx = -1
