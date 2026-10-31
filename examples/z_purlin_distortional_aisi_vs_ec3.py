"""Correa Z 250x75x20x2,5: pandeo distorsional según AISI S100 (DSM) y según EN 1993-1-3 §5.5.3.

Los dos métodos resuelven el mismo fenómeno (el ala con su labio gira sobre la unión
con el alma) con modelos distintos: AISI calcula σ_crd con las rigideces rotacionales
de Schafer y entra en las curvas de resistencia del DSM; EN 1993-1-3 idealiza el labio
como rigidizador sobre un muelle de rigidez K, obtiene σ_cr,s y reduce su espesor con
χ_d. Se imprimen los intermedios de cada método y las capacidades en compresión y
flexión.

Ejecutar:  python examples/z_purlin_distortional_aisi_vs_ec3.py
"""
from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling, ec3_distortional_buckling

SEC = SectionGeometryCZ(h_mm=250.0, b_mm=75.0, lip_mm=20.0, t_mm=2.5, shape="Z")
FY = 350.0


def main() -> None:
    print(f"Z {SEC.h_mm:.0f}x{SEC.b_mm:.0f}x{SEC.lip_mm:.0f}x{SEC.t_mm:.1f}, f_y = {FY:.0f} MPa, "
          f"A = {SEC.gross_area_mm2:.0f} mm², S_f ≈ {SEC.gross_modulus_major_mm3 / 1e3:.1f} cm³\n")

    a = aisi_distortional_buckling(SEC, Fy_MPa=FY)
    print(f"{a.standard} — {a.method}")
    print(f"  σ_crd = {a.sigma_crd_MPa:.1f} MPa, L_crd = {a.L_crd_mm:.0f} mm")
    print(f"  compresión: P_y = {a.Py_kN:.1f}, P_crd = {a.Pcrd_kN:.1f}, λ_d = {a.lambda_d_c:.3f} → "
          f"P_nd = {a.Pnd_kN:.1f} kN, φ_c·P_n = {a.phi_c_Pn_kN:.1f} kN")
    print(f"  flexión:    M_y = {a.My_kNm:.2f}, M_crd = {a.Mcrd_kNm:.2f}, λ_d = {a.lambda_d_b:.3f} → "
          f"M_nd = {a.Mnd_kNm:.2f} kN·m, φ_b·M_n = {a.phi_b_Mn_kNm:.2f} kN·m")
    print(f"  válido DSM: {a.is_valid_dsm} {a.validity_notes}\n")

    for loading in ("compression", "bending"):
        e = ec3_distortional_buckling(SEC, fyb_MPa=FY, loading=loading)
        print(f"{e.standard} — {e.method} ({loading})")
        print(f"  K = {e.K_spring_N_per_mm2:.4f} N/mm², A_s = {e.As_eff_mm2:.1f} mm², I_s = {e.Is_eff_mm4:.0f} mm⁴")
        print(f"  σ_cr,s = {e.sigma_cr_s_MPa:.1f} MPa, λ̄_d = {e.lambda_bar_d:.3f}, χ_d = {e.chi_d:.3f}, "
              f"t_red = {e.t_red_mm:.3f} mm")
        cap = f"N_c,Rd = {e.Nc_Rd_kN:.1f} kN" if loading == "compression" else f"M_c,Rd = {e.Mc_Rd_kNm:.2f} kN·m"
        print(f"  {cap}; válido EC3: {e.is_valid_ec3} {e.validity_notes}")


if __name__ == "__main__":
    main()
