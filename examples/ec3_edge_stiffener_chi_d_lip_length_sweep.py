"""Rigidizador de borde según EN 1993-1-3 §5.5.3: cuánto labio hace falta para que χ_d no penalice.

Sección C 200x60xc x1,5 (S350) con el labio c entre 8 y 30 mm. Para cada longitud se
obtiene la rigidez de muelle K, la tensión crítica del rigidizador σ_cr,s, la esbeltez
λ̄_d y el factor χ_d, en compresión y en flexión. Con labios cortos el rigidizador no
llega a estabilizar el ala (χ_d bajo); por encima de cierto c el beneficio se agota y
la norma avisa cuando c/b sale del rango recomendado 0,2–0,6.

Ejecutar:  python examples/ec3_edge_stiffener_chi_d_lip_length_sweep.py
"""
from coldformed.distortional import SectionGeometryCZ, ec3_distortional_buckling

FY = 350.0


def main() -> None:
    print("C 200x60xc x1,5, S350\n")
    print(f"{'c [mm]':>6} {'c/b':>5} | {'K':>8} {'σ_cr,s':>7} {'λ̄_d':>6} {'χ_d':>6} {'N_c,Rd':>7} | "
          f"{'χ_d flex':>8} {'M_c,Rd':>7}  avisos")
    for c in (8.0, 12.0, 15.0, 20.0, 25.0, 30.0):
        sec = SectionGeometryCZ(h_mm=200.0, b_mm=60.0, lip_mm=c, t_mm=1.5, shape="C")
        rc = ec3_distortional_buckling(sec, fyb_MPa=FY, loading="compression")
        rb = ec3_distortional_buckling(sec, fyb_MPa=FY, loading="bending")
        notes = "; ".join(rc.validity_notes) if rc.validity_notes else "—"
        print(f"{c:6.0f} {sec.lip_b:5.2f} | {rc.K_spring_N_per_mm2:8.4f} {rc.sigma_cr_s_MPa:7.1f} {rc.lambda_bar_d:6.3f} "
              f"{rc.chi_d:6.3f} {rc.Nc_Rd_kN:7.1f} | {rb.chi_d:8.3f} {rb.Mc_Rd_kNm:7.2f}  {notes}")


if __name__ == "__main__":
    main()
