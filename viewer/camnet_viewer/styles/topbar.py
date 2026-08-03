"""Topbar styles."""

TOPBAR_CSS = """
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
"""
