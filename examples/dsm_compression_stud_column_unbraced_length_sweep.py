"""Montante C en compresión por el Método de la Resistencia Directa: efecto de la longitud sin arriostrar.

Montante C 150x50x15x1,5 (S350), A = 420 mm². Las cargas críticas elásticas vienen
de: pandeo local del alma (placa apoyada, k = 4) multiplicada por el área, pandeo
distorsional según Schafer (σ_crd del módulo `distortional`) y pandeo global de
Euler con I_min = 1,2·10⁵ mm⁴ para cada longitud. `dsm_compression` aplica las curvas
de AISI S100 §E2, §E3 y §E4 y devuelve el modo que gobierna.

Ejecutar:  python examples/dsm_compression_stud_column_unbraced_length_sweep.py
"""
import math

from coldformed.direct_strength import DSMCompressionInput, dsm_compression
from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling
from coldformed.local_buckling import local_critical_stress

E = 210_000.0
FY = 350.0
I_MIN_MM4 = 1.2e5
SEC = SectionGeometryCZ(h_mm=150.0, b_mm=50.0, lip_mm=15.0, t_mm=1.5, shape="C")


def main() -> None:
    A = SEC.gross_area_mm2
    sigma_crl = local_critical_stress(SEC.h_mm, SEC.t_mm, boundary="ss_ss").sigma_cr_MPa
    dist = aisi_distortional_buckling(SEC, Fy_MPa=FY)
    Pcrl = sigma_crl * A / 1e3
    Pcrd = dist.Pcrd_kN
    print(f"A = {A:.0f} mm², P_y = {A * FY / 1e3:.1f} kN")
    print(f"σ_crl (alma, k = 4) = {sigma_crl:.1f} MPa → P_crl = {Pcrl:.1f} kN")
    print(f"σ_crd (Schafer)     = {dist.sigma_crd_MPa:.1f} MPa → P_crd = {Pcrd:.1f} kN, L_crd = {dist.L_crd_mm:.0f} mm\n")
    print(f"{'L [m]':>6} {'P_cre':>7} {'P_ne':>7} {'P_nl':>7} {'P_nd':>7} {'P_n':>7}  gobierna")
    for L_m in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        Pcre = math.pi ** 2 * E * I_MIN_MM4 / (L_m * 1e3) ** 2 / 1e3
        r = dsm_compression(DSMCompressionInput(Pcrl_kN=Pcrl, Pcrd_kN=Pcrd, Pcre_kN=Pcre, A_mm2=A, Fy_MPa=FY))
        print(f"{L_m:6.1f} {Pcre:7.1f} {r['Pne_kN']:7.1f} {r['Pnl_kN']:7.1f} {r['Pnd_kN']:7.1f} {r['Pn_kN']:7.1f}  "
              f"{r['governing_mode']}")
    print("\nφ_c = 0,85 (LRFD) se aplica después con codes_multi.design_resistance_compression.")


if __name__ == "__main__":
    main()
