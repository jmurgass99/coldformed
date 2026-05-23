# -*- coding: utf-8 -*-
"""Ecuaciones de interaccion (AISI S100-16 §H1).

  - Flexion + cortante (§H1.1):  (M/Mn_phi)^2 + (V/Vn_phi)^2 <= 1.0
  - Axial + flexion (§H1.2):     P/Pn_phi + Mx/Mnx_phi + My/Mny_phi <= 1.0

Las capacidades de diseño (con phi/gamma) las provee el llamador (p.ej. de
direct_strength.py). Devuelve el ratio de demanda/capacidad: <=1.0 = OK.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionResult:
    ratio: float
    ok: bool
    equation: str


def bending_shear(M_demand: float, M_cap: float, V_demand: float, V_cap: float) -> InteractionResult:
    """Interaccion flexion-cortante AISI §H1.1 (circular)."""
    r = (M_demand / M_cap) ** 2 + (V_demand / V_cap) ** 2
    r = r ** 0.5
    return InteractionResult(ratio=r, ok=r <= 1.0 + 1e-9, equation="H1.1 (M-V)")


def axial_bending(P_demand: float, P_cap: float,
                  Mx_demand: float, Mx_cap: float,
                  My_demand: float = 0.0, My_cap: float = 1.0) -> InteractionResult:
    """Interaccion axial-flexion AISI §H1.2 (lineal, lado seguro)."""
    r = P_demand / P_cap + Mx_demand / Mx_cap + (My_demand / My_cap if My_cap else 0.0)
    return InteractionResult(ratio=r, ok=r <= 1.0 + 1e-9, equation="H1.2 (P-M)")


__all__ = ["InteractionResult", "bending_shear", "axial_bending"]
