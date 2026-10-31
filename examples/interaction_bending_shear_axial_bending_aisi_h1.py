"""Interacción flexión-cortante y axil-flexión (AISI S100-16 §H1) con capacidades del propio paquete.

Correa C 200x65x20x2 (S350): la capacidad a flexión sale del DSM distorsional (φ_b·M_n),
la de cortante de §G2 (φ_v = 0,95 aplicado aquí) y la de compresión de φ_c·P_n. Se
comprueban tres combinaciones de esfuerzos en el apoyo interior (M y V altos) y en
un montante comprimido con flexión por excentricidad. El ratio ≤ 1 cumple.

Ejecutar:  python examples/interaction_bending_shear_axial_bending_aisi_h1.py
"""
from coldformed.distortional import SectionGeometryCZ, aisi_distortional_buckling
from coldformed.interaction import axial_bending, bending_shear
from coldformed.shear import ShearInput, shear_capacity

SEC = SectionGeometryCZ(h_mm=200.0, b_mm=65.0, lip_mm=20.0, t_mm=2.0, shape="C")
FY = 350.0


def main() -> None:
    d = aisi_distortional_buckling(SEC, Fy_MPa=FY)
    v = shear_capacity(ShearInput(h_mm=SEC.h_mm - 2 * SEC.t_mm, t_mm=SEC.t_mm, Fy_MPa=FY))
    M_cap, V_cap, P_cap = d.phi_b_Mn_kNm, 0.95 * v.Vn_kN, d.phi_c_Pn_kN
    print(f"Capacidades de diseño: φM_n = {M_cap:.2f} kN·m, φV_n = {V_cap:.2f} kN, φP_n = {P_cap:.1f} kN\n")

    print("Flexión + cortante (§H1.1, circular):")
    for M, V in ((6.0, 10.0), (9.0, 14.0), (11.0, 18.0)):
        r = bending_shear(M, M_cap, V, V_cap)
        print(f"  M = {M:5.1f} kN·m, V = {V:5.1f} kN → ratio = {r.ratio:.3f} {'OK' if r.ok else 'NO'}  [{r.equation}]")

    print("\nAxil + flexión (§H1.2, lineal):")
    for P, M in ((20.0, 3.0), (40.0, 5.0), (60.0, 6.0)):
        r = axial_bending(P, P_cap, M, M_cap)
        print(f"  P = {P:5.1f} kN, M = {M:4.1f} kN·m → ratio = {r.ratio:.3f} {'OK' if r.ok else 'NO'}  [{r.equation}]")


if __name__ == "__main__":
    main()
