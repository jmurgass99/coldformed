"""Tabla de capacidades distorsionales para los perfiles C y Z del catálogo del paquete.

Cada entrada del catálogo (AISI y EN 1993-1-3) se convierte en una `SectionGeometryCZ`
y se evalúa con los dos métodos: φ_c·P_n y φ_b·M_n del DSM de AISI y N_c,Rd y M_c,Rd
de EN 1993-1-3 §5.5.3. Sirve de preselección antes de comprobar la correa con sus
condiciones reales de arriostramiento.

Ejecutar:  python examples/catalogue_profiles_distortional_capacity_table.py
"""
from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling, ec3_distortional_buckling
from coldformed.profile_catalog import list_profiles

FY = 350.0


def main() -> None:
    print(f"f_y = {FY:.0f} MPa\n")
    print(f"{'perfil':<16} {'kg/m':>5} | {'φP_n AISI':>9} {'φM_n AISI':>9} | {'N_c,Rd EC3':>10} {'M_c,Rd EC3':>10}")
    for p in list_profiles(shape="C") + list_profiles(shape="Z"):
        sec = SectionGeometryCZ(h_mm=p.h_mm, b_mm=p.b_mm, lip_mm=p.lip_mm, t_mm=p.t_mm, shape=p.shape)
        a = aisi_distortional_buckling(sec, Fy_MPa=FY)
        ec = ec3_distortional_buckling(sec, fyb_MPa=FY, loading="compression")
        eb = ec3_distortional_buckling(sec, fyb_MPa=FY, loading="bending")
        flag = "" if a.is_valid_dsm and ec.is_valid_ec3 else "  *"
        print(f"{p.name:<16} {p.mass_kg_per_m:5.2f} | {a.phi_c_Pn_kN:9.1f} {a.phi_b_Mn_kNm:9.2f} | "
              f"{ec.Nc_Rd_kN:10.1f} {eb.Mc_Rd_kNm:10.2f}{flag}")
    print("\n* fuera de los límites de aplicabilidad de alguno de los métodos (ver applicability_limits_geometry_sweep.py)")
    print("Unidades: kN y kN·m. Los perfiles Σ del catálogo no se evalúan: los dos módulos cubren solo C y Z.")


if __name__ == "__main__":
    main()
