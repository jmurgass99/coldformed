"""Resistencia a cortante del alma según AISI S100-16 §G2: fluencia, pandeo inelástico y elástico.

Para almas de 100 a 400 mm con t = 1,5 mm y f_y = 350 MPa se obtiene V_n = A_w·F_v con
el régimen que gobierna según la esbeltez de cortante λ_v (k_v = 5,34, alma sin
rigidizadores). Un alma de correa con h/t alto cae en pandeo elástico y su cortante
resistente es una fracción pequeña de 0,6·f_y·A_w. Este módulo implementa solo AISI:
la rama de EN 1993-1-3 §6.1.5 no está en el paquete.

Ejecutar:  python examples/web_shear_capacity_aisi_g2_regimes.py
"""
from coldformed.shear import ShearInput, shear_capacity

T, FY = 1.5, 350.0


def main() -> None:
    print(f"t = {T} mm, f_y = {FY:.0f} MPa, k_v = 5,34\n")
    print(f"{'h [mm]':>6} {'h/t':>6} {'V_y [kN]':>9} {'V_cr [kN]':>10} {'λ_v':>6} {'V_n [kN]':>9}  régimen")
    for h in (100.0, 150.0, 200.0, 250.0, 300.0, 400.0):
        r = shear_capacity(ShearInput(h_mm=h, t_mm=T, Fy_MPa=FY))
        print(f"{h:6.0f} {h / T:6.0f} {r.Vy_kN:9.2f} {r.Vcr_kN:10.2f} {r.lambda_v:6.3f} {r.Vn_kN:9.2f}  {r.regime}")
    print("\nCon rigidizadores transversales k_v sube y el alma esbelta recupera cortante: pasa k_v en ShearInput.")


if __name__ == "__main__":
    main()
