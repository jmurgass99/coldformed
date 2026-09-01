"""
test_golden_coldformed_dsm.py — Golden Tests para ColdFormedJm
==============================================================
Verificaciones contra teoría de placas y Direct Strength Method:

1. Golden 1: Esfuerzo crítico de pandeo local de placa según Bryan (1891) y Timoshenko (1961).
   Fuente: Timoshenko & Gere, Theory of Elastic Stability 2nd Ed. Section 9.3 / Bryan (1891)
2. Golden 2: Resistencia nominal a flexión DSM según AISI S100-16 y Schafer (2008).
   Fuente: AISI S100-16 Chapter F / Schafer (2008) Example 1
"""
from __future__ import annotations

import math
import pytest

from coldformedjm.direct_strength import DSMFlexureInput, dsm_flexure
from coldformedjm.local_buckling import local_critical_stress


class TestGoldenColdFormedDSM:
    """Golden tests con fuentes normativas y bibliográficas de acero conformado en frío."""

    def test_golden_1_bryan_timoshenko_plate_local_buckling(self):
        """Golden Test 1: Pandeo local elástico de placa rectangular comprimida (Bryan/Timoshenko).

        Fuente: Timoshenko & Gere, Theory of Elastic Stability 2nd Ed. Section 9.3 / Bryan (1891)

        Derivación analítica:
        - Placa simplemente apoyada en los 4 bordes (ss_ss, k = 4.0):
          * b = 200 mm, t = 2.0 mm -> b/t = 100.
          * E = 210,000 MPa, nu = 0.30.
          * Rigidez a flexión de placa:
            D = E * t³ / (12 * (1 - nu²)) = 210000 * 8.0 / (12 * 0.91) = 1680000 / 10.92 = 153846.154 N·mm.
          * Esfuerzo crítico teórico:
            sigma_cr = k * pi² * D / (b² * t)
            sigma_cr = 4.0 * pi² * 153846.154 / (200² * 2.0) = 6073629.37 / 80000 = 75.9204 MPa.
        """
        res = local_critical_stress(
            width_mm=200.0,
            thickness_mm=2.0,
            E_MPa=210000.0,
            nu=0.30,
            boundary="ss_ss",
        )

        assert res.k == pytest.approx(4.0, rel=1e-4)
        assert res.slenderness == pytest.approx(100.0, rel=1e-4)

        D = (210000.0 * (2.0**3)) / (12.0 * (1.0 - 0.30**2))
        expected_sigma_cr = (4.0 * (math.pi**2) * D) / ((200.0**2) * 2.0)

        assert res.sigma_cr_MPa == pytest.approx(expected_sigma_cr, rel=1e-4)
        assert res.sigma_cr_MPa == pytest.approx(75.9204, rel=1e-4)

    def test_golden_2_aisi_s100_dsm_flexure_strength(self):
        """Golden Test 2: Resistencia a flexión por Direct Strength Method (DSM).

        Fuente: AISI S100-16 Chapter F / Schafer (2008) Example 1

        Derivación analítica:
        - Perfil C: Sf = 50,000 mm³, Fy = 350 MPa.
        - Momento de fluencia:
          My = Sf * Fy / 1e6 = 50000 * 350 / 1e6 = 17.50 kN·m.
        - Pandeos críticos FSM:
          * Pandeo local: Mcrl = 12.0 kN·m -> lambda_l = sqrt(17.50 / 12.0) = 1.2076 > 0.776.
            Mnl = (1 - 0.15 * (12.0/17.50)^0.4) * (12.0/17.50)^0.4 * 17.50
            (12.0/17.50)^0.4 = 0.86016
            Mnl = (1 - 0.15 * 0.86016) * 0.86016 * 17.50 = (1 - 0.12902) * 15.0528 = 0.87098 * 15.0528 = 13.1106 kN·m.
          * Pandeo distorsional: Mcrd = 15.0 kN·m -> lambda_d = sqrt(17.50 / 15.0) = 1.0797 > 0.673.
            Mnd = (1 - 0.22 * sqrt(15.0/17.50)) * sqrt(15.0/17.50) * 17.50
            sqrt(15.0/17.50) = 0.92582
            Mnd = (1 - 0.22 * 0.92582) * 0.92582 * 17.50 = (1 - 0.20368) * 16.20185 = 0.79632 * 16.20185 = 12.9018 kN·m.
          * Pandeo global: Mcre = 50.0 kN·m >= 2.78 * 17.50 = 48.65 kN·m -> Mne = My = 17.50 kN·m.
        - Resistencia gobernante:
          Mn = min(Mnl, Mnd, Mne) = min(13.1106, 12.9018, 17.50) = 12.9018 kN·m (Gobernado por Pandeo Distorsional).
        """
        inp = DSMFlexureInput(
            Mcrl_kNm=12.0,
            Mcrd_kNm=15.0,
            Mcre_kNm=50.0,
            Sf_mm3=50000.0,
            Fy_MPa=350.0,
        )
        res = dsm_flexure(inp)

        assert res.My_kNm == pytest.approx(17.50, rel=1e-4)
        assert res.Mnl_kNm == pytest.approx(13.1106, rel=1e-3)
        assert res.Mnd_kNm == pytest.approx(12.9018, rel=1e-3)
        assert res.Mne_kNm == pytest.approx(17.50, rel=1e-4)
        assert res.Mn_kNm == pytest.approx(12.9018, rel=1e-3)
        assert res.governing_mode == "distortional"
