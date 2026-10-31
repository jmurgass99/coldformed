"""Ancho eficaz de elementos de placa comprimidos (EN 1993-1-5 §4.4).

Para una viga armada de Clase 4 se calcula el factor de reducción ρ de Winter
del alma (flexión pura, ψ = −1, k_σ = 23,9) y del ala comprimida (compresión
uniforme, ψ = 1, k_σ = 4) para varias esbelteces b/t, y se muestra cuánto alma
"se pierde" en cada caso.

Ejecutar:  python examples/01_effective_width_class4.py
"""
from coldformed.class4_evaluator import effective_width_factor_rho, plate_relative_slenderness

FY = 355.0


def table(title: str, psi: float, k_sigma: float, ratios: list[float]) -> None:
    print(f"{title}  (ψ = {psi:+.0f}, k_σ = {k_sigma})")
    print(f"  {'b/t':>6} {'λ_p':>7} {'ρ':>6} {'b_eff/b':>8}")
    for bt in ratios:
        lam = plate_relative_slenderness(b_bar=bt * 10.0, t=10.0, fy=FY, k_sigma=k_sigma)
        rho = effective_width_factor_rho(lam, psi=psi)
        print(f"  {bt:6.0f} {lam:7.3f} {rho:6.3f} {rho:8.1%}")
    print()


def main() -> None:
    print(f"Acero S{FY:.0f}, ε = {(235 / FY) ** 0.5:.3f}\n")
    table("Alma en flexión pura", psi=-1.0, k_sigma=23.9, ratios=[80, 100, 124, 150, 200, 250])
    table("Ala comprimida apoyada en ambos bordes", psi=1.0, k_sigma=4.0, ratios=[30, 38, 42, 50, 60, 80])

    # Caso de referencia: alma 1500 x 10 mm (W00777) → ρ = 0,69
    lam = plate_relative_slenderness(b_bar=1500.0, t=10.0, fy=FY, k_sigma=23.9)
    rho = effective_width_factor_rho(lam, psi=-1.0)
    print(f"Alma 1500 x 10 mm en flexión: λ_p = {lam:.3f}, ρ = {rho:.2f} "
          f"→ altura eficaz comprimida = {rho * 750:.0f} mm de 750 mm")


if __name__ == "__main__":
    main()
