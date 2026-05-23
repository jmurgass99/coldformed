"""Tests signature curve + galvanizing."""
import pytest

from coldformedjm.signature_curve import SignatureInput, signature_curve
from coldformedjm.galvanizing import (
    adjusted_yield, coating_thickness_required_iso1461,
)


class TestSignature:
    def test_curva_tiene_min_local(self):
        r = signature_curve(SignatureInput(width_mm=200, thickness_mm=2))
        assert len(r.minima) >= 2
        local_min = next((m for m in r.minima if m[2] == "Local"), None)
        assert local_min is not None

    def test_distortional_si_existe(self):
        r = signature_curve(SignatureInput(width_mm=150, thickness_mm=1.5))
        modes = [m[2] for m in r.minima]
        assert "Local" in modes


class TestGalvanizing:
    def test_HG_reduce_fy(self):
        assert adjusted_yield(350, "hot_dip_galvanized") == 350 * 0.95

    def test_painted_no_reduce(self):
        assert adjusted_yield(350, "painted") == 350

    def test_invalido(self):
        with pytest.raises(ValueError):
            adjusted_yield(350, "xx")

    def test_coating_thickness_aumenta_con_espesor(self):
        assert coating_thickness_required_iso1461(1.0) == 45
        assert coating_thickness_required_iso1461(8.0) == 85
