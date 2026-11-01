# -*- coding: utf-8 -*-
"""Resistencia a cortante de almas — AISI S100-16 §G2 y EN 1993-1-3 §6.1.5.

Incluye:
1. ``shear_capacity(inp)`` — AISI S100-16 §G2.1: ``Vn = Aw · Fv`` con tres
   regímenes (fluencia, pandeo inelástico y pandeo elástico de cortante,
   ``kv = 5.34``, quiebres ``0.815 / 1.227``, ``E = 203000 MPa``).
2. ``shear_capacity_ec3(inp)`` — EN 1993-1-3:2006 §6.1.5 (Ec. 6.8, 6.10a y
   Tabla 6.1): ``V_b,Rd = (h_w / sin(phi)) · t · f_bv / gamma_M0``, con
   esbeltez relativa del alma ``lambda_w = 0.346 · (s_w / t) · sqrt(f_yb / E)``
   y resistencia de pandeo por cortante ``f_bv`` según Tabla 6.1 (con o sin
   rigidización en el apoyo).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .exceptions import ValidationError

_E = 203000.0   # MPa (acero conformado AISI)
_E_EC3 = 210000.0  # MPa (EN 1993-1-3)
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


@dataclass(frozen=True)
class EC3ShearInput:
    """Datos de entrada para resistencia a cortante según EN 1993-1-3 §6.1.5."""
    hw_mm: float                         # altura del alma entre líneas medias de las alas [mm]
    t_mm: float                          # espesor neto de cálculo del núcleo [mm]
    fyb_MPa: float                       # límite elástico básico f_yb [MPa]
    phi_deg: float = 90.0                # inclinación del alma respecto a las alas (grados, 0 < phi <= 90)
    stiffened_at_support: bool = False   # True si hay rigidizador en el apoyo que impide distorsión del alma
    E_MPa: float = _E_EC3
    gamma_M0: float = 1.00


@dataclass(frozen=True)
class EC3ShearResult:
    """Resultado de resistencia a cortante EN 1993-1-3 §6.1.5."""
    Vb_Rd_kN: float       # resistencia de cálculo a abolladura por cortante [kN]
    Vpl_Rd_kN: float      # resistencia plástica a cortante de referencia [kN]
    fbv_MPa: float        # tensión de abolladura por cortante (Tabla 6.1) [MPa]
    lambda_w: float       # esbeltez relativa del alma (Ec. 6.10a)
    sw_mm: float          # longitud inclinada del alma s_w = h_w / sin(phi) [mm]
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


def shear_capacity_ec3(inp: EC3ShearInput) -> EC3ShearResult:
    """Resistencia de cálculo a cortante V_b,Rd según EN 1993-1-3:2006 §6.1.5.

    Ecuaciones implementadas:
    - ``s_w = h_w / sin(phi)``
    - ``lambda_w = 0.346 * (s_w / t) * sqrt(f_yb / E)`` (Ec. 6.10a, alma sin rigidizadores longitudinales)
    - Tabla 6.1:
      * ``lambda_w <= 0.83``         : ``f_bv = 0.58 * f_yb``
      * ``0.83 < lambda_w < 1.40``   : ``f_bv = 0.48 * f_yb / lambda_w``
      * ``lambda_w >= 1.40`` (sin rigidizador en apoyo): ``f_bv = 0.67 * f_yb / lambda_w^2``
      * ``lambda_w >= 1.40`` (con rigidizador en apoyo): ``f_bv = 0.48 * f_yb / lambda_w``
    - ``V_b,Rd = ((h_w / sin(phi)) * t * f_bv) / gamma_M0`` (Ec. 6.8)
    """
    if inp.hw_mm <= 0 or inp.t_mm <= 0 or inp.fyb_MPa <= 0 or inp.E_MPa <= 0 or inp.gamma_M0 <= 0:
        raise ValidationError("hw_mm, t_mm, fyb_MPa, E_MPa y gamma_M0 deben ser > 0")
    if not (0.0 < inp.phi_deg <= 90.0):
        raise ValidationError("phi_deg debe estar en (0, 90]")

    sin_phi = math.sin(math.radians(inp.phi_deg))
    sw = inp.hw_mm / sin_phi
    lam_w = 0.346 * (sw / inp.t_mm) * math.sqrt(inp.fyb_MPa / inp.E_MPa)

    if lam_w <= 0.83:
        fbv = 0.58 * inp.fyb_MPa
        regime = "fluencia por cortante (lambda_w <= 0.83)"
    elif lam_w < 1.40:
        fbv = 0.48 * inp.fyb_MPa / lam_w
        regime = "abolladura inelastica (0.83 < lambda_w < 1.40)"
    else:
        if inp.stiffened_at_support:
            fbv = 0.48 * inp.fyb_MPa / lam_w
            regime = "abolladura con rigidizador en apoyo (lambda_w >= 1.40)"
        else:
            fbv = 0.67 * inp.fyb_MPa / (lam_w ** 2)
            regime = "abolladura elastica sin rigidizador en apoyo (lambda_w >= 1.40)"

    Vb_Rd_kN = (sw * inp.t_mm * fbv) / (inp.gamma_M0 * 1.0e3)
    Vpl_Rd_kN = (sw * inp.t_mm * (inp.fyb_MPa / math.sqrt(3.0))) / (inp.gamma_M0 * 1.0e3)
    return EC3ShearResult(
        Vb_Rd_kN=Vb_Rd_kN,
        Vpl_Rd_kN=Vpl_Rd_kN,
        fbv_MPa=fbv,
        lambda_w=lam_w,
        sw_mm=sw,
        regime=regime,
    )


__all__ = [
    "ShearInput",
    "ShearResult",
    "shear_capacity",
    "EC3ShearInput",
    "EC3ShearResult",
    "shear_capacity_ec3",
]
