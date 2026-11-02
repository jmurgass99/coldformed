"""Resistencia a cortante del alma según AISI S100-16 §G2: fluencia, pandeo inelástico y elástico.

Para almas de 100 a 400 mm con t = 1,5 mm y f_y = 350 MPa se obtiene V_n = A_w·F_v con
el régimen que gobierna según la esbeltez de cortante λ_v (k_v = 5,34, alma sin
rigidizadores). Un alma de correa con h/t alto cae en pandeo elástico y su cortante
resistente es una fracción pequeña de 0,6·f_y·A_w. Las mismas almas se comprueban con
`shear_capacity_ec3` (EN 1993-1-3 §6.1.5: λ_w = 0,346·(s_w/t)·√(f_yb/E), f_bv de la Tabla 6.1 sin
rigidizador en apoyo, V_b,Rd con γ_M0 = 1) y se rehace a mano V_b,Rd del alma más esbelta.

Ejecutar:  python examples/web_shear_capacity_aisi_g2_regimes.py
"""
import math

from coldformed.shear import EC3ShearInput, ShearInput, shear_capacity, shear_capacity_ec3

T, FY = 1.5, 350.0


def main() -> None:
    print(f"t = {T} mm, f_y = {FY:.0f} MPa, k_v = 5,34\n")
    print(f"{'h [mm]':>6} {'h/t':>6} {'V_y [kN]':>9} {'V_cr [kN]':>10} {'λ_v':>6} {'V_n [kN]':>9}  régimen")
    for h in (100.0, 150.0, 200.0, 250.0, 300.0, 400.0):
        r = shear_capacity(ShearInput(h_mm=h, t_mm=T, Fy_MPa=FY))
        print(f"{h:6.0f} {h / T:6.0f} {r.Vy_kN:9.2f} {r.Vcr_kN:10.2f} {r.lambda_v:6.3f} {r.Vn_kN:9.2f}  {r.regime}")
    print("\nCon rigidizadores transversales k_v sube y el alma esbelta recupera cortante: pasa k_v en ShearInput.")

    print(f"\nEN 1993-1-3 §6.1.5 (alma recta, sin rigidizador en apoyo, γ_M0 = 1) frente a AISI V_n:")
    print(f"{'h [mm]':>6} {'λ_w':>6} {'f_bv [MPa]':>10} {'V_b,Rd [kN]':>11} {'AISI V_n':>9} {'EC3/AISI':>8}  régimen EC3")
    for h in (100.0, 150.0, 200.0, 250.0, 300.0, 400.0):
        e = shear_capacity_ec3(EC3ShearInput(hw_mm=h, t_mm=T, fyb_MPa=FY))
        a = shear_capacity(ShearInput(h_mm=h, t_mm=T, Fy_MPa=FY))
        print(f"{h:6.0f} {e.lambda_w:6.3f} {e.fbv_MPa:10.1f} {e.Vb_Rd_kN:11.2f} {a.Vn_kN:9.2f} {e.Vb_Rd_kN / a.Vn_kN:8.2f}  {e.regime}")
    lam = 0.346 * (400.0 / T) * math.sqrt(FY / 210000.0)
    fbv = 0.67 * FY / lam ** 2 if lam >= 1.40 else (0.48 * FY / lam if lam > 0.83 else 0.58 * FY)
    print(f"A mano, h = 400 mm: λ_w = {lam:.3f}, f_bv = {fbv:.1f} MPa, V_b,Rd = 400·{T}·f_bv = {400.0 * T * fbv / 1e3:.2f} kN")


if __name__ == "__main__":
    main()
