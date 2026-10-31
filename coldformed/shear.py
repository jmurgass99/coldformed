# -*- coding: utf-8 -*-
"""Resistencia a cortante de almas — AISI S100-16 §G2 UNICAMENTE.

Vn = Aw·Fv, con Fv segun la esbeltez de cortante del alma. Tres regimenes:
fluencia, pandeo inelastico y pandeo elastico de cortante (kv=5.34, quiebres
0.815/1.227, E=203000 MPa — todos coeficientes AISI).

NOTA DE ALCANCE (correccion de docstring): la version anterior decia tambien
"EN 1993-1-3 §6.1.5", pero aqui NO hay ninguna formula de esa norma — ni la
esbeltez lambda_w = 0.346·(s_w/t)·sqrt(f_yb/E) ni la tabla de f_bv del EC3.
Quien necesite V_b,Rd segun EC3-1-3 no puede usar este modulo tal cual: la
rama EC3 esta SIN implementar (gap declarado por la campana de goldens; ver
tests/test_ec3_1_3_effective_width_goldens.py, seccion de insatisfacibles).
Etiquetar como existente lo que no existe es el patron de "capacidad aparente"
que esta campana persigue.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .exceptions import ValidationError

_E = 203000.0   # MPa (acero conformado)
_NU = 0.30


@dataclass(frozen=True)
class ShearInput:
    h_mm: float          # altura plana del alma
    t_mm: float          # espesor
    Fy_MPa: float
    kv: float = 5.34     # coef. de pandeo (alma no rigidizada)


@dataclass(frozen=True)
class ShearResult:
    Vn_kN: float          # resistencia nominal
    Vy_kN: float          # fluencia (0.6·Fy·Aw)
    Vcr_kN: float         # pandeo elastico
    lambda_v: float
    regime: str


def shear_capacity(inp: ShearInput) -> ShearResult:
    """Vn segun AISI S100-16 §G2.1 (almas sin rigidizar)."""
    if inp.h_mm <= 0 or inp.t_mm <= 0 or inp.Fy_MPa <= 0:
        raise ValidationError("h, t, Fy deben ser > 0")
    Aw = inp.h_mm * inp.t_mm
    Vy = 0.6 * inp.Fy_MPa * Aw / 1.0e3  # kN
    Fcr = math.pi ** 2 * inp.kv * _E / (12.0 * (1.0 - _NU ** 2) * (inp.h_mm / inp.t_mm) ** 2)
    Vcr = Fcr * Aw / 1.0e3
    lam = math.sqrt(Vy / Vcr) if Vcr > 0 else float("inf")
    if lam <= 0.815:
        Vn, regime = Vy, "fluencia"
    elif lam <= 1.227:
        Vn, regime = 0.815 * math.sqrt(Vcr * Vy), "pandeo inelastico"
    else:
        Vn, regime = Vcr, "pandeo elastico"
    return ShearResult(Vn_kN=Vn, Vy_kN=Vy, Vcr_kN=Vcr, lambda_v=lam, regime=regime)


__all__ = ["ShearInput", "ShearResult", "shear_capacity"]
