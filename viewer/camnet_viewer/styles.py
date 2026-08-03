"""Hoja de estilos GTK4 del visor."""

_STYLESHEET = """
/* ===== Global ===== */

.material-icon {
  font-family: 'Material Symbols Rounded', sans-serif;
  font-size: 18px;
  font-weight: 400;
  font-style: normal;
  color: inherit;
  min-width: 24px;
}

.button-text {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
}

window, .content-area {
  background-color: #000000;
  color: #FFFFFF;
}

/* ===== Sidebar ===== */
.sidebar {
  background-color: #000000;
  border-right: 1px solid #262626;
  padding: 0;
}

.sidebar-logo {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 8px;
}

.sidebar-status-title {
  font-size: 13px;
  font-weight: 500;
  color: #FFFFFF;
}

.sidebar-status-subtitle {
  font-size: 11px;
  font-weight: 600;
  color: #4adf9d;
  letter-spacing: 0.05em;
}

.sidebar-add-btn {
  background: none;
  border: none;
  color: #666666;
  padding: 3px 10px;
  border-radius: 6px;
}
.sidebar-add-btn:hover {
  color: #FFFFFF;
  background-color: #0e0e0e;
}
.sidebar-add-btn .button-text {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: inherit;
}
.sidebar-add-btn .material-icon {
  color: #666666;
}

.sidebar-separator {
  background-color: #262626;
  min-height: 1px;
  min-width: 1px;
}

.nav-item {
  background: none;
  border: none;
  color: #666666;
  padding: 3px 10px;
  border-radius: 6px;
}
.nav-item:hover {
  color: #FFFFFF;
  background-color: #0e0e0e;
}
.nav-item .button-text {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: inherit;
}
.nav-item .material-icon {
  color: #666666;
}
.nav-item:hover .material-icon {
  color: #FFFFFF;
}

.nav-item-active {
  background-color: #1b1b1b;
  border: none;
  color: #FFFFFF;
  padding: 3px 10px;
  border-radius: 8px;
}
.nav-item-active:hover {
  background-color: #1f1f1f;
}
.nav-item-active .button-text {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: inherit;
}
.nav-item-active .material-icon {
  color: #FFFFFF;
}

.sidebar-bottom {
  border-top: 1px solid #262626;
}

/* ===== Top Bar ===== */
.topbar {
  background-color: #131313;
}

.tab-active {
  background-color: #1b1b1b;
  border: 1px solid #262626;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 12px;
  border-radius: 4px;
}
.tab-active:hover {
  background-color: #1f1f1f;
}

.tab-inactive {
  background: none;
  border: 1px solid transparent;
  color: #666666;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 12px;
  border-radius: 4px;
}
.tab-inactive:hover {
  border-color: #262626;
  background-color: #0e0e0e;
}

.layout-label {
  font-size: 11px;
  font-weight: 600;
  color: #FFFFFF;
  margin-right: 4px;
}

.layout-toggle {
  background-color: #000000;
  border: 1px solid #262626;
  border-radius: 6px;
}

.layout-btn-active {
  background-color: #2a2a2a;
  border: none;
  border-right: 1px solid #262626;
  color: #FFFFFF;
  font-size: 16px;
  padding: 3px 8px;
  border-radius: 0;
  min-width: 28px;
}
.layout-btn-active:hover {
  background-color: #1f1f1f;
}

.layout-btn-inactive {
  background-color: #000000;
  border: none;
  color: #666666;
  font-size: 16px;
  padding: 3px 8px;
  border-radius: 0;
  min-width: 28px;
}
.layout-btn-inactive:hover {
  background-color: #0e0e0e;
}

.topbar-separator {
  background-color: #262626;
  min-height: 1px;
}

/* ===== Camera Grid ===== */
.camera-grid-container {
  background-color: #131313;
}

.camera-flow {
  background-color: #131313;
}

.camera-card {
  background-color: #131313;
  border: 1px solid #262626;
  border-radius: 8px;
  min-width: 280px;
}

.camera-feed {
  background-color: #0a0a0a;
  min-height: 158px;
}

.camera-video {
  opacity: 0.8;
}
.camera-video:hover {
  opacity: 1.0;
}

.camera-gradient-top {
  background: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent);
  min-height: 48px;
}

.camera-name {
  font-size: 11px;
  font-weight: 600;
  color: #FFFFFF;
  background-color: rgba(0,0,0,0.5);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(38,38,38,0.5);
}

.camera-status-tag {
  background-color: rgba(0,0,0,0.5);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(38,38,38,0.5);
}

.camera-status-text {
  font-size: 11px;
  font-weight: 600;
  color: #FFFFFF;
}

.status-dot {
  font-size: 8px;
  line-height: 8px;
  min-width: 8px;
  min-height: 8px;
  color: #666666;
}

.status-connecting {
  color: #666666;
}
.status-live {
  color: #4adf9d;
}
.status-recording {
  color: #ffb4ab;
}
.status-no-signal {
  color: #666666;
}
.status-error {
  color: #ffb4ab;
}

.no-signal-overlay {
  background-color: rgba(19,19,19,0.9);
  padding: 12px 24px;
  border-radius: 8px;
}

.no-signal-text {
  font-size: 11px;
  font-weight: 600;
  color: #666666;
}

/* ===== Camera List ===== */
.camera-list-container {
  background-color: #131313;
}

.camera-list-row {
  background-color: #2A2A2A;
  border: 1px solid #262626;
  border-radius: 8px;
  min-height: 150px;
}

.camera-list-preview-box {
  background-color: #0a0a0a;
  border-right: 1px solid #262626;
  border-radius: 8px 0 0 8px;
}

.camera-list-feed {
  background-color: #0a0a0a;
  min-height: 120px;
  border-radius: 0 0 0 8px;
}

.camera-list-detail {
  background-color: #2A2A2A;
  border-radius: 0 8px 8px 0;
  padding: 4px 4px;
}

.camera-list-detail-title {
  font-size: 14px;
  font-weight: 600;
  color: #FFFFFF;
}

.camera-list-detail-subtitle {
  font-size: 10px;
  font-weight: 500;
  color: #666666;
}

.camera-list-info-grid {
  background-color: #1f1f1f;
  border-radius: 6px;
  padding: 6px 8px;
}

.camera-list-info-label {
  font-size: 10px;
  font-weight: 600;
  color: #666666;
}

.camera-list-info-value {
  font-size: 10px;
  font-weight: 500;
  color: #A1A1A1;
}

.camera-list-action-btn {
  background: none;
  border: 1px solid #333333;
  color: #A1A1A1;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}
.camera-list-action-btn:hover {
  border-color: #555555;
  color: #FFFFFF;
  background-color: #1f1f1f;
}

/* ===== Dialog ===== */

.dialog-title {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
}

.dialog-label {
  font-size: 12px;
  font-weight: 500;
  color: #A1A1A1;
}

.dialog-entry {
  background-color: #1b1b1b;
  border: 1px solid #262626;
  border-radius: 6px;
  color: #FFFFFF;
  font-size: 14px;
  padding: 8px 12px;
}

.dialog-btn-cancel {
  background: none;
  border: 1px solid #262626;
  color: #A1A1A1;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 16px;
  border-radius: 6px;
}
.dialog-btn-cancel:hover {
  background-color: #1b1b1b;
}

.dialog-btn-add {
  background-color: #1d9bf0;
  border: none;
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 16px;
  border-radius: 6px;
}
.dialog-btn-add:hover {
  background-color: #1a8cd8;
}

.dialog-btn-preview {
  background: none;
  border: 1px solid #262626;
  color: #99cbff;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 14px;
  border-radius: 6px;
}
.dialog-btn-preview:hover {
  background-color: #1b1b1b;
}

.preview-container {
  background-color: #0a0a0a;
  border: 1px solid #262626;
  border-radius: 8px;
  padding: 8px;
}

.preview-video {
  opacity: 0.85;
}

.preview-status {
  font-size: 11px;
  font-weight: 500;
  color: #4adf9d;
  margin-top: 4px;
}

.dialog-dropdown {
  min-width: 100px;
}

.dialog-dropdown > button {
  background-color: #1b1b1b;
  border: 1px solid #262626;
  border-radius: 6px;
  color: #FFFFFF;
  font-size: 14px;
  padding: 6px 12px;
}

window.transient-for {
  background-color: #131313;
  color: #FFFFFF;
}
"""


def load_css(provider: object) -> None:
    """Carga la hoja de estilos en el CSS provider de GTK."""
    from gi.repository import Gtk, Gdk

    css_provider = Gtk.CssProvider()
    css_provider.load_from_string(_STYLESHEET)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
