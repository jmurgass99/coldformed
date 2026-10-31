"""Curva de firma de una sección C por franjas finitas: lo que el ensamblado captura y lo que no.

Sección C 200x60x20x2 en compresión uniforme. `build_profile_strips` crea cinco
franjas (labio, ala, alma, ala, labio); `refine_profile_strips` subdivide cada una
en cuatro para que el alma pueda flectar en media onda. Se comparan las dos curvas
y sus mínimos.

Resultado honesto: el ensamblado actual reproduce el modo local (mínimo a λ ≈ 150 mm,
que baja de 154 a 109 MPa al refinar, frente a 76 MPa del alma aislada con k = 4), pero
no muestra el mínimo distorsional (que AISI S100 Apéndice 2 sitúa en 228 MPa a
λ ≈ 590 mm para esta sección) ni el global (a λ = 2,6 m da miles de MPa donde Euler
daría unos 200). Para σ_crd usa `distortional.aisi_distortional_buckling`; la curva
FSM sirve para el modo local.

Ejecutar:  python examples/fsm_signature_curve_c_section_modes.py
"""
import numpy as np

from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling
from coldformed.fsm_assembly import build_profile_strips, compute_signature_curve_fsm, refine_profile_strips
from coldformed.local_buckling import local_critical_stress

DIMS = {"H": 200.0, "B": 60.0, "D": 20.0, "t": 2.0}


def main() -> None:
    base = build_profile_strips("C", DIMS)
    fine = refine_profile_strips(base, n_sub=4)
    lams = np.logspace(np.log10(20.0), np.log10(5000.0), 60)
    curves = {
        f"1 franja por elemento ({base.n_strips} franjas, {base.n_nodes} nodos)":
            compute_signature_curve_fsm(base, np.ones(base.n_strips), lams),
        f"4 subfranjas por elemento ({fine.n_strips} franjas, {fine.n_nodes} nodos)":
            compute_signature_curve_fsm(fine, np.ones(fine.n_strips), lams),
    }
    print(f"{'λ [mm]':>8} | " + " | ".join(f"{k[:22]:>22}" for k in curves))
    for i in range(0, len(lams), 5):
        print(f"{lams[i]:8.1f} | " + " | ".join(f"{c.sigma_cr_MPa[i]:22.1f}" for c in curves.values()))
    for name, c in curves.items():
        print(f"\n{name}: mínimos detectados " + ", ".join(f"{m} λ = {l:.0f} mm, σ = {s:.1f} MPa" for l, s, m in c.minima))

    web = local_critical_stress(DIMS["H"], DIMS["t"], boundary="ss_ss").sigma_cr_MPa
    d = aisi_distortional_buckling(SectionGeometryCZ(DIMS["H"], DIMS["B"], DIMS["D"], DIMS["t"], "C"), 350.0)
    print(f"\nReferencias: alma aislada k = 4 → {web:.1f} MPa; AISI Apéndice 2 distorsional → "
          f"{d.sigma_crd_MPa:.1f} MPa a L_cr = {d.L_crd_mm:.0f} mm.")
    print("La curva FSM no presenta mínimo en torno a 590 mm ni se aplana a longitudes largas: "
          "este ensamblado solo es fiable para el modo local.")


if __name__ == "__main__":
    main()
