# -*- coding: utf-8 -*-
"""Resistencia a cortante de almas (AISI S100-16 §G2 / EN 1993-1-3 §6.1.5).

Vn = Aw·Fv, con Fv segun la esbeltez de cortante del alma. Tres regimenes:
fluencia, pandeo inelastico y pandeo elastico de cortante.
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
