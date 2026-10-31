"""Franjas finitas con kernel Numba frente a la solución cerrada de Bryan: convergencia y diagnóstico.

`local_critical_stress_fsm` ensambla n franjas a lo ancho de la placa, aplica la
condición de borde y barre la semilongitud de onda para quedarse con el mínimo de la
curva de firma. Se compara con la solución analítica para una placa apoyada (k = 4)
y para un voladizo (k = 0,425, que necesita L/b grande) con 4, 8 y 16 franjas, y se
muestra el diagnóstico del barrido (longitudes intentadas y convergidas). La primera
llamada compila el kernel JIT y tarda unos segundos.

Ejecutar:  python examples/fsm_jit_plate_convergence_vs_bryan.py
"""
from coldformed.local_buckling import local_critical_stress, local_critical_stress_fsm

B, T = 120.0, 1.5


def main() -> None:
    for boundary in ("ss_ss", "ss_free"):
        ref = local_critical_stress(B, T, boundary=boundary)
        print(f"Placa {B:.0f}x{T} mm, borde {boundary}: Bryan σ_cr = {ref.sigma_cr_MPa:.3f} MPa (k = {ref.k})")
        for n in (4, 8, 16):
            r = local_critical_stress_fsm(B, T, boundary=boundary, n_strips=n)
            err = r.sigma_cr_MPa / ref.sigma_cr_MPa - 1.0
            print(f"  {n:2d} franjas: σ_cr = {r.sigma_cr_MPa:.3f} MPa, k_ef = {r.k:.4f}, error {err:+.2e}; "
                  f"barrido {r.n_lengths_converged}/{r.n_lengths_attempted} longitudes convergidas"
                  f"{'' if not r.failed_ratios else ', L/b fallidas: ' + str(r.failed_ratios)}")
        print()


if __name__ == "__main__":
    main()
