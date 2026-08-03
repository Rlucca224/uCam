"""Entry point y ventana principal del visor."""

from __future__ import annotations

import logging
import signal

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk  # noqa: E402

from .cli import parse_cameras
from .dialogs import AddCameraDialog
from .styles import load_css
from .widgets import Sidebar, TopBar, CameraGrid


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------


class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    def __init__(self, app: Gtk.Application, cameras: list):
        super().__init__(application=app, title="uCam — Dashboard")
        self.set_default_size(1280, 800)

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

        topbar = TopBar()
        content.append(topbar)

        top_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        top_sep.add_css_class("topbar-separator")
        content.append(top_sep)

        self._grid = CameraGrid(cameras)
        content.append(self._grid)

        self._sidebar.set_camera_count(len(cameras))

    def _on_add_device(self) -> None:
        dialog = AddCameraDialog(self, on_add=self._add_camera)
        dialog.present()

    def _add_camera(self, config) -> None:
        self._grid.add_camera(config)
        self._sidebar.set_camera_count(len(self._grid._cards))

    def shutdown(self) -> None:
        self._grid.shutdown()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    setup_logging()
    cameras = parse_cameras()

    load_css(None)

    def on_activate(app: Gtk.Application) -> None:
        win = MainWindow(app, cameras)

        def on_shutdown(*_args: object) -> None:
            win.shutdown()

        app.connect("shutdown", on_shutdown)
        win.present()

    app = Gtk.Application(application_id="ai.camnet.viewer")
    app.connect("activate", on_activate)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.run(None)
