"""
Iteración de propiedades efectivas para perfiles Clase 4 (gotcha #18).

SAP/ETABS resuelve la matriz con propiedades brutas (Gross). Las
deformaciones reales se subestiman porque pandeo local reduce la rigidez
efectiva. Este módulo implementa el loop:

    σ_demand → AISI b_eff → A_eff/I_eff → re-solver → σ' → repeat

hasta convergencia en deformaciones (tolerancia configurable, default 5%).

Diseñado para ser llamado desde un wrapper de fastsap que reasigne los
``Property Modifiers`` vía OAPI tras cada iteración.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class EffectiveIterInput:
    """Args:
        b_gross: ancho bruto del elemento de placa [mm].
        t: espesor [mm].
        sigma_demand_provider: callable(b_eff_ratio) -> sigma_act [MPa].
            La función la inyecta el wrapper SAP — recibe el ratio actual
            de A_eff/A_gross y devuelve la tensión actuante tras re-correr.
        sigma_y: tensión de fluencia [MPa].
        E: módulo de elasticidad [MPa].
        nu: coeficiente Poisson.
        k_plate: factor de placa (4.0 ss-ss).
        tol: tolerancia relativa en el ratio entre iteraciones.
        max_iter: máximo de iteraciones.
    """
    b_gross: float
    t: float
    sigma_demand_provider: Callable[[float], float]
    sigma_y: float = 350.0
    E: float = 210_000.0
    nu: float = 0.30
    k_plate: float = 4.0
    tol: float = 0.05
    max_iter: int = 10


@dataclass(frozen=True)
class EffectiveIterResult:
    iterations: int
    converged: bool
    final_ratio: float          # b_eff / b_gross final
    history: list[float] = field(default_factory=list)


def _b_eff_aisi(b: float, t: float, sigma_act: float, sigma_y: float,
                 E: float, k: float = 4.0, nu: float = 0.30) -> float:
    """AISI / EN 1993-1-5 — ancho efectivo de placa con compresión uniforme.

    ``λ_p = (b/t) / sqrt(σ_cr/σ_act)`` con
    ``σ_cr = k·π²·E / (12·(1-ν²)·(b/t)²)``.

    Si λ_p ≤ 0.673 → b_eff = b. Si > 0.673 → b_eff = ρ·b con
    ``ρ = (λ_p - 0.22) / λ_p²``.
    """
    if sigma_act <= 0 or b <= 0 or t <= 0:
        return b
    sigma_cr = (k * np.pi ** 2 * E) / (12.0 * (1.0 - nu ** 2) * (b / t) ** 2)
    lam_p = np.sqrt(sigma_act / sigma_cr)
    if lam_p <= 0.673:
        return b
    rho = (lam_p - 0.22) / (lam_p ** 2)
    return float(rho * b)


def iterate_effective(data: EffectiveIterInput) -> EffectiveIterResult:
    """Itera hasta convergencia del ratio b_eff/b_gross.

    El usuario provee ``sigma_demand_provider`` que sabe cómo re-correr
    el solver con el ratio actual y devolver la nueva tensión actuante.
    """
    ratio = 1.0
    history: list[float] = [ratio]
    converged = False
    for i in range(1, data.max_iter + 1):
        sigma_act = data.sigma_demand_provider(ratio)
        b_eff = _b_eff_aisi(data.b_gross, data.t, sigma_act,
                            data.sigma_y, data.E,
                            k=data.k_plate, nu=data.nu)
        new_ratio = b_eff / data.b_gross
        history.append(new_ratio)
        if abs(new_ratio - ratio) / max(ratio, 1e-9) < data.tol:
            ratio = new_ratio
            converged = True
            break
        ratio = new_ratio
    return EffectiveIterResult(
        iterations=i, converged=converged,
        final_ratio=ratio, history=history,
    )


__all__ = [
    "EffectiveIterInput", "EffectiveIterResult",
    "iterate_effective", "_b_eff_aisi",
]
