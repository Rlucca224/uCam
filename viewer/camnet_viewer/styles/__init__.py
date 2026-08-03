"""GTK4 stylesheet loader."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk  # noqa: E402

from .base import BASE_CSS
from .camera import CAMERA_CSS
from .dialog import DIALOG_CSS
from .sidebar import SIDEBAR_CSS
from .topbar import TOPBAR_CSS

_STYLESHEET = "".join([
    BASE_CSS,
    SIDEBAR_CSS,
    TOPBAR_CSS,
    CAMERA_CSS,
    DIALOG_CSS,
])


def load_css(provider: object) -> None:
    """Load the stylesheet into the GTK CSS provider."""
    css_provider = Gtk.CssProvider()
    css_provider.load_from_string(_STYLESHEET)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
