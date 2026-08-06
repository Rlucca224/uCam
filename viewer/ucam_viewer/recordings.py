"""Modelo y utilidades para grabaciones de cámaras."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402

RECORDINGS_DIR = Path(GLib.get_user_data_dir()) / "ucam" / "recordings"
THUMB_DIR = Path(GLib.get_user_cache_dir()) / "ucam" / "thumbnails"

_FILENAME_RE = re.compile(r"^(?P<camera>.+)_(?P<ts>\d{8}_\d{6})\.mp4$")


@dataclass
class RecordingInfo:
    path: Path
    camera_name: str
    timestamp: datetime
    size: int
    duration: float | None = None


def parse_filename(name: str) -> tuple[str, datetime] | None:
    """Parse 'CAMERA_YYYYMMDD_HHMMSS.mp4' -> (camera, datetime)."""
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    try:
        ts = datetime.strptime(m.group("ts"), "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    return m.group("camera"), ts


def scan_recordings(directory: Path | None = None) -> list[RecordingInfo]:
    """List recordings newest-first."""
    d = directory or RECORDINGS_DIR
    if not d.exists():
        return []
    out: list[RecordingInfo] = []
    for p in d.iterdir():
        if not p.is_file() or p.suffix.lower() != ".mp4":
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        parsed = parse_filename(p.name)
        if parsed is None:
            camera, ts = p.stem, datetime.fromtimestamp(p.stat().st_mtime)
        else:
            camera, ts = parsed
        out.append(RecordingInfo(path=p, camera_name=camera, timestamp=ts, size=size))
    out.sort(key=lambda r: r.timestamp, reverse=True)
    return out


def discover_duration(path: Path) -> float | None:
    """Duration in seconds via GStreamer Discoverer (blocking; call off-thread)."""
    import gi  # noqa: F401

    gi.require_version("Gst", "1.0")
    gi.require_version("GstPbutils", "1.0")
    from gi.repository import Gst, GstPbutils  # noqa: E402

    Gst.init(None)
    try:
        info = GstPbutils.Discoverer.new(5 * Gst.SECOND).discover_uri(path.as_uri())
    except GLib.Error:
        return None
    return info.get_duration() / 1e9


def thumbnail_key(path: Path) -> str:
    st = path.stat()
    return f"{path.stem}_{st.st_size}_{int(st.st_mtime)}.jpg"


def thumbnail_for(path: Path) -> Path | None:
    t = THUMB_DIR / thumbnail_key(path)
    return t if t.exists() else None


def generate_thumbnail(path: Path) -> Path:
    """Extract first frame with ffmpeg into the cache dir (blocking; off-thread)."""
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    t = THUMB_DIR / thumbnail_key(path)
    if t.exists():
        return t
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", "1", "-i", str(path),
            "-frames:v", "1", "-vf", "scale=160:90", str(t),
        ],
        capture_output=True,
    )
    return t


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d %b %Y, %H:%M")
