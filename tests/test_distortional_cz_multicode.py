"""coldformed.tests.test_distortional_cz_multicode
=================================================
Validación rigurosa de pandeo distorsional para perfiles C y Z conformados en frío:
- Método Direct Strength Method (DSM) según AISI S100-16/22 (§E3, §F3)
- Método de Ancho Eficaz (EWM) con rigidizador elástico según EN 1993-1-3:2006 (§5.5.3)
- Separación normativa estricta entre AISI S100 y Eurocódigo
- Verificación de límites de aplicabilidad geométrica (h/t, b/t, lip/t, lip/b)
- Benchmark analítico de referencia para perfiles C y Z representativos
"""
from __future__ import annotations

import math
import pytest

from coldformed.distortional import (
    SectionGeometryCZ,
    DistortionalResultAISI,
    DistortionalResultEC3,
    aisi_distortional_buckling,
    ec3_distortional_buckling,
    check_aisi_dsm_applicability,
    check_ec3_applicability,
)
from coldformed.codes_multi import design_capacity_cz, code_description


# ---------------------------------------------------------------------------
# Geometrías Representativas de Benchmark
# ---------------------------------------------------------------------------

@pytest.fixture
def lipped_channel_c200() -> SectionGeometryCZ:
    """Perfil C representativo: C200x80x25x2.0 (S350GD)."""
    return SectionGeometryCZ(h_mm=200.0, b_mm=80.0, lip_mm=25.0, t_mm=2.0, shape="C")


@pytest.fixture
def lipped_z_section_z200() -> SectionGeometryCZ:
    """Perfil Z representativo: Z200x65x20x2.5 (S350GD)."""
    return SectionGeometryCZ(h_mm=200.0, b_mm=65.0, lip_mm=20.0, t_mm=2.5, shape="Z")


# ---------------------------------------------------------------------------
# 1. Tests AISI S100 Direct Strength Method (DSM)
# ---------------------------------------------------------------------------

def test_aisi_dsm_lipped_channel_compression(lipped_channel_c200: SectionGeometryCZ):
    """Verifica el pandeo distorsional en compresión según AISI S100 §E3."""
    res = aisi_distortional_buckling(lipped_channel_c200, Fy_MPa=350.0)

    assert res.standard == "AISI S100-16/22"
    assert res.method == "Direct Strength Method (DSM)"
    assert res.is_valid_dsm is True
    assert res.sigma_crd_MPa > 0.0
    assert res.L_crd_mm > 0.0

    # Carga de fluencia Py = Ag * Fy
    Ag = (200.0 + 2 * 80.0 + 2 * 25.0) * 2.0  # 820 mm²
    expected_Py = Ag * 350.0 / 1000.0         # 287.0 kN
    assert res.Py_kN == pytest.approx(expected_Py, rel=1e-2)

    # La resistencia distorsional Pnd debe ser menor o igual que Py
    assert res.Pnd_kN <= res.Py_kN
    # Factor LRFD φc = 0.85
    assert res.phi_c_Pn_kN == pytest.approx(res.Pnd_kN * 0.85, rel=1e-3)


def test_aisi_dsm_lipped_channel_flexure(lipped_channel_c200: SectionGeometryCZ):
    """Verifica el pandeo distorsional en flexión según AISI S100 §F3."""
    res = aisi_distortional_buckling(lipped_channel_c200, Fy_MPa=350.0)

    assert res.My_kNm > 0.0
    assert res.Mcrd_kNm > 0.0
    assert res.Mnd_kNm <= res.My_kNm
    # Factor LRFD φb = 0.90
    assert res.phi_b_Mn_kNm == pytest.approx(res.Mnd_kNm * 0.90, rel=1e-3)


def test_aisi_dsm_z_section(lipped_z_section_z200: SectionGeometryCZ):
    """Verifica el cálculo DSM para perfil Z."""
    res = aisi_distortional_buckling(lipped_z_section_z200, Fy_MPa=350.0)
    assert res.is_valid_dsm is True
    assert res.sigma_crd_MPa > 0.0
    assert res.Pnd_kN > 0.0
    assert res.Mnd_kNm > 0.0


# ---------------------------------------------------------------------------
# 2. Tests EN 1993-1-3 §5.5.3 (Rigidizador de Borde con Muelle Elástico)
# ---------------------------------------------------------------------------

