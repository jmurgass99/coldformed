"""Configuracion comun de pytest para ColdFormed."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Asegura que el paquete sea importable sin instalar.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def section_dims() -> dict[str, float]:
    """Dimensiones tipicas de una seccion para pruebas."""
    return {"b": 200.0, "h": 400.0, "t": 6.0, "f_y": 355.0}
