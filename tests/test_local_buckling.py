# -*- coding: utf-8 -*-
"""Tests del pandeo local de placa (engine analitico + kernel JIT expuesto)."""
import math

import numpy as np
import pytest

from coldformedjm.local_buckling import (
    LocalBucklingResult,
    assemble_strip_matrices_jit,
    local_critical_stress,
    local_critical_stress_fsm,
)


class TestEngineAnalitico:
    def test_ss_ss_k_igual_4(self):
        r = local_critical_stress(200.0, 6.0, boundary="ss_ss")
        assert r.k == pytest.approx(4.0)
        assert isinstance(r, LocalBucklingResult)

    def test_ss_free_k_igual_0p425(self):
        r = local_critical_stress(80.0, 10.0, boundary="ss_free")
        assert r.k == pytest.approx(0.425)

    def test_formula_bryan(self):
        # sigma_cr = k pi^2 E /(12(1-nu^2)) (t/b)^2
        b, t, E, nu, k = 200.0, 6.0, 210000.0, 0.30, 4.0
        esperado = k * math.pi ** 2 * E / (12.0 * (1 - nu ** 2)) * (t / b) ** 2
        r = local_critical_stress(b, t, E_MPa=E, nu=nu, boundary="ss_ss")
        assert r.sigma_cr_MPa == pytest.approx(esperado, rel=1e-9)

    def test_placa_esbelta_sigma_cr_bajo(self):
        # Pared delgada de viga cajon de acero: b/t = 400 -> sigma_cr << Fy.
        r = local_critical_stress(2400.0, 6.0, E_MPa=200000.0, boundary="ss_ss")
        assert r.slenderness == pytest.approx(400.0)
        assert r.sigma_cr_MPa < 50.0

    def test_placa_robusta_sigma_cr_alto(self):
        r = local_critical_stress(80.0, 10.0, E_MPa=200000.0, boundary="ss_free")
        assert r.sigma_cr_MPa > 345.0  # supera la fluencia -> estable

    def test_sigma_cr_escala_con_t_sobre_b_cuadrado(self):
        r1 = local_critical_stress(200.0, 6.0, boundary="ss_ss")
        r2 = local_critical_stress(400.0, 6.0, boundary="ss_ss")  # b x2 -> sigma/4
        assert r1.sigma_cr_MPa / r2.sigma_cr_MPa == pytest.approx(4.0, rel=1e-9)


class TestKernelJITExpuesto:
    def test_matrices_4x4_simetricas(self):
        ke, kg = assemble_strip_matrices_jit(160.0, 6.0, 200.0)
        assert ke.shape == (4, 4) and kg.shape == (4, 4)
        assert np.allclose(ke, ke.T)
        assert np.allclose(kg, kg.T)

    def test_kg_patron_masa_no_calibrado(self):
        # Kg ahora es la rigidez geometrica calibrada: escala con sigma_x y con
        # (pi/L)^2 (NO es una matriz de masa estatica).
        _ke1, kg1 = assemble_strip_matrices_jit(160.0, 6.0, 200.0, sigma_ref_MPa=1.0)
        _ke2, kg2 = assemble_strip_matrices_jit(160.0, 6.0, 200.0, sigma_ref_MPa=2.0)
        assert np.allclose(kg2, 2.0 * kg1)  # lineal en sigma_x
        _ke3, kg3 = assemble_strip_matrices_jit(160.0, 6.0, 400.0, sigma_ref_MPa=1.0)
        # L x2 -> (pi/L)^2 a la cuarta parte -> kg a la cuarta parte.
        assert np.allclose(kg3, kg1 / 4.0)


class TestEngineFSM:
    def test_converge_ss_ss_k4(self):
        r = local_critical_stress_fsm(200.0, 6.0, boundary="ss_ss", n_strips=8)
        assert r.k == pytest.approx(4.0, abs=0.01)
        assert r.method.startswith("FSM")

    def test_converge_ss_free_outstand(self):
        r = local_critical_stress_fsm(200.0, 6.0, boundary="ss_free", n_strips=16)
        assert r.k == pytest.approx(0.425, abs=0.01)

    def test_fsm_concuerda_con_analitico(self):
        for bnd, tol in (("ss_ss", 0.01), ("ss_free", 0.03)):
            a = local_critical_stress(200.0, 6.0, boundary=bnd)
            f = local_critical_stress_fsm(200.0, 6.0, boundary=bnd,
                                          n_strips=12 if bnd == "ss_free" else 8)
            assert f.sigma_cr_MPa == pytest.approx(a.sigma_cr_MPa, rel=tol)

    def test_fsm_escala_t_sobre_b(self):
        # sigma_cr ~ (t/b)^2: duplicar b -> sigma_cr a la cuarta parte.
        r1 = local_critical_stress_fsm(200.0, 6.0, boundary="ss_ss", n_strips=8)
        r2 = local_critical_stress_fsm(400.0, 6.0, boundary="ss_ss", n_strips=8)
        assert r1.sigma_cr_MPa / r2.sigma_cr_MPa == pytest.approx(4.0, rel=0.02)
