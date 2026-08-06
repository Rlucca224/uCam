"""Helper widgets for the camera viewer."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk  # noqa: E402


def popup_at_pointer(popover: Gtk.PopoverMenu, on_before_popup: object = None):
    """Callback for GestureClick 'pressed' that pops the popover at the pointer."""
    def on_pressed(_gesture: Gtk.GestureClick, _n_press: int, x: float, y: float) -> None:
        if on_before_popup is not None:
            on_before_popup()
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)
        popover.popup()

    return on_pressed


def icon_button(icon_name: str, label: str, css_class: str) -> Gtk.Button:
    """GTK button with a Material Symbols icon + text."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
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
