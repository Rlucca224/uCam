"""Sidebar styles."""

SIDEBAR_CSS = """
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
"""
