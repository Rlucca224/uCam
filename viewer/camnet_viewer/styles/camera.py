"""Camera grid and list styles."""

CAMERA_CSS = """
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
"""
