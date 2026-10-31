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
        "US": "AISI S100-22 Specification for Cold-Formed Steel (DSM)",
        "CO": "NSR-10 §F.4 (basado en AISI DSM)",
        "AU": "AS/NZS 4600:2018 Cold-formed steel structures (DSM)",
        "EU": "EN 1993-1-3:2006 Eurocode 3 Part 1-3 (EWM)",
        "SG": "SS EN 1993-1-3 (NA Singapore EWM)",
    }
    return descriptions.get(code, "")


def design_capacity_cz(
    code: Literal["US", "CO", "AU", "EU", "SG"],
    sec: Any,
    Fy_MPa: float = 350.0,
    loading: Literal["compression", "bending"] = "compression",
) -> dict[str, Any]:
    """Cálculo normativamente segregado de capacidad de secciones C y Z conformadas en frío.

    Garantiza que:
    - US / CO / AU aplican AISI S100-22 / NSR-10 / AS/NZS 4600 Direct Strength Method (DSM).
    - EU / SG aplican EN 1993-1-3:2006 / SS EN 1993-1-3 Effective Width Method (§5.5.3 Rigidizador de borde).
    - No se asume que DSM de AISI sea el método normativo de Eurocódigo.
    """
    from .distortional import aisi_distortional_buckling, ec3_distortional_buckling

    if code in ("US", "CO", "AU"):
        res = aisi_distortional_buckling(sec, Fy_MPa=Fy_MPa)
        if loading == "compression":
            cap = res.phi_c_Pn_kN
            nom = res.Pnd_kN
            unit = "kN"
        else:
            cap = res.phi_b_Mn_kNm
            nom = res.Mnd_kNm
            unit = "kN·m"
        return {
            "code": code,
            "standard": res.standard,
            "method": res.method,
            "loading": loading,
            "unit": unit,
            "nominal_capacity": nom,
            "design_capacity": cap,
            "is_valid": res.is_valid_dsm,
            "validity_notes": res.validity_notes,
            "raw_result": res.to_dict(),
        }
    elif code in ("EU", "SG"):
        res_ec = ec3_distortional_buckling(sec, fyb_MPa=Fy_MPa, loading=loading)
        if loading == "compression":
            cap = res_ec.Nc_Rd_kN
            unit = "kN"
        else:
            cap = res_ec.Mc_Rd_kNm
            unit = "kN·m"
        return {
            "code": code,
            "standard": res_ec.standard,
            "method": res_ec.method,
            "loading": loading,
            "unit": unit,
            "nominal_capacity": cap,
            "design_capacity": cap,
            "is_valid": res_ec.is_valid_ec3,
            "validity_notes": res_ec.validity_notes,
            "raw_result": res_ec.to_dict(),
        }
    else:
        raise ValueError(f"código '{code}' no soportado")


__all__ = [
    "design_resistance_flexure",
    "design_resistance_compression",
    "code_description",
    "design_capacity_cz",
]

