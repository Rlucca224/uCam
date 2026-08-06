"""Dialog styles."""

DIALOG_CSS = """
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

.dialog-dropdown popover.background,
.dialog-dropdown popover {
  background-color: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.dialog-dropdown popover.background > arrow,
.dialog-dropdown popover > arrow {
  background-color: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.dialog-dropdown popover.background contents,
.dialog-dropdown popover contents {
  background-color: #2f2d31;
  border: 1px solid #26262a;
  border-radius: 9px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 1px;
}

.dialog-dropdown popover row,
.dialog-dropdown popover listitem {
  background-color: #2f2d31;
  color: #FFFFFF;
}

.dialog-dropdown popover row:hover,
.dialog-dropdown popover listitem:hover {
  background-color: #403e47;
}

window.transient-for {
  background-color: #131313;
  color: #FFFFFF;
}
"""
