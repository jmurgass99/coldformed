"""Pruebas de la jerarquia de excepciones."""
from __future__ import annotations

import pytest

from coldformedjm.exceptions import (
    ColdFormedError,
    GeometryError,
    MaterialError,
    ValidationError,
)


@pytest.mark.unit
def test_jerarquia_base() -> None:
    assert issubclass(ValidationError, ColdFormedError)
    assert issubclass(GeometryError, ValidationError)
    assert issubclass(MaterialError, ValidationError)


@pytest.mark.unit
def test_geometry_error_es_atrapable_como_base() -> None:
    with pytest.raises(ColdFormedError):
        raise GeometryError("b <= 0")


@pytest.mark.unit
def test_material_error_es_validation() -> None:
    with pytest.raises(ValidationError):
        raise MaterialError("f_y invalido")


@pytest.mark.unit
def test_mensaje_se_preserva() -> None:
    exc = GeometryError("dim invalida")
    assert str(exc) == "dim invalida"
