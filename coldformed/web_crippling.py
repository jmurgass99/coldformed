# -*- coding: utf-8 -*-
"""Abolladura del alma por carga concentrada (web crippling) — AISI S100-16 §G5.

Pn = C t^2 Fy sin(theta) (1 - C_R sqrt(R/t)) (1 + C_N sqrt(N/t)) (1 - C_h sqrt(h/t))

con coeficientes C, C_R, C_N, C_h de las Tablas G5-1..G5-5 segun: condicion de
apoyo (un ala / dos alas), posicion (extremo / interior), alas rigidizadas o no, y
si esta sujeto al apoyo. theta = angulo alma-superficie de apoyo (90 deg habitual).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .exceptions import ValidationError

PHI_WC = 0.75  # factor de resistencia LRFD (web crippling)


@dataclass(frozen=True)
class WebCripplingCoeffs:
    C: float
    CR: float
    CN: float
    Ch: float
    label: str = ""


# Conjuntos representativos (AISI S100-16 Tabla G5-1, perfil de alma simple,
# alas rigidizadas/parcialmente rigidizadas).
COEFF_SETS = {
    "stiffened_end_one_flange":      WebCripplingCoeffs(4.0, 0.14, 0.35, 0.02, "EOF rigidizada"),
    "stiffened_interior_one_flange": WebCripplingCoeffs(13.0, 0.23, 0.14, 0.01, "IOF rigidizada"),
    "stiffened_end_two_flange":      WebCripplingCoeffs(7.5, 0.08, 0.12, 0.048, "ETF rigidizada"),
    "stiffened_interior_two_flange": WebCripplingCoeffs(20.0, 0.10, 0.08, 0.031, "ITF rigidizada"),
    "unstiffened_end_one_flange":    WebCripplingCoeffs(4.0, 0.14, 0.35, 0.02, "EOF no rigidizada"),
}


@dataclass(frozen=True)
class WebCripplingResult:
    Pn_kN: float        # resistencia nominal
    Pn_design_kN: float  # phi*Pn (LRFD)
    coeffs: str


def web_crippling_strength(t_mm: float, Fy_MPa: float, R_mm: float, N_mm: float,
                           h_mm: float, case: str = "stiffened_interior_one_flange",
                           theta_deg: float = 90.0) -> WebCripplingResult:
    """Resistencia a abolladura del alma por carga concentrada (AISI §G5)."""
    if min(t_mm, Fy_MPa, N_mm, h_mm) <= 0 or R_mm < 0:
        raise ValidationError("t, Fy, N, h deben ser > 0 y R >= 0")
    if case not in COEFF_SETS:
        raise ValidationError("caso desconocido: %s (validos: %s)" % (case, sorted(COEFF_SETS)))
    c = COEFF_SETS[case]
    theta = math.radians(theta_deg)
    Pn_N = (c.C * t_mm ** 2 * Fy_MPa * math.sin(theta)
            * (1 - c.CR * math.sqrt(R_mm / t_mm))
            * (1 + c.CN * math.sqrt(N_mm / t_mm))
            * (1 - c.Ch * math.sqrt(h_mm / t_mm)))
    Pn_N = max(Pn_N, 0.0)
    return WebCripplingResult(Pn_kN=Pn_N / 1e3, Pn_design_kN=PHI_WC * Pn_N / 1e3, coeffs=c.label)


__all__ = ["WebCripplingCoeffs", "COEFF_SETS", "WebCripplingResult",
           "web_crippling_strength", "PHI_WC"]
