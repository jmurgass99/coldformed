"""
Catálogo de perfiles cold-formed estándar — AISI + EN 1993-1-3.

Perfiles típicos C, Z y Σ con dimensiones canónicas. Permite lookup por
nombre y construir un `CFShape` listo para `sap_section_bridge`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CFProfile:
    name: str
    standard: str           # 'AISI' | 'EN 1993-1-3'
    shape: str              # 'C' | 'Z' | 'Sigma'
    h_mm: float
    b_mm: float
    lip_mm: float
    t_mm: float
    mass_kg_per_m: float


_CATALOG: list[CFProfile] = [
    # AISI canónicos
    CFProfile("AISI C8x2.5",   "AISI", "C", 203.2, 63.5, 12.7, 2.0, 3.92),
    CFProfile("AISI C10x2.5",  "AISI", "C", 254.0, 63.5, 12.7, 2.5, 5.16),
    CFProfile("AISI C12x3",    "AISI", "C", 304.8, 76.2, 19.0, 3.0, 7.24),
    CFProfile("AISI Z8x2.5",   "AISI", "Z", 203.2, 63.5, 12.7, 2.0, 3.92),
    CFProfile("AISI Z10x3",    "AISI", "Z", 254.0, 76.2, 19.0, 3.0, 5.85),
    # EN 1993-1-3 (Sigma)
    CFProfile("EN Σ200x80x25", "EN 1993-1-3", "Sigma", 200, 80, 25, 2.5, 6.18),
    CFProfile("EN Σ250x80x30", "EN 1993-1-3", "Sigma", 250, 80, 30, 3.0, 8.39),
    CFProfile("EN Σ300x90x30", "EN 1993-1-3", "Sigma", 300, 90, 30, 3.5, 11.50),
    # C europeos
    CFProfile("EN C200x80x25", "EN 1993-1-3", "C", 200, 80, 25, 2.0, 5.50),
    CFProfile("EN C250x80x25", "EN 1993-1-3", "C", 250, 80, 25, 2.5, 7.85),
]


def lookup(name: str) -> CFProfile | None:
    for p in _CATALOG:
        if p.name == name:
            return p
    return None


def list_profiles(shape: str | None = None,
                   standard: str | None = None) -> list[CFProfile]:
    out = list(_CATALOG)
    if shape:
        out = [p for p in out if p.shape == shape]
    if standard:
        out = [p for p in out if p.standard == standard]
    return out


def to_cf_shape(profile_name: str):
    """Construye un `CFShape` a partir de un perfil del catálogo."""
    p = lookup(profile_name)
    if p is None:
        raise KeyError(f"Perfil '{profile_name}' no existe")
    from .sap_section_bridge import channel, sigma_section, z_section
    if p.shape == "C":
        return channel(h=p.h_mm, b=p.b_mm, t=p.t_mm, name=p.name)
    if p.shape == "Z":
        return z_section(h=p.h_mm, b_top=p.b_mm, b_bot=p.b_mm, t=p.t_mm, name=p.name)
    return sigma_section(h=p.h_mm, b=p.b_mm, lip=p.lip_mm, t=p.t_mm, name=p.name)


__all__ = ["CFProfile", "lookup", "list_profiles", "to_cf_shape"]
