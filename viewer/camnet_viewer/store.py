"""Camera persistence layer. JSON-backed; swappable to SQLite later."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .models import CameraConfig

logger = logging.getLogger("camnet.viewer")

CAMNET_DIR = Path.home() / ".config" / "camnet"
CAMERAS_FILE = CAMNET_DIR / "cameras.json"


class CameraStore:
    """Loads and saves camera configurations from/to a JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or CAMERAS_FILE

    def load(self) -> list[CameraConfig]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read %s: %s", self._path, exc)
            return []
        cameras: list[CameraConfig] = []
        for entry in data:
            if isinstance(entry, dict) and "name" in entry and "rtsp_url" in entry:
                cameras.append(CameraConfig(name=entry["name"], rtsp_url=entry["rtsp_url"]))
        return cameras

    def save(self, cameras: list[CameraConfig]) -> None:
        CAMNET_DIR.mkdir(parents=True, exist_ok=True)
        data = [{"name": c.name, "rtsp_url": c.rtsp_url} for c in cameras]
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved %d cameras to %s", len(cameras), self._path)

    def add(self, camera: CameraConfig) -> list[CameraConfig]:
        cameras = self.load()
        urls = {c.rtsp_url for c in cameras}
        if camera.rtsp_url in urls:
            return cameras
        cameras.append(camera)
        self.save(cameras)
        return cameras

    def remove(self, rtsp_url: str) -> list[CameraConfig]:
        cameras = self.load()
        cameras = [c for c in cameras if c.rtsp_url != rtsp_url]
        self.save(cameras)
        return cameras
