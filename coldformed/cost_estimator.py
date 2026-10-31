"""
cost_estimator.py — Generador de costos por perfil conformado en frío.

Tabla de precios USD/ton estimativa Q2-2025 para perfiles cold-formed
(C, Z, Σ, U, omega) basados en cotizaciones de planta laminadora.
Multi-código: cubre CL (Chile), CO (Colombia), US, EU, AU, SG, NSR10.
"""
from __future__ import annotations

from dataclasses import dataclass


# USD/ton para chapa galvanizada calidad estructural
# (perfil terminado, recargo respecto a chapa plana ~25-40%).
USD_TON_BASE: dict[str, float] = {
    "CL": 1850.0,
    "CO": 1900.0,
    "US": 1550.0,
    "EU": 1700.0,
    "AU": 2050.0,
    "SG": 1750.0,
    "NSR10": 1900.0,
    "DEFAULT": 1800.0,
}

# Recargo por proceso de conformado (fracción)
FORMING_SURCHARGE: dict[str, float] = {
    "C": 0.25,
    "Z": 0.30,
    "Sigma": 0.35,
    "Omega": 0.30,
    "U": 0.20,
    "Hat": 0.35,
}


@dataclass(frozen=True)
class CostInput:
    profile_type: str
    weight_per_m_kg: float
    length_m: float
    country: str = "DEFAULT"
    quantity: int = 1
    galvanized: bool = True


def cost_estimate(inp: CostInput) -> dict:
    """
    Devuelve el costo USD para un pedido de perfiles.

    Total = base_usd_ton * (1 + forming_surcharge) * peso_total/1000
            * (1 + 0.05 si galvanizado).
    """
    if inp.weight_per_m_kg <= 0:
        raise ValueError("weight_per_m_kg debe ser > 0")
    if inp.length_m <= 0:
        raise ValueError("length_m debe ser > 0")
    if inp.quantity <= 0:
        raise ValueError("quantity debe ser >= 1")

    base = USD_TON_BASE.get(inp.country.upper(), USD_TON_BASE["DEFAULT"])
    surch = FORMING_SURCHARGE.get(inp.profile_type, 0.25)
    galv = 0.05 if inp.galvanized else 0.0
    total_kg = inp.weight_per_m_kg * inp.length_m * inp.quantity
    usd_per_ton = base * (1.0 + surch) * (1.0 + galv)
    total_usd = usd_per_ton * total_kg / 1000.0
    return {
        "country": inp.country,
        "profile_type": inp.profile_type,
        "quantity": inp.quantity,
        "total_weight_kg": round(total_kg, 2),
        "usd_per_ton_effective": round(usd_per_ton, 2),
        "total_USD": round(total_usd, 2),
        "USD_per_kg": round(usd_per_ton / 1000.0, 3),
    }


def co2_estimate(weight_kg: float, country: str = "DEFAULT") -> float:
    """
    Emisiones CO2 [t] para acero cold-formed.
    Coeficiente típico 2.0 t CO2/t para chapa primaria.
    """
    factor_tco2_per_ton = {
        "EU": 1.6,
        "US": 1.8,
        "CL": 2.2,
        "CO": 2.2,
        "AU": 1.9,
        "SG": 1.8,
        "NSR10": 2.2,
        "DEFAULT": 2.0,
    }
    f = factor_tco2_per_ton.get(country.upper(), 2.0)
    return round(f * weight_kg / 1000.0, 4)


__all__ = ["CostInput", "cost_estimate", "co2_estimate",
           "USD_TON_BASE", "FORMING_SURCHARGE"]
