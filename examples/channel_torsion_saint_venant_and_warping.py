"""Torsión de un canal de pared delgada: J de Saint-Venant, tensión tangencial y constante de alabeo.

Canal C 200x75x2,5 (sin labios) sometido a un par de 150 N·m por una carga excéntrica.
J = (1/3)·Σ b·t³ es muy pequeño en secciones abiertas, así que la tensión de
Saint-Venant τ = T·t/J crece deprisa; la constante de alabeo C_w del canal (fórmula
clásica) indica que la mayor parte del par se resiste por torsión no uniforme. El
chequeo compara τ con 0,6·f_y.

Ejecutar:  python examples/channel_torsion_saint_venant_and_warping.py
"""
from coldformed.torsion_open import torsion_check, torsion_constant_J, warping_constant_channel

H, B, T, FY = 200.0, 75.0, 2.5, 350.0
ELEMENTS = [(H, T), (B, T), (B, T)]           # alma y dos alas (longitud, espesor)


def main() -> None:
    J = torsion_constant_J(ELEMENTS)
    Cw = warping_constant_channel(H - T, B - T / 2, T)
    print(f"Canal {H:.0f}x{B:.0f}x{T}: J = {J:.1f} mm⁴, C_w = {Cw:.3e} mm⁶")
    print(f"{'T [N·m]':>8} {'τ_sv [MPa]':>11}  frente a 0,6·f_y = {0.6 * FY:.0f} MPa")
    for T_Nm in (25.0, 50.0, 100.0, 150.0, 250.0):
        r = torsion_check(ELEMENTS, T_Nmm=T_Nm * 1e3, t_max_mm=T, Fy_MPa=FY)
        print(f"{T_Nm:8.0f} {r.tau_MPa:11.1f}  {'OK' if r.ok else 'NO'}")
    print("\nCon J tan bajo, cargas fuera del centro de esfuerzos cortantes deben resistirse por alabeo "
          "o evitarse con arriostramiento: este chequeo solo acota la componente de Saint-Venant.")


if __name__ == "__main__":
    main()
