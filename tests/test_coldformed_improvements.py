"""Tests de las mejoras de ingeniería en coldformed:
- Bloque consistente de rigidez geométrica de membrana en FSM (fsm.py y fsm_assembly.py).
- Ensamblado real de K_G en FiniteStripMethodSeed (eliminando el stub identidad).
- Abolladura por cortante del alma V_b,Rd según EN 1993-1-3 §6.1.5 (Tabla 6.1).
- Espesores independientes de ala y alma (t_f, t_w) y ala en voladizo en Class4Section.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from coldformed.class4_evaluator import Class4Section
from coldformed.fsm import strip_geometric_stiffness
from coldformed.fsm_assembly import assemble_K_G, build_profile_strips
from coldformed.fsm_master_seed import FiniteStripMethodSeed
from coldformed.shear import EC3ShearInput, shear_capacity_ec3


def test_fsm_membrane_geometric_stiffness_block():
    kg_full = strip_geometric_stiffness(width=100.0, length=500.0, thickness=2.0, sigma_x=150.0)
    kg_memb = kg_full[4:, 4:]
    # Nx * b / (6 * L) = (150 * 2) * 100 / (6 * 500) = 30000 / 3000 = 10.0
    assert kg_memb[0, 0] == pytest.approx(20.0)
    assert kg_memb[0, 2] == pytest.approx(10.0)
    assert np.allclose(kg_full, kg_full.T)

    ps = build_profile_strips("C", {"H": 200.0, "B": 80.0, "D": 20.0, "t": 2.0})
    stress = np.ones(ps.n_strips) * 100.0
    kg_no_m = assemble_K_G(ps, 300.0, stress, include_membrane_kg=False)
    kg_with_m = assemble_K_G(ps, 300.0, stress, include_membrane_kg=True)
    # El DOF axial longitudinal u (índice 0, 4, 8...) es 0 cuando include_membrane_kg=False y >0 cuando True
    assert kg_no_m[0, 0] == pytest.approx(0.0)
    assert kg_with_m[0, 0] > 0.0


def test_fsm_master_seed_builds_real_kg():
    seed = FiniteStripMethodSeed(E=210_000.0, nu=0.30)
    kg_single = seed.build_geometric_stiffness_matrix([0.0, 100.0], thickness=2.0, length=500.0, sigma_x=100.0)
    assert kg_single.shape == (4, 4)
    assert np.allclose(kg_single, kg_single.T)
    assert not np.allclose(kg_single, np.eye(4))

    kg_span = seed.build_geometric_stiffness_matrix([0.0, 50.0, 100.0], thickness=2.0, length=500.0, sigma_x=100.0)
    assert np.allclose(kg_span, kg_single)


def test_ec3_1_3_shear_buckling_regimes():
    # 1) Alma compacta (lambda_w <= 0.83): hw=60, t=2.0, fyb=350 -> lam_w = 0.346*30*sqrt(350/210000) = 0.4238
    r_low = shear_capacity_ec3(EC3ShearInput(hw_mm=60.0, t_mm=2.0, fyb_MPa=350.0))
    assert r_low.lambda_w <= 0.83
    assert r_low.fbv_MPa == pytest.approx(0.58 * 350.0)
    assert r_low.Vb_Rd_kN == pytest.approx(60.0 * 2.0 * 0.58 * 350.0 / 1000.0)

    # 2) Alma intermedia (0.83 < lambda_w < 1.40): hw=160, t=2.0, fyb=350 -> lam_w = 1.130
    r_mid = shear_capacity_ec3(EC3ShearInput(hw_mm=160.0, t_mm=2.0, fyb_MPa=350.0))
    assert 0.83 < r_mid.lambda_w < 1.40
    assert r_mid.fbv_MPa == pytest.approx(0.48 * 350.0 / r_mid.lambda_w)

    # 3) Alma esbelta (lambda_w >= 1.40): comparar sin y con rigidizador en apoyo
    r_unstiff = shear_capacity_ec3(
        EC3ShearInput(hw_mm=300.0, t_mm=1.5, fyb_MPa=350.0, stiffened_at_support=False)
    )
    r_stiff = shear_capacity_ec3(
        EC3ShearInput(hw_mm=300.0, t_mm=1.5, fyb_MPa=350.0, stiffened_at_support=True)
    )
    assert r_unstiff.lambda_w >= 1.40
    assert r_unstiff.fbv_MPa == pytest.approx(0.67 * 350.0 / (r_unstiff.lambda_w ** 2))
    assert r_stiff.fbv_MPa == pytest.approx(0.48 * 350.0 / r_stiff.lambda_w)
    assert r_stiff.Vb_Rd_kN > r_unstiff.Vb_Rd_kN


def test_class4_section_independent_flange_and_web_thickness():
    # Con t_f > t_w el módulo eficaz debe ser mayor que con espesor uniforme igual a t_w
    sec_uniform = Class4Section(b=300.0, h=1200.0, t=8.0, f_y=355.0)
    sec_welded = Class4Section(b=300.0, h=1200.0, t=8.0, f_y=355.0, t_f=20.0, t_w=8.0)
    assert sec_uniform.check_class() == 4
    assert sec_welded.check_class() == 4
    assert sec_welded.calculate_effective_modulus() > sec_uniform.calculate_effective_modulus()
