"""Tests para sap_section_bridge."""
import pytest

from coldformedjm.sap_section_bridge import (
    CFShape, channel, push_to_sap, sigma_section, z_section,
)


def test_channel_genera_8_puntos():
    c = channel(h=200, b=80, t=2)
    assert len(c.points_mm) == 8
    assert c.thickness_mm == 2


def test_z_section_genera_8_puntos():
    z = z_section(h=200, b_top=80, b_bot=80, t=2)
    assert len(z.points_mm) == 8


def test_sigma_section_genera_16_puntos():
    s = sigma_section(h=200, b=80, lip=20, t=2)
    assert len(s.points_mm) == 16


def test_to_sap_dict_estructura():
    c = channel(h=200, b=80, t=2, name="C200")
    d = c.to_sap_dict()
    assert d["name"] == "C200"
    assert "polygon" in d
    assert "thickness_mm" in d


def test_push_to_sap_sin_fastsap_devuelve_false():
    # Sin un sap mock real, debe fallar silenciosamente
    c = channel(h=200, b=80, t=2)
    assert push_to_sap(sap=None, shape=c) is False
