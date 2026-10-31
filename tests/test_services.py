"""Pruebas del servicio de evaluacion de secciones."""
from __future__ import annotations

import pytest

from coldformed.exceptions import GeometryError, MaterialError
from coldformed.services import SectionInput, SectionResult, evaluate_section


@pytest.mark.unit
def test_evaluate_section_devuelve_resultado(section_dims: dict[str, float]) -> None:
    result = evaluate_section(SectionInput(**section_dims))
    assert isinstance(result, SectionResult)
    assert result.section_class in (3, 4)
    assert result.epsilon > 0
    assert result.w_eff_cm3 > 0


@pytest.mark.unit
def test_evaluate_section_clase4_detectada() -> None:
    # Alma muy esbelta -> Clase 4
    result = evaluate_section(SectionInput(b=100.0, h=1000.0, t=3.0, f_y=355.0))
    assert result.section_class == 4


@pytest.mark.unit
def test_geometria_invalida_lanza_geometry_error() -> None:
    with pytest.raises(GeometryError):
        evaluate_section(SectionInput(b=-1.0, h=400.0, t=6.0))


@pytest.mark.unit
def test_material_invalido_lanza_material_error() -> None:
    with pytest.raises(MaterialError):
        evaluate_section(SectionInput(b=200.0, h=400.0, t=6.0, f_y=0.0))


@pytest.mark.unit
def test_resultado_serializable(section_dims: dict[str, float]) -> None:
    result = evaluate_section(SectionInput(**section_dims))
    d = result.to_dict()
    assert set(d.keys()) == {"section_class", "epsilon", "w_eff_cm3"}
