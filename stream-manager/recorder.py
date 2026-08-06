#!/usr/bin/env python3
"""
CamNet - Stream Manager (Hito 1)
=================================

Se conecta a una única cámara IP por RTSP, graba segmentos de video a disco
usando FFmpeg, y se reconecta automáticamente ante caídas de la cámara o
de la red, con backoff exponencial para no martillar la conexión.

Uso:
    python3 recorder.py --camera-name entrada --rtsp-url rtsp://user:pass@192.168.1.50:554/stream1

    O, para no exponer la contraseña en la lista de procesos del sistema
    (recomendado):
        export UCAM_RTSP_URL="rtsp://user:pass@192.168.1.50:554/stream1"
        python3 recorder.py --camera-name entrada

Requiere: ffmpeg y ffprobe instalados y disponibles en el PATH.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

def setup_logging(camera_name: str, log_file: str | None) -> logging.Logger:
    """Configura logging a consola y, opcionalmente, a un archivo."""
    logger = logging.getLogger(f"ucam.recorder.{camera_name}")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


# ---------------------------------------------------------------------------
# Verificación de conectividad
# ---------------------------------------------------------------------------

def check_stream(rtsp_url: str, timeout_seconds: int = 10) -> bool:
    """
    Usa ffprobe para verificar que el stream RTSP responde antes de intentar
    grabar. Evita lanzar ffmpeg contra una cámara que sabemos caída y llenar
    los logs de ruido.
    """
    cmd = [
        "ffprobe",
        "-rtsp_transport", "tcp",
        "-timeout", str(timeout_seconds * 1_000_000),  # microsegundos
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-of", "csv=p=0",
        rtsp_url,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout_seconds + 5,
            text=True,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe no está instalado o no está en el PATH. "
            "Instalá ffmpeg (incluye ffprobe) antes de continuar."
        )


# ---------------------------------------------------------------------------
# Construcción del comando de grabación
# ---------------------------------------------------------------------------

def build_ffmpeg_command(
    rtsp_url: str,
    output_dir: Path,
    camera_name: str,
    segment_seconds: int,
    rtsp_timeout_seconds: int,
) -> list[str]:
    """
    Arma el comando de ffmpeg para grabar por segmentos (segment muxer),
    sin recodificar (-c copy) para minimizar uso de CPU, con nombres de
    archivo basados en timestamp real (-strftime 1).
    """
    output_pattern = str(output_dir / f"{camera_name}_%Y%m%d_%H%M%S.mp4")
    return [
        "ffmpeg",
        "-nostdin",
        "-loglevel", "warning",
        "-rtsp_transport", "tcp",
        "-timeout", str(rtsp_timeout_seconds * 1_000_000),  # microsegundos
        "-i", rtsp_url,
        "-c", "copy",
        "-an",
        "-f", "segment",
        "-segment_time", str(segment_seconds),
        "-segment_format", "mp4",
        "-reset_timestamps", "1",
        "-strftime", "1",
        output_pattern,
    ]


# ---------------------------------------------------------------------------
# Loop principal de grabación con reconexión
# ---------------------------------------------------------------------------

class Recorder:
    def __init__(
        self,
        camera_name: str,
        rtsp_url: str,
        output_dir: Path,
        segment_seconds: int,
        rtsp_timeout_seconds: int,
        logger: logging.Logger,
    ) -> None:
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.output_dir = output_dir
        self.segment_seconds = segment_seconds
        self.rtsp_timeout_seconds = rtsp_timeout_seconds
        self.logger = logger

        self._shutdown_requested = False
        self._current_process: subprocess.Popen | None = None

        # Un proceso se considera "run estable" si duró más que esto.
        # Si murió antes, es señal de fallo real (no un shutdown normal
        # de nuestra parte) y aplicamos backoff.
        self._min_stable_run_seconds = 15
        self._backoff_seconds = 1
        self._max_backoff_seconds = 60

    def request_shutdown(self) -> None:
        self._shutdown_requested = True
        if self._current_process and self._current_process.poll() is None:
            self.logger.info("Enviando señal de apagado a ffmpeg (SIGINT)...")
            self._current_process.send_signal(signal.SIGINT)

    def run(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            "Iniciando grabación de '%s' -> %s (segmentos de %ss)",
            self.camera_name, self.output_dir, self.segment_seconds,
        )

        while not self._shutdown_requested:
            if not check_stream(self.rtsp_url, timeout_seconds=self.rtsp_timeout_seconds):
                self.logger.warning(
                    "Cámara '%s' no responde. Reintentando en %ss...",
                    self.camera_name, self._backoff_seconds,
                )
                self._sleep_with_shutdown_check(self._backoff_seconds)
                self._increase_backoff()
                continue

            self.logger.info("Cámara '%s' responde. Iniciando ffmpeg.", self.camera_name)
            exit_code, run_duration = self._record_until_process_exits()

            if self._shutdown_requested:
                self.logger.info("Grabación de '%s' finalizada por pedido de apagado.", self.camera_name)
                break

            if run_duration >= self._min_stable_run_seconds:
                # Corrió suficiente tiempo antes de caerse: probablemente fue
                # un corte de red puntual, no un problema persistente.
                self._reset_backoff()
                self.logger.warning(
                    "ffmpeg terminó (código %s) tras %.0fs de grabación estable. Reconectando...",
                    exit_code, run_duration,
                )
            else:
                self._increase_backoff()
                self.logger.error(
                    "ffmpeg terminó (código %s) tras solo %.0fs. Posible fallo persistente. "
                    "Reintentando en %ss...",
                    exit_code, run_duration, self._backoff_seconds,
                )
                self._sleep_with_shutdown_check(self._backoff_seconds)

        self.logger.info("Recorder de '%s' detenido.", self.camera_name)

    # -- helpers internos ----------------------------------------------

    def _record_until_process_exits(self) -> tuple[int, float]:
        cmd = build_ffmpeg_command(
            self.rtsp_url, self.output_dir, self.camera_name,
            self.segment_seconds, self.rtsp_timeout_seconds,
        )
        start = time.monotonic()
        self._current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Volcamos stderr de ffmpeg a nuestro logger en vivo, línea por línea.
        assert self._current_process.stderr is not None
        for line in self._current_process.stderr:
            line = line.strip()
            if line:
                self.logger.debug("[ffmpeg] %s", line)

        exit_code = self._current_process.wait()
        duration = time.monotonic() - start
        self._current_process = None
        return exit_code, duration

    def _sleep_with_shutdown_check(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while not self._shutdown_requested and time.monotonic() < deadline:
            time.sleep(0.5)

    def _increase_backoff(self) -> None:
        self._backoff_seconds = min(self._backoff_seconds * 2, self._max_backoff_seconds)

    def _reset_backoff(self) -> None:
        self._backoff_seconds = 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CamNet - Recorder de una cámara RTSP (Hito 1)")
    parser.add_argument("--camera-name", required=True, help="Nombre identificador de la cámara (usado en nombres de archivo y logs)")
    parser.add_argument(
        "--rtsp-url",
        default=None,
        help="URL RTSP completa. Si no se pasa, se lee de la variable de entorno UCAM_RTSP_URL "
             "(recomendado, evita exponer la contraseña en `ps aux`).",
    )
    parser.add_argument("--output-dir", default="./recordings", help="Directorio donde guardar los segmentos grabados")
    parser.add_argument("--segment-seconds", type=int, default=300, help="Duración de cada segmento grabado, en segundos (default: 300 = 5 min)")
    parser.add_argument("--rtsp-timeout-seconds", type=int, default=10, help="Timeout de conexión/lectura RTSP, en segundos")
    parser.add_argument("--log-file", default=None, help="Ruta opcional a un archivo de log (además de stdout)")
    parser.add_argument("--verbose", action="store_true", help="Incluye el output crudo de ffmpeg en los logs (nivel DEBUG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rtsp_url = args.rtsp_url or os.environ.get("UCAM_RTSP_URL")
    if not rtsp_url:
        print(
            "Error: no se especificó una URL RTSP. Usá --rtsp-url o la variable "
            "de entorno UCAM_RTSP_URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    logger = setup_logging(args.camera_name, args.log_file)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    recorder = Recorder(
        camera_name=args.camera_name,
        rtsp_url=rtsp_url,
        output_dir=Path(args.output_dir),
        segment_seconds=args.segment_seconds,
        rtsp_timeout_seconds=args.rtsp_timeout_seconds,
        logger=logger,
    )

    def handle_signal(signum, frame):  # noqa: ANN001, ARG001
        logger.info("Señal de apagado recibida (%s). Cerrando de forma prolija...", signum)
        recorder.request_shutdown()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    recorder.run()


if __name__ == "__main__":
    main()
