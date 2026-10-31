"""Método de la Resistencia Directa (AISI S100) en flexión: barrido de modos.

Con el momento de fluencia fijo, se varían los momentos críticos elásticos
local (M_crl) y distorsional (M_crd) para ver qué modo gobierna la resistencia
nominal M_n y cuánto penaliza cada uno. Útil para decidir si merece la pena
rigidizar el ala o reducir la luz entre arriostramientos.

Ejecutar:  python examples/03_dsm_flexure_sweep.py
"""
from coldformed.direct_strength import DSMFlexureInput, dsm_flexure

SF_MM3 = 34_000.0   # módulo elástico de la sección
FY = 350.0
MCRE = 30.0         # pandeo lateral-torsional (kN·m), arriostramiento cada 2 m


def main() -> None:
    My = SF_MM3 * FY / 1e6
    print(f"M_y = S_f·f_y = {My:.2f} kN·m, M_cre = {MCRE:.1f} kN·m\n")
    print(f"{'M_crl':>7} {'M_crd':>7} | {'M_nl':>7} {'M_nd':>7} {'M_ne':>7} | {'M_n':>7}  gobierna")
    print("-" * 66)
    for mcrl in (6.0, 9.0, 14.0, 25.0):
        for mcrd in (8.0, 10.5, 16.0):
            r = dsm_flexure(DSMFlexureInput(Mcrl_kNm=mcrl, Mcrd_kNm=mcrd, Mcre_kNm=MCRE,
                                            Sf_mm3=SF_MM3, Fy_MPa=FY))
            print(f"{mcrl:7.1f} {mcrd:7.1f} | {r.Mnl_kNm:7.2f} {r.Mnd_kNm:7.2f} {r.Mne_kNm:7.2f} | "
                  f"{r.Mn_kNm:7.2f}  {r.governing_mode}")
    print("\nM_n = min(M_nl, M_nd, M_ne); la columna 'gobierna' indica el modo que limita.")


if __name__ == "__main__":
    main()
