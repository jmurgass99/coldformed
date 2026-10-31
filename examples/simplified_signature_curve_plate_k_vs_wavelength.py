"""Curva σ_cr(λ) de una placa aislada: el coeficiente k = (b/λ + λ/b)² y su mínimo en λ = b.

`signature_curve` es la versión analítica para una placa apoyada en ambos bordes:
sirve para ver por qué el pandeo local aparece a semilongitudes de onda del orden del
ancho (k = 4 exactamente en λ = b) y cómo crece k para ondas más cortas o más largas.
Los mínimos «distorsional» y «global» que devuelve son etiquetas de región, no
resultados de una sección: para eso está la curva de franjas finitas de `fsm_assembly`.

Ejecutar:  python examples/simplified_signature_curve_plate_k_vs_wavelength.py
"""
import math

import numpy as np

from coldformed.signature_curve import SignatureInput, signature_curve

B, T, E, NU = 200.0, 2.0, 210_000.0, 0.30


def main() -> None:
    lams = np.array([50, 100, 150, 200, 250, 300, 400, 600, 1000, 2000], dtype=float)
    res = signature_curve(SignatureInput(width_mm=B, thickness_mm=T, half_wavelengths_mm=lams))
    D = E * T ** 3 / (12 * (1 - NU ** 2))
    base = math.pi ** 2 * D / (B ** 2 * T)
    print(f"Placa {B:.0f}x{T} mm apoyada-apoyada; π²D/(b²t) = {base:.3f} MPa\n")
    print(f"{'λ [mm]':>7} {'λ/b':>5} {'σ_cr [MPa]':>11} {'k':>7}")
    for lam, sig in zip(res.half_wavelengths_mm, res.sigma_cr_MPa):
        print(f"{lam:7.0f} {lam / B:5.2f} {sig:11.2f} {sig / base:7.3f}")
    print("\nMínimos etiquetados:")
    for lam, sig, mode in res.minima:
        print(f"  {mode:<13} λ = {lam:7.1f} mm, σ_cr = {sig:8.2f} MPa")


if __name__ == "__main__":
    main()
