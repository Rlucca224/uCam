"""Per-camera recording controller (wraps stream-manager's Recorder in a thread)."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stream-manager"))

from recorder import Recorder  # noqa: E402

from .recordings import RECORDINGS_DIR


class RecordingController:
    """Start/stop recording for a single camera on a background thread."""

    def __init__(
        self,
        camera_name: str,
        rtsp_url: str,
        output_dir: Path | None = None,
        segment_seconds: int = 3600,
        rtsp_timeout_seconds: int = 10,
    ) -> None:
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.segment_seconds = segment_seconds
        self.rtsp_timeout_seconds = rtsp_timeout_seconds
        self.output_dir = output_dir or RECORDINGS_DIR
        self._recorder: Recorder | None = None
        self._thread: threading.Thread | None = None
        self._logger = self._make_logger()
        self._state_listeners: list = []

    def _make_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"ucam.recorder.{self.camera_name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            logger.addHandler(handler)
        return logger

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def current_recording_path(self) -> Path | None:
        """Path of the segment ffmpeg is currently writing, if recording."""
        if not self.is_recording or not self.output_dir.exists():
            return None
        newest: Path | None = None
        for p in self.output_dir.iterdir():
            if not p.is_file() or p.suffix.lower() != ".mp4":
                continue
            if not p.name.startswith(f"{self.camera_name}_"):
                continue
            try:
                if newest is None or p.stat().st_mtime > newest.stat().st_mtime:
                    newest = p
            except OSError:
                continue
        return newest

    def add_state_listener(self, cb: object) -> None:
        self._state_listeners.append(cb)

    def _notify_state(self) -> None:
        is_recording = self.is_recording
        for cb in self._state_listeners:
            cb(is_recording)

    def start(self) -> None:
        if self.is_recording:
            return
        self._recorder = Recorder(
            camera_name=self.camera_name,
            rtsp_url=self.rtsp_url,
            output_dir=self.output_dir,
            segment_seconds=self.segment_seconds,
            rtsp_timeout_seconds=self.rtsp_timeout_seconds,
            logger=self._logger,
        )
        self._thread = threading.Thread(
            target=self._recorder.run,
            name=f"recorder-{self.camera_name}",
            daemon=True,
        )
        self._thread.start()
        self._notify_state()

    def stop(self) -> None:
        if self._recorder is not None:
            self._recorder.request_shutdown()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._recorder = None
        self._thread = None
        self._notify_state()
