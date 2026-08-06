"""Playback window for a recorded clip (playbin + gtk4paintablesink)."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, GLib, Gdk  # noqa: E402

from ..recordings import RecordingInfo, format_datetime, format_duration

Gst.init(None)


class PlayerDialog(Gtk.Window):
    __gtype_name__ = "PlayerDialog"

    def __init__(self, parent: Gtk.Window, recording: RecordingInfo) -> None:
        title = f"uCam — {recording.camera_name} — {format_datetime(recording.timestamp)}"
        super().__init__(title=title, transient_for=parent)
        self.set_default_size(960, 560)
        self._recording = recording
        self._pipeline: Gst.Element | None = None
        self._duration_ns: int = 0
        self._tick_source: int | None = None
        self._ended = False

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.set_margin_top(8)
        content.set_margin_start(8)
        content.set_margin_end(8)
        content.set_margin_bottom(8)
        self.set_child(content)

        self._picture = Gtk.Picture()
        self._picture.set_hexpand(True)
        self._picture.set_vexpand(True)
        self._picture.set_can_shrink(True)
        self._picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        content.append(self._picture)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls.set_halign(Gtk.Align.FILL)
        content.append(controls)

        self._play_btn = Gtk.Button(label="Pause")
        self._play_btn.add_css_class("recording-action-btn")
        self._play_btn.connect("clicked", self._on_toggle_play)
        controls.append(self._play_btn)

        self._time_label = Gtk.Label(label="00:00 / 00:00")
        self._time_label.add_css_class("recording-meta")
        controls.append(self._time_label)

        self._seek = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._seek.set_range(0, 100)
        self._seek.set_draw_value(False)
        self._seek.set_hexpand(True)
        self._seek.connect("change-value", self._on_seek)
        controls.append(self._seek)

        close_btn = Gtk.Button(label="Close")
        close_btn.add_css_class("recording-action-btn")
        close_btn.connect("clicked", lambda _b: self.close())
        controls.append(close_btn)

        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

        self.connect("close-request", self._on_close_request)

        self._build_pipeline()
        self._play()

    # -- Pipeline -------------------------------------------------------

    def _build_pipeline(self) -> None:
        self._pipeline = Gst.ElementFactory.make("playbin", "playback")
        self._pipeline.set_property("uri", self._recording.path.as_uri())

        sink = Gst.ElementFactory.make("gtk4paintablesink", None)
        if sink is not None:
            self._pipeline.set_property("video-sink", sink)
            paintable = sink.get_property("paintable")
            if paintable is not None:
                self._picture.set_paintable(paintable)
            else:
                sink.connect("notify::paintable", self._on_paintable)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)

    def _on_paintable(self, sink, _pspec) -> None:
        paintable = sink.get_property("paintable")
        if paintable is not None:
            self._picture.set_paintable(paintable)

    def _play(self) -> None:
        if self._pipeline is None:
            return
        self._pipeline.set_state(Gst.State.PLAYING)
        self._play_btn.set_label("Pause")
        self._ended = False
        if self._tick_source is None:
            self._tick_source = GLib.timeout_add(500, self._tick)

    def _pause(self) -> None:
        if self._pipeline is not None:
            self._pipeline.set_state(Gst.State.PAUSED)
        self._play_btn.set_label("Play")

    def _on_toggle_play(self, _btn) -> None:
        if self._pipeline is None:
            return
        if self._ended:
            self._pipeline.seek_simple(
                Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0
            )
            self._play()
            return
        _ok, state, _pending = self._pipeline.get_state(0)
        if state == Gst.State.PLAYING:
            self._pause()
        else:
            self._play()

    def _on_seek(self, _range, scroll, value) -> bool:
        if self._pipeline is not None and self._duration_ns > 0:
            target = int((value / 100.0) * self._duration_ns)
            self._pipeline.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                target,
            )
        return False

    def _tick(self) -> bool:
        if self._pipeline is None:
            self._tick_source = None
            return False

        if self._duration_ns == 0:
            ok, self._duration_ns = self._pipeline.query_duration(Gst.Format.TIME)
            if ok and self._duration_ns > 0:
                self._seek.set_range(0, 100)

        ok, pos = self._pipeline.query_position(Gst.Format.TIME)
        if ok:
            cur = pos / 1e9
            self._time_label.set_label(
                f"{format_duration(cur)} / {format_duration(self._duration_ns / 1e9)}"
            )
            if self._duration_ns > 0:
                self._seek.set_value(pos * 100.0 / self._duration_ns)
        return True

    def _on_error(self, _bus: Gst.Bus, msg: Gst.Message) -> None:
        err, _debug = msg.parse_error()
        self._pause()
        self._time_label.set_label(f"Error: {err.message}")

    def _on_eos(self, _bus: Gst.Bus, _msg: Gst.Message) -> None:
        self._ended = True
        self._pause()
        self._seek.set_value(100)
        if self._duration_ns > 0:
            self._time_label.set_label(
                f"{format_duration(self._duration_ns / 1e9)} / "
                f"{format_duration(self._duration_ns / 1e9)}"
            )

    def _on_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, _state: Gdk.ModifierType
    ) -> bool:
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            self.close()
            return True
        if keyval in (Gdk.KEY_space,):
            self._on_toggle_play(None)
            return True
        return False

    def _on_close_request(self, _window) -> bool:
        if self._tick_source is not None:
            GLib.source_remove(self._tick_source)
            self._tick_source = None
        if self._pipeline is not None:
            bus = self._pipeline.get_bus()
            bus.remove_signal_watch()
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline.get_state(Gst.SECOND)
            self._pipeline = None
        return False
