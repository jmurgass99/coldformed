# -*- coding: utf-8 -*-
"""Cortante AISI §G2 + interacciones §H1."""
import math

import pytest

from coldformedjm.shear import ShearInput, shear_capacity
from coldformedjm.interaction import bending_shear, axial_bending


class TestShear:
    def test_alma_compacta_fluencia(self):
        # Alma gruesa (h/t bajo) -> regimen de fluencia, Vn = 0.6 Fy Aw.
        r = shear_capacity(ShearInput(h_mm=100.0, t_mm=4.0, Fy_MPa=350.0))
        assert r.regime == "fluencia"
        assert r.Vn_kN == pytest.approx(0.6 * 350.0 * 100.0 * 4.0 / 1e3, rel=1e-9)

    def test_alma_esbelta_pandeo_elastico(self):
        # Alma muy esbelta (h/t alto) -> pandeo elastico, Vn = Vcr < Vy.
        r = shear_capacity(ShearInput(h_mm=400.0, t_mm=1.0, Fy_MPa=350.0))
        assert r.regime == "pandeo elastico"
        assert r.Vn_kN == pytest.approx(r.Vcr_kN, rel=1e-9)
        assert r.Vn_kN < r.Vy_kN

    def test_lambda_monotona(self):
        gruesa = shear_capacity(ShearInput(150.0, 3.0, 350.0)).lambda_v
        esbelta = shear_capacity(ShearInput(300.0, 1.5, 350.0)).lambda_v
        assert esbelta > gruesa


class TestInteraction:
    def test_MV_circular(self):
        r = bending_shear(60.0, 100.0, 30.0, 100.0)  # 0.6, 0.3
        assert r.ratio == pytest.approx(math.sqrt(0.6 ** 2 + 0.3 ** 2), rel=1e-9)
        assert r.ok

    def test_MV_excede(self):
        r = bending_shear(90.0, 100.0, 80.0, 100.0)
        assert not r.ok

    def test_PM_lineal(self):
        r = axial_bending(40.0, 100.0, 30.0, 100.0, 10.0, 100.0)
        assert r.ratio == pytest.approx(0.4 + 0.3 + 0.1, rel=1e-9)
        assert r.ok

    def test_PM_excede(self):
        r = axial_bending(60.0, 100.0, 60.0, 100.0)
        assert not r.ok
