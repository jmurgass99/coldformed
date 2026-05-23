# -*- coding: utf-8 -*-
"""Web crippling (AISI G5) + torsion de seccion abierta."""
import math

import pytest

from coldformedjm.web_crippling import web_crippling_strength, COEFF_SETS, PHI_WC
from coldformedjm.torsion_open import (
    torsion_constant_J,
    st_venant_shear_stress,
    warping_constant_channel,
    torsion_check,
)


class TestWebCrippling:
    def test_resistencia_positiva(self):
        r = web_crippling_strength(t_mm=2.0, Fy_MPa=350.0, R_mm=4.0, N_mm=100.0, h_mm=200.0)
        assert r.Pn_kN > 0
        assert r.Pn_design_kN == pytest.approx(PHI_WC * r.Pn_kN, rel=1e-9)

    def test_interior_mayor_que_extremo(self):
        # Coef. C interior (13) > extremo (4) -> mayor resistencia (1 ala).
        intr = web_crippling_strength(2.0, 350.0, 4.0, 100.0, 200.0, "stiffened_interior_one_flange").Pn_kN
        end = web_crippling_strength(2.0, 350.0, 4.0, 100.0, 200.0, "stiffened_end_one_flange").Pn_kN
        assert intr > end

    def test_mayor_apoyo_mas_resistencia(self):
        corto = web_crippling_strength(2.0, 350.0, 4.0, 50.0, 200.0).Pn_kN
        largo = web_crippling_strength(2.0, 350.0, 4.0, 150.0, 200.0).Pn_kN
        assert largo > corto    # N mayor (1 + CN sqrt(N/t)) -> mas resistencia

    def test_alma_esbelta_reduce(self):
        compacta = web_crippling_strength(2.0, 350.0, 4.0, 100.0, 100.0).Pn_kN
        esbelta = web_crippling_strength(2.0, 350.0, 4.0, 100.0, 400.0).Pn_kN
        assert esbelta < compacta   # (1 - Ch sqrt(h/t)) penaliza el alma esbelta

    def test_caso_invalido(self):
        with pytest.raises(Exception):
            web_crippling_strength(2.0, 350.0, 4.0, 100.0, 200.0, case="inexistente")


class TestTorsion:
    def test_J_formula(self):
        # Canal: alma 200x2 + 2 alas 60x2 -> J = (1/3)(200·8 + 2·60·8)
        elems = [(200.0, 2.0), (60.0, 2.0), (60.0, 2.0)]
        J = torsion_constant_J(elems)
        assert J == pytest.approx((200 * 8 + 60 * 8 + 60 * 8) / 3.0, rel=1e-9)

    def test_cortante_sv(self):
        tau = st_venant_shear_stress(T_Nmm=1.0e6, t_max_mm=2.0, J_mm4=853.3)
        assert tau == pytest.approx(1.0e6 * 2.0 / 853.3, rel=1e-6)

    def test_warping_positivo(self):
        Cw = warping_constant_channel(h_mm=200.0, b_mm=60.0, t_mm=2.0)
        assert Cw > 0

    def test_check_falla_con_torsion_alta(self):
        elems = [(200.0, 2.0), (60.0, 2.0), (60.0, 2.0)]
        bajo = torsion_check(elems, T_Nmm=5.0e4, t_max_mm=2.0, Fy_MPa=350.0)
        alto = torsion_check(elems, T_Nmm=5.0e7, t_max_mm=2.0, Fy_MPa=350.0)
        assert bajo.ok and not alto.ok
