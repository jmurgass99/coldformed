"""Alma de una correa C 200.74.2 (S350GD) bajo gradiente de tensiones: ρ de Winter con ψ = −0,74.

Exercise 16 del máster UPC (ficha W01486): ancho plano del alma h_p = 198 mm,
espesor neto t = 1,96 mm (descontado el galvanizado), f_y = 350 MPa. El eje neutro
no está en el centro del alma, así que ψ = −0,74 y k_σ sale de la fórmula de
interpolación de EN 1993-1-5 Tabla 4.1 para elementos internos (0 > ψ > −1):
k_σ = 7,81 − 6,29·ψ + 9,78·ψ² = 17,82. Resultado de la ficha: λ_p = 1,03, ρ = 0,85.
Se muestra además lo que saldría con un ψ equivocado (+1) y con la fórmula de
voladizo (0,188), para ver que el caso no pasa por casualidad.

Ejecutar:  python examples/exam_c200_purlin_web_stress_gradient_psi_w01486.py
"""
from coldformed.class4_evaluator import effective_width_factor_rho, plate_relative_slenderness

FY, HP, T, PSI = 350.0, 198.0, 1.96, -0.74


def k_sigma_internal(psi: float) -> float:
    """EN 1993-1-5 Tabla 4.1, elemento interno, 0 > ψ > −1."""
    return 7.81 - 6.29 * psi + 9.78 * psi ** 2


def main() -> None:
    k = k_sigma_internal(PSI)
    lam = plate_relative_slenderness(b_bar=HP, t=T, fy=FY, k_sigma=k)
    rho = effective_width_factor_rho(lam, psi=PSI)
    print(f"C 200.74.2, S350GD: h_p = {HP} mm, t = {T} mm, ψ = {PSI}")
    print(f"  ε = {(235 / FY) ** 0.5:.4f}, k_σ = {k:.2f} (fórmula Tabla 4.1)")
    print(f"  λ_p = {lam:.4f}   (ficha: 1,03)")
    print(f"  ρ   = {rho:.4f}   (ficha: 0,85)")
    print(f"  altura eficaz comprimida de la parte plana: ρ·h_p = {rho * HP:.1f} mm de {HP:.0f} mm\n")

    rho_psi1 = effective_width_factor_rho(lam, psi=1.0)
    rho_outstand = (lam - 0.188) / lam ** 2
    print("Mismo λ_p con hipótesis equivocadas:")
    print(f"  ψ = +1 (compresión uniforme): ρ = {rho_psi1:.3f}")
    print(f"  fórmula de voladizo (0,188):  ρ = {rho_outstand:.3f}")
    print("  Ninguna reproduce el 0,85 de la ficha: el término 0,055·(3+ψ) y el umbral dependen de ψ.")


if __name__ == "__main__":
    main()
