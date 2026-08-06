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
