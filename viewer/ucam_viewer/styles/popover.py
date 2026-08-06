"""Popover menu styles.

GtkPopover CSS node tree (verified at runtime with get_css_name()):
  popover.background[.menu]
  ╰── contents                  <- real widget (GtkPopoverContent), paints the visible card
      ╰── scrolledwindow
          ╰── viewport
              ╰── stack
                  ╰── box
                      ╰── modelbutton[.flat]   <- menu items are modelbutton, NOT button
                          ╰── label

The compiled-in Adwaita theme paints background/border/shadow on the
`contents` node, so styling only `popover.background` leaves Adwaita's
default hairline border visible around the menu. Item styling must use
`modelbutton` as the node name — `button` selectors never match.
"""

POPOVER_CSS = """
/* ===== Popover Menu ===== */

popover.background {
  background-color: transparent;
  border: none;
  box-shadow: none;
}

popover.background > contents {
  background-color: #302e33;
  border: none;
  outline: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 4px;
}

popover.background > contents modelbutton.flat,
popover.background > contents modelbutton.model {
  background: none;
  color: #FFFFFF;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 12px;
  border-radius: 6px;
  outline: none;
  box-shadow: none;
}

popover.background > contents modelbutton.flat label,
popover.background > contents modelbutton.model label {
  color: #FFFFFF;
}

popover.background > contents modelbutton.flat:hover,
popover.background > contents modelbutton.model:hover {
  background-color: #1b1b1b;
}

popover.background > contents modelbutton.flat:focus,
popover.background > contents modelbutton.model:focus,
popover.background > contents modelbutton.flat:focus-visible,
popover.background > contents modelbutton.model:focus-visible {
  outline: none;
  box-shadow: none;
}
"""
