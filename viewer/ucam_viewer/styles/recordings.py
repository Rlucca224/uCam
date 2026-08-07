"""Recordings section styles."""

RECORDINGS_CSS = """
/* ===== Recordings toolbar ===== */

.recordings-toolbar {
  padding: 16px 20px 14px;
}

.recordings-title {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
}

.recordings-subtitle {
  font-size: 12px;
  color: #9a9a9a;
}

.recordings-filter {
  min-width: 0px;
  background: none;
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  padding: 6px 10px;
}

.recordings-filter:disabled {
  color: #7a7a80;
  opacity: 0.75;
}

/* popup del dropdown alineado al ancho del boton */
dropdown.recordings-filter popover.background,
dropdown.recordings-filter popover {
  background-color: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

dropdown.recordings-filter popover.background > arrow,
dropdown.recordings-filter popover > arrow {
  background-color: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

dropdown.recordings-filter popover.background contents,
dropdown.recordings-filter popover contents {
  background-color: #2f2d31;
  border: 1px solid #26262a;
  border-radius: 9px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 1px;
  min-width: 147px;
}

dropdown.recordings-filter popover scrolledwindow,
dropdown.recordings-filter popover viewport,
dropdown.recordings-filter popover listview,
dropdown.recordings-filter popover list {
  background-color: transparent;
  border: none;
  box-shadow: none;
  outline: none;
  color: #FFFFFF;
}

dropdown.recordings-filter popover listview {
  padding: 0;
}

dropdown.recordings-filter popover row,
dropdown.recordings-filter popover listitem {
  background-color: #2f2d31;
  color: #FFFFFF;
  border: none;
  border-radius: 5px;
  margin: 0;
  padding: 6px 10px;
  min-height: 0;
  font-size: 13px;
  font-weight: 400;
  outline: none;
  box-shadow: none;
}

dropdown.recordings-filter popover row label,
dropdown.recordings-filter popover listitem label,
dropdown.recordings-filter popover row image,
dropdown.recordings-filter popover listitem image {
  color: #FFFFFF;
}

dropdown.recordings-filter popover row:hover,
dropdown.recordings-filter popover listitem:hover {
  background-color: #403e47;
}

dropdown.recordings-filter popover row:selected,
dropdown.recordings-filter popover row.selected,
dropdown.recordings-filter popover row:checked,
dropdown.recordings-filter popover listitem:selected,
dropdown.recordings-filter popover listitem.selected,
dropdown.recordings-filter popover listitem:checked {
  background-color: #2f2d31;
  color: #FFFFFF;
}

dropdown.recordings-filter popover row:selected:hover,
dropdown.recordings-filter popover row:checked:hover,
dropdown.recordings-filter popover listitem:selected:hover,
dropdown.recordings-filter popover listitem:checked:hover {
  background-color: #403e47;
}

dropdown.recordings-filter popover row:active,
dropdown.recordings-filter popover listitem:active {
  background-color: #141414;
}

.recordings-refresh-btn {
  background-color: #1b1b1b;
  border: 1px solid #262626;
  border-radius: 5px;
  padding: 7px 10px;
  min-height: 0px;
  font-size: 14.667px;
  font-weight: 400;
}

.recordings-refresh-btn:hover {
  background-color: #1f1f1f;
}

/* ===== Recording rows ===== */

.recording-row {
  background-color: #161618;
  border: 1px solid #26262a;
  border-radius: 10px;
  padding: 10px;
}

.recording-row:hover {
  background-color: #1c1c1f;
  border-color: #333338;
}

.recording-thumb {
  background-color: #0d0d0f;
  border-radius: 6px;
}

.recording-thumb-icon {
  color: #555559;
  font-size: 40px;
}

.recording-name {
  font-size: 14px;
  font-weight: 600;
  color: #FFFFFF;
}

.recording-meta {
  font-size: 12px;
  color: #9a9a9a;
}

.recording-action-btn {
  background-color: #1b1b1d;
  color: #FFFFFF;
  border: none;
  border-radius: 5px;
  padding: 6px 11px;
  min-height: 0px;
  font-size: 14.667px;
  font-weight: 500;
}

.recording-action-btn .material-icon,
.recording-action-btn-danger .material-icon {
  min-width: 0px;
  font-size: 13px;
}

.recording-action-btn .button-text,
.recording-action-btn-danger .button-text {
  font-size: 13px;
}

.recording-action-btn:hover {
  background-color: #1f1f22;
  border-color: #777777;
}

.recording-action-btn:active {
  background-color: #141414;
}

.recording-action-btn-danger {
  background-color: #1b1b1d;
  color: #ffb4ab;
  border: none;
  border-radius: 5px;
  padding: 6px 11px;
  min-height: 0px;
  font-size: 14.667px;
  font-weight: 500;
}

.recording-action-btn-danger:hover {
  background-color: #2a1c1c;
  border-color: #ffb4ab;
}

/* ===== Selection footer ===== */

.recordings-footer {
  background: #161618;
  border-top: 1px solid #26262a;
  padding: 10px 20px;
}

.recordings-footer-label {
  font-size: 13px;
  font-weight: 600;
  color: #FFFFFF;
}

.recordings-footer-btn {
  background-color: #1b1b1b;
  border: 1px solid #262626;
  border-radius: 5px;
  padding: 6px 12px;
  min-height: 0px;
  font-size: 13px;
  font-weight: 500;
}

.recordings-footer-btn .material-icon {
  font-size: 13px;
  min-width: 0px;
}

.recordings-footer-btn .button-text {
  font-size: 13px;
}

.recordings-footer-btn:hover {
  background-color: #1f1f1f;
}

.recordings-footer-btn-danger {
  background-color: #301414;
  color: #ffb4ab;
  border: none;
  border-radius: 5px;
  padding: 6px 12px;
  min-height: 0px;
  font-size: 13px;
  font-weight: 500;
}

.recordings-footer-btn-danger .material-icon {
  font-size: 13px;
  min-width: 0px;
}

.recordings-footer-btn-danger .button-text {
  font-size: 13px;
}

.recordings-footer-btn-danger:hover {
  background-color: #3a1a1a;
}

.recording-check {
  margin-right: 4px;
}

/* ===== Empty state ===== */

.recordings-empty-icon {
  color: #3a3a3d;
  font-size: 56px;
}

.recordings-empty-text {
  font-size: 13px;
  color: #9a9a9a;
}
"""
