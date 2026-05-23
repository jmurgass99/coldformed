"""
Wrappers Cold-Formed multi-código.

AISI S100-22 (US/CO):    DSM ya en `direct_strength.py` (factor φ=0.90 flexión)
AS/NZS 4600 (AU):        DSM idéntico AISI con φ=0.90
EN 1993-1-3 (EU/SG):     Effective Width Method (EWM) ya en `fsm.py`/`memos`

Este módulo da una API uniforme `design_capacity(code, mode, ...)`.
"""
from __future__ import annotations

from typing import Any, Literal


def design_resistance_flexure(
    code: Literal["US", "CO", "AU", "EU", "SG"],
    Mn_kNm: float,
) -> float:
    """Aplica el factor de resistencia/seguridad por código a la
    resistencia nominal de flexión.

    US / CO (AISI S100-22 / NSR-10 §F.4):   φ = 0.90 LRFD
    AU (AS/NZS 4600):                       φ = 0.90
    EU / SG (EN 1993-1-3):                  γ_M1 = 1.00 (M_y/γ_M1)
    """
    factors = {"US": 0.90, "CO": 0.90, "AU": 0.90, "EU": 1.0, "SG": 1.0}
    if code not in factors:
        raise ValueError(f"código '{code}' no soportado")
    if code in ("EU", "SG"):
        return Mn_kNm / factors[code]  # γ aplicado a denominador
    return Mn_kNm * factors[code]


def design_resistance_compression(
    code: Literal["US", "CO", "AU", "EU", "SG"],
    Pn_kN: float,
) -> float:
    """Compresión axial.

    US / CO: φc = 0.85 (AISI / NSR-10)
    AU:      φc = 0.85 (AS/NZS 4600)
    EU/SG:   γ_M1 = 1.00
    """
    factors = {"US": 0.85, "CO": 0.85, "AU": 0.85, "EU": 1.0, "SG": 1.0}
    if code not in factors:
        raise ValueError(f"código '{code}' no soportado")
    if code in ("EU", "SG"):
        return Pn_kN / factors[code]
    return Pn_kN * factors[code]


def code_description(code: str) -> str:
    descriptions = {
        "US": "AISI S100-22 Specification for Cold-Formed Steel",
        "CO": "NSR-10 §F.4 (basado en AISI)",
        "AU": "AS/NZS 4600:2018 Cold-formed steel structures",
        "EU": "EN 1993-1-3 Eurocode 3 Part 1-3",
        "SG": "SS EN 1993-1-3 (NA Singapore)",
    }
    return descriptions.get(code, "")


__all__ = [
    "design_resistance_flexure", "design_resistance_compression",
    "code_description",
]
