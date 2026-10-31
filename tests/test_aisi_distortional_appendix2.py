"""Pandeo distorsional AISI S100-16 Apéndice 2 — anclaje por sustitución a mano y consistencia.

No hay en el corpus de fichas un ejemplo resuelto con σ_crd numérico, así que el
oráculo es la sustitución a mano de las ecuaciones §2.3.1.3 (compresión) para la
sección C 200x60x20x2 (S350), hecha ANTES de ejecutar el código:

  línea media: b = 58, d = 19, t = 2, h_o = 200; G = 80 769 MPa
  A_f = 154 mm²; J_f = 205,3 mm⁴
  I_xf = 2·(4·58² + 4·58·19³ + 4·58·19 + 19⁴)/(12·77) = 3 765 mm⁴
  I_yf = 2·(58⁴ + 4·19·58³)/(12·77) = 56 591 mm⁴
  I_xyf = 2·58²·19²/(4·77) = 7 886 mm⁴
  x_o − h_x = b = 58 ; y_o = −2,344 ; h_x = −36,16
  núcleo = I_xf·b² − (I_xyf²/I_yf)·b² = 12 665 460 − 3 696 700 = 8 968 760 mm⁶
  L_cr = [6π⁴·200·0,91/8 · 8 968 760]^(1/4) = (1,1925·10¹¹)^(1/4) = 587,6 mm
  k_φfe = (π/L)⁴·E·núcleo + (π/L)²·G·J_f = 1 535 + 473 = 2 008 N
  k_φwe = E·t³/(6·h_o·0,91) = 1 538 N
  k̃_φfg = (π/L)²·[A_f·(65,3 + 37,9 + 1 307,5 + 5,5) + I_xf + I_yf] = 7,95 mm²
  k̃_φwg = (π/L)²·t·h_o³/60 = 7,61 mm²
  σ_crd = (2 008 + 1 538)/(7,95 + 7,61) = 228 MPa

Comprobaciones de consistencia añadidas: la L_cr cerrada es el mínimo de F_crd(L)
evaluada numéricamente con las mismas rigideces (eso valida que k̃_φwg y la
expresión de L_cr se corresponden); σ_crd crece con el labio y cae sin él; un
arriostramiento L_m < L_cr sube σ_crd; y la guarda de regresión contra la versión
anterior (σ_crd ≈ 2,7·10⁶ MPa).
"""
from __future__ import annotations

import math

import pytest

from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling

SEC = SectionGeometryCZ(h_mm=200.0, b_mm=60.0, lip_mm=20.0, t_mm=2.0, shape="C")


def test_hand_substitution_c200x60x20x2_compression():
    r = aisi_distortional_buckling(SEC, Fy_MPa=350.0)
    assert r.L_crd_mm == pytest.approx(587.6, abs=0.5)
    assert r.sigma_crd_MPa == pytest.approx(228.0, abs=1.0)


def test_flexure_critical_stress_exceeds_compression_and_is_plausible():
    r = aisi_distortional_buckling(SEC, Fy_MPa=350.0)
    assert r.sigma_crd_flex_MPa > r.sigma_crd_MPa
    assert 300.0 < r.sigma_crd_flex_MPa < 1000.0
    assert 400.0 < r.L_crd_flex_mm < 700.0


def test_closed_form_L_cr_is_the_numerical_minimum():
    """F_crd(L) con las rigideces del Apéndice 2 tiene su mínimo en la L_cr cerrada."""
    E, nu, t, h_o, b, d = 210_000.0, 0.30, 2.0, 200.0, 58.0, 19.0
    G = E / (2 * (1 + nu))
    Af, Jf = (b + d) * t, (b + d) * t ** 3 / 3
    Ixf = t * (t ** 2 * b ** 2 + 4 * b * d ** 3 + t ** 2 * b * d + d ** 4) / (12 * (b + d))
    Iyf = t * (b ** 4 + 4 * d * b ** 3) / (12 * (b + d))
    Ixyf = t * b ** 2 * d ** 2 / (4 * (b + d))
    xo, yo, hx = b ** 2 / (2 * (b + d)), -d ** 2 / (2 * (b + d)), -(b ** 2 + 2 * d * b) / (2 * (b + d))
    core = Ixf * (xo - hx) ** 2 - Ixyf ** 2 / Iyf * (xo - hx) ** 2

    def F(L: float) -> float:
        kfe = (math.pi / L) ** 4 * E * core + (math.pi / L) ** 2 * G * Jf
        kfg = (math.pi / L) ** 2 * (Af * ((xo - hx) ** 2 * (Ixyf / Iyf) ** 2 - 2 * yo * (xo - hx) * (Ixyf / Iyf)
                                          + hx ** 2 + yo ** 2) + Ixf + Iyf)
        kwe = E * t ** 3 / (6 * h_o * (1 - nu ** 2))
        kwg = (math.pi / L) ** 2 * t * h_o ** 3 / 60
        return (kfe + kwe) / (kfg + kwg)

    r = aisi_distortional_buckling(SEC, Fy_MPa=350.0)
    L_grid = [r.L_crd_mm * f for f in (0.6, 0.8, 0.9, 1.0, 1.1, 1.25, 1.6)]
    values = [F(L) for L in L_grid]
    assert min(values) == pytest.approx(F(r.L_crd_mm), rel=1e-3)
    assert F(r.L_crd_mm) == pytest.approx(r.sigma_crd_MPa, rel=2e-3)


def test_lip_raises_sigma_crd_and_no_lip_collapses_it():
    s0 = aisi_distortional_buckling(SectionGeometryCZ(200, 60, 0.0, 2.0, "C"), 350.0)
    s20 = aisi_distortional_buckling(SEC, 350.0)
    s30 = aisi_distortional_buckling(SectionGeometryCZ(200, 60, 30.0, 2.0, "C"), 350.0)
    assert s0.sigma_crd_MPa < 0.3 * s20.sigma_crd_MPa
    assert s30.sigma_crd_MPa > s20.sigma_crd_MPa


def test_bracing_shorter_than_L_cr_raises_sigma_crd():
    free = aisi_distortional_buckling(SEC, 350.0)
    braced = aisi_distortional_buckling(SEC, 350.0, L_m_mm=300.0)
    assert braced.L_crd_mm == pytest.approx(300.0)
    assert braced.sigma_crd_MPa > free.sigma_crd_MPa


def test_regression_guard_against_dimensionally_wrong_version():
    r = aisi_distortional_buckling(SEC, 350.0)
    assert r.sigma_crd_MPa < 10.0 * 350.0
    assert r.lambda_d_c > 0.5          # antes: 0,011 → P_nd = P_y siempre
    assert r.Pnd_kN < r.Py_kN
