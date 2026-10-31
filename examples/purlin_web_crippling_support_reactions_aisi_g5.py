"""Abolladura del alma de una correa en los apoyos (web crippling, AISI S100-16 §G5).

Correa C 250x75x20x2,0 (f_y = 350 MPa, radio interior de doblado R = 3 mm) apoyada
sobre una placa de N = 60 mm. Se compara la reacción nominal y de diseño (φ = 0,75)
para apoyo extremo y apoyo interior, un ala y dos alas, con alas rigidizadas, y se
mira el efecto de la longitud de apoyo N y del espesor t. Los coeficientes C, C_R, C_N
y C_h son los conjuntos representativos de la Tabla G5-1 incluidos en el paquete.

Ejecutar:  python examples/purlin_web_crippling_support_reactions_aisi_g5.py
"""
from coldformed.web_crippling import COEFF_SETS, web_crippling_strength

T, FY, R, H = 2.0, 350.0, 3.0, 250.0


def main() -> None:
    print(f"C 250x75x20x{T}, f_y = {FY:.0f}, R = {R} mm, h = {H:.0f} mm, N = 60 mm\n")
    print(f"{'caso':<32} {'P_n [kN]':>9} {'φP_n [kN]':>10}  coeficientes")
    for case in COEFF_SETS:
        r = web_crippling_strength(T, FY, R, 60.0, H, case=case)
        print(f"{case:<32} {r.Pn_kN:9.2f} {r.Pn_design_kN:10.2f}  {r.coeffs}")

    print("\nApoyo interior, un ala: efecto de la longitud de apoyo N y del espesor t")
    print(f"{'N [mm]':>6} | " + " ".join(f"t={t}" .rjust(8) for t in (1.5, 2.0, 2.5, 3.0)))
    for N in (40.0, 60.0, 100.0, 150.0):
        row = [web_crippling_strength(t, FY, R, N, H).Pn_design_kN for t in (1.5, 2.0, 2.5, 3.0)]
        print(f"{N:6.0f} | " + " ".join(f"{v:8.2f}" for v in row))


if __name__ == "__main__":
    main()
