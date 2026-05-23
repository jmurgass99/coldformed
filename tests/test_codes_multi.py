"""Tests ColdFormed multi-código."""
import pytest

from coldformedjm.codes_multi import (
    code_description, design_resistance_compression, design_resistance_flexure,
)


def test_5_codes_flexure():
    for c in ("US", "CO", "AU", "EU", "SG"):
        M_d = design_resistance_flexure(c, Mn_kNm=100)
        assert M_d > 0


def test_eu_aplica_gamma():
    M_us = design_resistance_flexure("US", 100)
    M_eu = design_resistance_flexure("EU", 100)
    # EU usa γ=1.0 → M_eu = 100
    assert M_eu == 100
    # US usa φ=0.9 → 90
    assert M_us == 90


def test_descriptions():
    for c in ("US", "CO", "AU", "EU", "SG"):
        assert code_description(c) != ""


def test_invalid():
    with pytest.raises(ValueError):
        design_resistance_compression("XX", 100)
