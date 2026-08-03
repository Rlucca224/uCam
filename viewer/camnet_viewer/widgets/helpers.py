"""Helper widgets for the camera viewer."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402


def icon_button(icon_name: str, label: str, css_class: str) -> Gtk.Button:
    """GTK button with a Material Symbols icon + text."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box.set_halign(Gtk.Align.START)

    icon = Gtk.Label(label=icon_name)
    icon.add_css_class("material-icon")
    box.append(icon)

    text = Gtk.Label(label=label)
    text.add_css_class("button-text")
    box.append(text)

    btn = Gtk.Button()
    btn.set_child(box)
    btn.set_halign(Gtk.Align.FILL)
    btn.add_css_class(css_class)
    return btn
