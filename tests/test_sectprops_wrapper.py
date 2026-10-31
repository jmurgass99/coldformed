"""Tests del wrapper sectionproperties."""
from __future__ import annotations
import pytest

sp = pytest.importorskip("sectionproperties")
from coldformed.sectprops_wrapper import (
    SectionProperties,
    analyze_i_section, analyze_channel_section, analyze_hollow_rect_section,
)


@pytest.mark.slow
def test_i_section_w24x76_approx():
    """Perfil similar a W24x76: d=608, b=228, tf=17.3, tw=11."""
    res = analyze_i_section(d=608, b=228, tf=17.3, tw=11.0, name="W24x76_like")
    assert res.area_mm2 > 0
    # W24x76 tabulado: A ~ 14,500 mm2 (sin radios de transicion)
    assert 13000 < res.area_mm2 < 16000
    assert res.Ixx_mm4 > 0
    assert res.Iyy_mm4 > 0
    assert res.Ixx_mm4 > res.Iyy_mm4  # eje fuerte


@pytest.mark.slow
def test_channel_section_basic():
    res = analyze_channel_section(d=200, b=80, tf=10, tw=8, name="C200x80")
    assert res.area_mm2 > 0
    # x_centroid debe estar fuera del medio (perfil asimetrico)
    assert res.x_centroid_mm > 0


@pytest.mark.slow
def test_hollow_rect_basic():
    res = analyze_hollow_rect_section(d=200, b=100, t=8, name="HSS200x100x8")
    # Area aprox 2*(d+b)*t - 4*t^2 = 2*300*8 - 4*64 = 4544
    assert 4000 < res.area_mm2 < 5000


def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        analyze_i_section(d=-100, b=100, tf=10, tw=10)
    with pytest.raises(ValueError):
        analyze_i_section(d=20, b=100, tf=15, tw=10)  # d <= 2*tf
    with pytest.raises(ValueError):
        analyze_hollow_rect_section(d=100, b=100, t=60)  # t >= dim/2


@pytest.mark.slow
def test_section_properties_dataclass_complete():
    res = analyze_hollow_rect_section(d=150, b=100, t=6)
    assert isinstance(res, SectionProperties)
    assert res.J_torsion_mm4 > 0
    assert res.rxx_mm > 0
    assert res.ryy_mm > 0
    assert len(res.notes) >= 2
