"""Modelos de datos del visor de cámaras."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402


class CameraStatus(Enum):
    CONNECTING = auto()
    LIVE = auto()
    RECORDING = auto()
    NO_SIGNAL = auto()
    ERROR = auto()


@dataclass
class CameraConfig:
    name: str
    rtsp_url: str


@dataclass
class CameraState:
    config: CameraConfig
    status: CameraStatus = CameraStatus.CONNECTING
    pipeline: Gst.Pipeline | None = None
    paintable: object | None = None
