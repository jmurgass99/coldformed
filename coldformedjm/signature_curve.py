"""
Signature curve (Schafer) — σ_cr vs half-wavelength para identificar
modos Local / Distorsional / Global en perfiles cold-formed.

Implementación simplificada: para una placa con propiedades dadas,
calcula σ_cr en función de λ = half-wavelength. La curva real CUFSM
involucra resolución de auto-valores K_E·φ = λ·K_G·φ — aquí usamos
una aproximación analítica suficiente para identificar regiones.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np


@dataclass(frozen=True)
class SignatureInput:
    width_mm: float
    thickness_mm: float
    E_MPa: float = 210_000.0
    nu: float = 0.30
    half_wavelengths_mm: np.ndarray | None = None


@dataclass(frozen=True)
class SignatureResult:
    half_wavelengths_mm: np.ndarray
    sigma_cr_MPa: np.ndarray
    minima: list[tuple[float, float, str]]   # (λ, σ, mode_name)


def signature_curve(inp: SignatureInput) -> SignatureResult:
    """Calcula σ_cr(λ) y detecta mínimos locales (Local, Distorsional)."""
    if inp.half_wavelengths_mm is None:
        lams = np.logspace(np.log10(20), np.log10(5000), 80)
    else:
        lams = np.asarray(inp.half_wavelengths_mm, dtype=float)

    b, t = inp.width_mm, inp.thickness_mm
    D = inp.E_MPa * t ** 3 / (12 * (1 - inp.nu ** 2))

    # σ_cr en función de half-wavelength λ y ancho b
    # k = (b/λ + λ/b)² para placa simplemente apoyada
    sigma = np.zeros_like(lams)
    for i, lam in enumerate(lams):
        k = (b / lam + lam / b) ** 2
        sigma[i] = (k * pi ** 2 * D) / (b ** 2 * t)

    # Mínimos locales
    minima: list[tuple[float, float, str]] = []
    # Mínimo Local (λ ≈ b → k=4)
    idx_local = int(np.argmin(np.abs(lams - b)))
    minima.append((float(lams[idx_local]), float(sigma[idx_local]), "Local"))
    # Mínimo distorsional (λ ≈ 4-6 · b típicamente)
    mask = (lams > 3 * b) & (lams < 8 * b)
    if mask.any():
        sub = sigma[mask]
        idx_d = int(np.argmin(sub))
        idx_dist = np.where(mask)[0][idx_d]
        minima.append((float(lams[idx_dist]), float(sigma[idx_dist]),
                        "Distortional"))
    # Global = λ grande
    minima.append((float(lams[-1]), float(sigma[-1]), "Global"))

    return SignatureResult(
        half_wavelengths_mm=lams, sigma_cr_MPa=sigma, minima=minima,
    )


__all__ = ["SignatureInput", "SignatureResult", "signature_curve"]