def test_ec3_distortional_compression(lipped_channel_c200: SectionGeometryCZ):
    """Verifica el pandeo distorsional del rigidizador según EN 1993-1-3 §5.5.3 en compresión."""
    res = ec3_distortional_buckling(lipped_channel_c200, fyb_MPa=350.0, loading="compression")

    assert res.standard == "EN 1993-1-3:2006"
    assert "EWM §5.5.3" in res.method
    assert res.is_valid_ec3 is True
    assert res.K_spring_N_per_mm2 > 0.0
    assert res.sigma_cr_s_MPa > 0.0
    assert res.lambda_bar_d > 0.0

    # Reducción distorsional 0 < χ_d <= 1.0
    assert 0.0 < res.chi_d <= 1.0
    assert res.t_red_mm <= lipped_channel_c200.t_mm
    assert res.As_red_mm2 <= res.As_eff_mm2
    assert res.Nc_Rd_kN > 0.0


def test_ec3_distortional_bending(lipped_channel_c200: SectionGeometryCZ):
    """Verifica el pandeo distorsional según EN 1993-1-3 en flexión."""
    res = ec3_distortional_buckling(lipped_channel_c200, fyb_MPa=350.0, loading="bending")

    # En flexión, la rigidez del muelle K es mayor debido al anclaje del ala traccionada
    res_comp = ec3_distortional_buckling(lipped_channel_c200, fyb_MPa=350.0, loading="compression")
    assert res.K_spring_N_per_mm2 > res_comp.K_spring_N_per_mm2
    assert res.sigma_cr_s_MPa >= res_comp.sigma_cr_s_MPa
    assert res.Mc_Rd_kNm > 0.0


# ---------------------------------------------------------------------------
# 3. Límites de Aplicabilidad Geométrica
# ---------------------------------------------------------------------------

def test_applicability_limits_detection():
    """Detecta violaciones de límites normativos y alerta sin crash."""
    # Perfil con alma excesivamente esbelta (h/t = 250 > límite AISI de 200)
    slender_web = SectionGeometryCZ(h_mm=500.0, b_mm=80.0, lip_mm=25.0, t_mm=2.0)
    is_valid_aisi, notes_aisi = check_aisi_dsm_applicability(slender_web, Fy_MPa=350.0)
    assert is_valid_aisi is False
    assert any("h/t" in n for n in notes_aisi)

    # Perfil sin labio (lip = 0)
    unlipped = SectionGeometryCZ(h_mm=200.0, b_mm=80.0, lip_mm=0.0, t_mm=2.0)
    is_valid_aisi_unl, notes_unl = check_aisi_dsm_applicability(unlipped, Fy_MPa=350.0)
    assert is_valid_aisi_unl is False
    assert any("lip <= 0" in n for n in notes_unl)

    is_valid_ec, notes_ec = check_ec3_applicability(unlipped, fyb_MPa=350.0)
    assert is_valid_ec is False
    assert any("c <= 0" in n for n in notes_ec)


# ---------------------------------------------------------------------------
# 4. Separación Normativa en la API Multi-Código
# ---------------------------------------------------------------------------

def test_normative_segregation_api(lipped_channel_c200: SectionGeometryCZ):
    """Garantiza que design_capacity_cz nunca confunde DSM con Eurocódigo."""
    # US / AISI
    us_res = design_capacity_cz("US", lipped_channel_c200, Fy_MPa=350.0, loading="compression")
    assert us_res["standard"] == "AISI S100-16/22"
    assert "Direct Strength Method" in us_res["method"]
    assert us_res["unit"] == "kN"

    # EU / Eurocódigo
    eu_res = design_capacity_cz("EU", lipped_channel_c200, Fy_MPa=350.0, loading="compression")
    assert eu_res["standard"] == "EN 1993-1-3:2006"
    assert "Effective Width Method" in eu_res["method"]
    assert eu_res["unit"] == "kN"

    # Ambos métodos arrojan capacidades físicas de magnitudes comparables pero formulaciones distintas
    assert us_res["design_capacity"] > 50.0
    assert eu_res["design_capacity"] > 50.0
    # No son idénticos porque DSM y EWM tienen derivaciones diferentes
    assert us_res["design_capacity"] != pytest.approx(eu_res["design_capacity"], rel=1e-4)


def test_code_descriptions():
    assert "AISI" in code_description("US")
    assert "EN 1993-1-3" in code_description("EU")
    assert "AS/NZS 4600" in code_description("AU")
