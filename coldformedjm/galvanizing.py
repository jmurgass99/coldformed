"""
Pérdida de capacidad por galvanizado en caliente.

EN 1461 (galvanizado) reduce Fy por embrittlement térmico ~3-5%.
AISI especifica Fy efectivo = Fy_base · 0.95 para H-gal.
"""
from __future__ import annotations


def adjusted_yield(Fy_MPa: float, process: str = "hot_dip_galvanized") -> float:
    """Devuelve Fy ajustado por proceso superficial."""
    factors = {
        "hot_dip_galvanized": 0.95,
        "electrogalvanized":  0.98,
        "painted":            1.00,
        "aluminized":         0.97,
        "duplex":             0.94,
    }
    if process not in factors:
        raise ValueError(f"proceso '{process}' no soportado")
    return Fy_MPa * factors[process]


def coating_thickness_required_iso1461(t_mm: float) -> int:
    """Espesor mínimo de recubrimiento Zn (μm) según EN ISO 1461 Tabla 3."""
    if t_mm < 1.5:
        return 45
    if t_mm < 3.0:
        return 55
    if t_mm < 6.0:
        return 70
    return 85


__all__ = ["adjusted_yield", "coating_thickness_required_iso1461"]
