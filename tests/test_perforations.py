"""Tests para reducción por perforaciones."""
import pytest
from coldformedjm.perforations import HoleSpec, reduce_for_holes, Pn_with_holes


def test_no_holes_no_reduction():
    spec = HoleSpec(diameter_mm=20.0, n_holes=0, web_width_mm=200.0, thickness_mm=2.0)
    r = reduce_for_holes(spec, code="AISI")
    assert r.A_net_mm2 == pytest.approx(r.A_gross_mm2)
    assert r.reduction_factor == pytest.approx(1.0)


def test_holes_reduce_area_aisi():
    spec = HoleSpec(diameter_mm=20.0, n_holes=3, web_width_mm=200.0, thickness_mm=2.0,
                    spacing_mm=600.0)
    r = reduce_for_holes(spec, code="AISI")
    # A_gross = 400, A_holes = 3*20*2=120, A_net=280, reduction=0.7
    assert r.A_net_mm2 == pytest.approx(280.0)
    assert r.reduction_factor == pytest.approx(0.7)
    assert len(r.warnings) == 0


def test_eurocode_kw_penalty():
    spec = HoleSpec(diameter_mm=40.0, n_holes=2, web_width_mm=200.0, thickness_mm=2.0)
    r_en = reduce_for_holes(spec, code="EN")
    r_aisi = reduce_for_holes(spec, code="AISI")
    assert r_en.reduction_factor <= r_aisi.reduction_factor


def test_pn_with_holes_multi_code():
    spec = HoleSpec(diameter_mm=15.0, n_holes=2, web_width_mm=150.0, thickness_mm=1.5)
    for code in ("AISI", "EN", "AS", "NSR"):
        pn = Pn_with_holes(100.0, spec, code=code)
        assert 0 < pn < 100.0


def test_invalid_inputs():
    with pytest.raises(ValueError):
        reduce_for_holes(HoleSpec(0.0, 1, 100.0, 1.0))
    with pytest.raises(ValueError):
        reduce_for_holes(HoleSpec(10.0, 1, 100.0, 1.0), code="ZZ")
