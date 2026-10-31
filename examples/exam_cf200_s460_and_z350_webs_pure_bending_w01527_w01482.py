"""Dos almas en flexión pura resueltas en el máster: CF 200.2 en S460 y Z 350.3 en S350GD.

Ficha W01527 (Problema 3, sección ligera): vigueta CF 200.2, S460, ancho plano del alma
198 mm, t = 2 mm, ψ = −1, k_σ = 23,88 → λ_p = 1,00, ρ = 0,89.
Ficha W01482 (Exercise 14): correa Z 350.3, S350GD, t = 3 mm, ψ = −1, k_σ = 23,9. La
ficha usa la altura total de 350 mm como ancho plano (no descuenta las esquinas), por
lo que el resultado es una afirmación a nivel de placa: λ_p = 1,03, ρ = 0,867.
Los dos casos confirman la fórmula de EN 1993-1-5 §4.4 con otro límite elástico y
otra relación b/t que el caso de referencia S355 (W00777).

Ejecutar:  python examples/exam_cf200_s460_and_z350_webs_pure_bending_w01527_w01482.py
"""
from coldformed.class4_evaluator import effective_width_factor_rho, plate_relative_slenderness

CASES = [
    ("CF 200.2, S460 (W01527)", 460.0, 198.0, 2.0, 23.88, 1.00, 0.89),
    ("Z 350.3, S350GD (W01482)", 350.0, 350.0, 3.0, 23.9, 1.03, 0.867),
    ("Viga armada 1488x10, S355 (W00777)", 355.0, 1488.0, 10.0, 23.9, 1.32, 0.69),
]


def main() -> None:
    print(f"{'caso':<38} {'b/t':>6} {'ε':>6} {'λ_p':>6} {'ρ':>6} | ficha λ_p / ρ")
    for name, fy, b, t, k, lam_ref, rho_ref in CASES:
        lam = plate_relative_slenderness(b_bar=b, t=t, fy=fy, k_sigma=k)
        rho = effective_width_factor_rho(lam, psi=-1.0)
        print(f"{name:<38} {b / t:6.1f} {(235 / fy) ** 0.5:6.3f} {lam:6.3f} {rho:6.3f} | "
              f"{lam_ref:.2f} / {rho_ref:.3f}")
    print("\nLas fichas redondean λ_p a dos decimales antes de evaluar ρ; la diferencia con el valor "
          "exacto es de 0,001 a 0,003 en ρ.")


if __name__ == "__main__":
    main()
