"""Entry point y ventana principal del visor."""

from __future__ import annotations

import logging
import signal

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk  # noqa: E402

from .cli import parse_cameras
from .dialogs import AddCameraDialog
from .models import CameraConfig
from .store import CameraStore
from .styles import load_css
from .widgets import Sidebar, TopBar, CameraGrid


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


def _merge_cameras(
    stored: list[CameraConfig], cli: list[CameraConfig]
) -> list[CameraConfig]:
    merged: dict[str, CameraConfig] = {}
    for c in stored:
        merged[c.rtsp_url] = c
    for c in cli:
        merged[c.rtsp_url] = c
    return list(merged.values())


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------


class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    def __init__(self, app: Gtk.Application, cameras: list, store: CameraStore):
        super().__init__(application=app, title="uCam — Dashboard")
        self.set_default_size(1280, 800)
        self._store = store

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(main_box)

        self._sidebar = Sidebar(on_add_device=self._on_add_device)
        main_box.append(self._sidebar)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.add_css_class("sidebar-separator")
        main_box.append(sep)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_vexpand(True)
        content.set_hexpand(True)
        content.add_css_class("content-area")
        main_box.append(content)

        self._grid = CameraGrid(
            cameras,
            on_delete=self._on_delete_camera,
            on_config=self._on_config_camera,
        )

        topbar = TopBar(on_layout_change=self._grid.set_layout)
        content.append(topbar)

        top_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        top_sep.add_css_class("topbar-separator")
        content.append(top_sep)

        content.append(self._grid)

        self._sidebar.set_camera_count(len(cameras))

    def _cameras_list(self) -> list[CameraConfig]:
        cameras: list[CameraConfig] = []
        for card in self._grid._cards:
            if card.camera is not None:
                cameras.append(
                    CameraConfig(name=card.camera.name, rtsp_url=card.camera.rtsp_url)
                )
        return cameras

    def _on_add_device(self) -> None:
        dialog = AddCameraDialog(self, on_add=self._add_camera)
        dialog.present()

    def _add_camera(self, config: CameraConfig) -> None:
        self._grid.add_camera(config)
        self._sidebar.set_camera_count(len(self._grid._cards))
        self._store.save(self._cameras_list())

    def _on_delete_camera(self, camera: CameraConfig) -> None:
        self._grid.remove_camera(camera.rtsp_url)
        self._sidebar.set_camera_count(len(self._grid._cards))
        self._store.save(self._cameras_list())

    def _on_config_camera(self, camera: CameraConfig) -> None:
        # TODO: open camera management dialog
        pass

    def shutdown(self) -> None:
        self._grid.shutdown()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    setup_logging()

    store = CameraStore()
    stored = store.load()
    cli_cameras = parse_cameras()
    cameras = _merge_cameras(stored, cli_cameras)
    if cameras != stored:
        store.save(cameras)

    load_css(None)

    def on_activate(app: Gtk.Application) -> None:
        win = MainWindow(app, cameras, store)

        def on_shutdown(*_args: object) -> None:
            win.shutdown()

        app.connect("shutdown", on_shutdown)
        win.present()

    app = Gtk.Application(application_id="ai.camnet.viewer")
    app.connect("activate", on_activate)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.run(None)
