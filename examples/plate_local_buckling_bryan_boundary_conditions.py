"""Tensión crítica de pandeo local de placas (Bryan/Timoshenko) para las cuatro condiciones de borde.

σ_cr = k·π²·E/(12·(1−ν²))·(t/b)². Alma apoyada en ambos bordes (k = 4,0), ala en
voladizo apoyada-libre (k = 0,425), empotrada-empotrada (6,97) y empotrada-apoyada
(5,42), para una chapa de 2 mm y anchos de 50 a 300 mm. También con un k impuesto
por el usuario (`k_override`) para el caso de flexión pura del alma (k = 23,9).

Ejecutar:  python examples/plate_local_buckling_bryan_boundary_conditions.py
"""
from coldformed.fsm import PLATE_K, PlateBucklingInput, plate_critical_stress
from coldformed.local_buckling import local_critical_stress

T = 2.0


def main() -> None:
    print(f"t = {T} mm, E = 210 000 MPa, ν = 0,30\n")
    header = f"{'b [mm]':>7} {'b/t':>6} | " + " ".join(f"{bc:>8}" for bc in PLATE_K) + f" | {'k=23,9':>8}"
    print(header)
    print(f"{'':>16}" + " ".join(f"{'k=' + str(k):>8}" for k in PLATE_K.values()))
    for b in (50.0, 100.0, 150.0, 200.0, 300.0):
        row = [plate_critical_stress(PlateBucklingInput(b, T, boundary=bc)).sigma_cr_MPa for bc in PLATE_K]
        bend = plate_critical_stress(PlateBucklingInput(b, T, k_override=23.9)).sigma_cr_MPa
        print(f"{b:7.0f} {b / T:6.0f} | " + " ".join(f"{s:8.1f}" for s in row) + f" | {bend:8.1f}")

    r = local_critical_stress(150.0, T, boundary="ss_free")
    print(f"\nlocal_critical_stress(150, 2, 'ss_free') → σ_cr = {r.sigma_cr_MPa:.2f} MPa, k = {r.k}, "
          f"b/t = {r.slenderness:.0f}, método: {r.method}")
    print("Comparación con f_y = 350 MPa: por encima de la fila con σ_cr < 350 la placa pandea antes de plastificar.")


if __name__ == "__main__":
    main()
