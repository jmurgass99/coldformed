"""Montante C en compresión por DSM: local desde la curva FSM, distorsional desde AISI Apéndice 2, global de Euler.

Sección C 200x60x20x2 (S350), montante de 2 400 mm sin arriostrar. Las tres cargas
críticas del Método de la Resistencia Directa se obtienen cada una por la vía que el
paquete resuelve bien: el mínimo local de la curva de franjas finitas refinada
(`refine_profile_strips`, 4 subfranjas por elemento), la tensión distorsional de
`aisi_distortional_buckling` (AISI S100-16 Apéndice 2) y la carga de Euler sobre el
eje débil con I_min = 3,0·10⁵ mm⁴ (dato de entrada: la curva FSM de este ensamblado
no reproduce el modo global). Con ellas, `dsm_compression` aplica §E2–§E4.

Ejecutar:  python examples/stud_dsm_local_from_fsm_distortional_from_appendix2.py
"""
import math

import numpy as np

from coldformed.direct_strength import DSMCompressionInput, dsm_compression
from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling
from coldformed.fsm_assembly import build_profile_strips, compute_signature_curve_fsm, refine_profile_strips

DIMS = {"H": 200.0, "B": 60.0, "D": 20.0, "t": 2.0}
FY, E = 350.0, 210_000.0
L_MM, I_MIN_MM4 = 2400.0, 3.0e5


def main() -> None:
    sec = SectionGeometryCZ(DIMS["H"], DIMS["B"], DIMS["D"], DIMS["t"], "C")
    A = sec.gross_area_mm2

    strips = refine_profile_strips(build_profile_strips("C", DIMS), n_sub=4)
    lams = np.logspace(np.log10(50.0), np.log10(600.0), 40)
    curve = compute_signature_curve_fsm(strips, np.ones(strips.n_strips), lams)
    i = int(np.argmin(curve.sigma_cr_MPa))
    sigma_crl, lam_l = float(curve.sigma_cr_MPa[i]), float(curve.half_wavelengths_mm[i])

    dist = aisi_distortional_buckling(sec, Fy_MPa=FY)
    Pcre = math.pi ** 2 * E * I_MIN_MM4 / L_MM ** 2 / 1e3

    print(f"C {DIMS['H']:.0f}x{DIMS['B']:.0f}x{DIMS['D']:.0f}x{DIMS['t']:.1f}, A = {A:.0f} mm², L = {L_MM:.0f} mm")
    print(f"  local (FSM refinado):       σ_crl = {sigma_crl:6.1f} MPa a λ = {lam_l:.0f} mm → P_crl = {sigma_crl * A / 1e3:.1f} kN")
    print(f"  distorsional (Apéndice 2):  σ_crd = {dist.sigma_crd_MPa:6.1f} MPa a L_cr = {dist.L_crd_mm:.0f} mm → P_crd = {dist.Pcrd_kN:.1f} kN")
    print(f"  global (Euler, I_min dato): P_cre = {Pcre:.1f} kN")

    r = dsm_compression(DSMCompressionInput(Pcrl_kN=sigma_crl * A / 1e3, Pcrd_kN=dist.Pcrd_kN, Pcre_kN=Pcre,
                                            A_mm2=A, Fy_MPa=FY))
    print(f"\nDSM: P_y = {r['Py_kN']:.1f}  P_ne = {r['Pne_kN']:.1f}  P_nl = {r['Pnl_kN']:.1f}  P_nd = {r['Pnd_kN']:.1f}"
          f"  →  P_n = {r['Pn_kN']:.1f} kN, gobierna {r['governing_mode']}; φ_c·P_n = {0.85 * r['Pn_kN']:.1f} kN")


if __name__ == "__main__":
    main()
