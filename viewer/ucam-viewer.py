#!/usr/bin/env python3
"""Entry point del visor nativo CamNet."""

import os
import sys

# Preferir el entorno virtual empaquetado si existe
_VENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
_VENV_PYTHON = os.path.join(_VENV, "bin", "python3")
if os.path.exists(_VENV_PYTHON) and sys.executable != _VENV_PYTHON:
    os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)

from ucam_viewer.main import main

if __name__ == "__main__":
    main()
