# -*- coding: utf-8 -*-
"""Torsion de secciones abiertas de pared delgada (perfiles conformados en frio).

Para perfiles abiertos (C, Z, U, sombrero) la rigidez torsional es esencialmente
de Saint-Venant mas alabeo (warping). Aqui:
  - J = (1/3) Σ b_i t_i^3   (constante de torsion uniforme, rectangulos delgados)
  - tau_sv = T t_max / J     (cortante de Saint-Venant, maximo en el elemento mas grueso)
  - Cw del canal (warping) por formula cerrada para verificar torsion no uniforme.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


def torsion_constant_J(elements: List[Tuple[float, float]]) -> float:
    """J = (1/3) Σ b·t^3 (mm^4). elements = [(longitud_mm, espesor_mm), ...]."""
    return sum(b * t ** 3 for b, t in elements) / 3.0


def st_venant_shear_stress(T_Nmm: float, t_max_mm: float, J_mm4: float) -> float:
    """Cortante de Saint-Venant maximo: tau = T·t_max / J (MPa)."""
    if J_mm4 <= 0:
        raise ValueError("J debe ser > 0")
    return T_Nmm * t_max_mm / J_mm4


def warping_constant_channel(h_mm: float, b_mm: float, t_mm: float) -> float:
    """Constante de alabeo Cw de un canal (mm^6), formula clasica.

    Cw = (t·h^2·b^3 / 12) · (2·h + 3·b)/(h + 6·b)  (aprox. para canal de pared delgada,
    h = altura entre ejes de alas, b = ancho de ala).
    """
    return (t_mm * h_mm ** 2 * b_mm ** 3 / 12.0) * (2 * h_mm + 3 * b_mm) / (h_mm + 6 * b_mm)


@dataclass(frozen=True)
class TorsionResult:
    J_mm4: float
    tau_MPa: float
    ok: bool


def torsion_check(elements: List[Tuple[float, float]], T_Nmm: float, t_max_mm: float,
                  Fy_MPa: float, gamma: float = 0.6) -> TorsionResult:
    """Verifica el cortante de torsion frente a 0.6·Fy (plastificacion por cortante)."""
    J = torsion_constant_J(elements)
    tau = st_venant_shear_stress(T_Nmm, t_max_mm, J)
    return TorsionResult(J_mm4=J, tau_MPa=tau, ok=tau <= gamma * Fy_MPa)


__all__ = ["torsion_constant_J", "st_venant_shear_stress", "warping_constant_channel",
           "TorsionResult", "torsion_check"]
