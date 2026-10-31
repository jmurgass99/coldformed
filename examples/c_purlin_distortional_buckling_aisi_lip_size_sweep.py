"""Pandeo distorsional de una correa en C conformada en frío (AISI S100 DSM).

Se parte de una sección C 200x60x20x2 (alma x ala x labio x espesor, en mm),
se comprueban los límites de aplicabilidad del DSM y de EN 1993-1-3 y se
calcula el pandeo distorsional según AISI. Después se estudia cómo cambia el
resultado con el tamaño del labio rigidizador.

Ejecutar:  python examples/02_distortional_buckling_c_section.py
"""
from dataclasses import asdict

from coldformed.distortional import (
    SectionGeometryCZ,
    aisi_distortional_buckling,
    check_aisi_dsm_applicability,
    check_ec3_applicability,
)

FY = 350.0


def main() -> None:
    sec = SectionGeometryCZ(h_mm=200.0, b_mm=60.0, lip_mm=20.0, t_mm=2.0, shape="C")

    ok_aisi, notes_aisi = check_aisi_dsm_applicability(sec, FY)
    ok_ec3, notes_ec3 = check_ec3_applicability(sec, FY)
    print(f"Sección C {sec.h_mm:.0f}x{sec.b_mm:.0f}x{sec.lip_mm:.0f}x{sec.t_mm:.1f}, f_y = {FY:.0f} MPa")
    print(f"  Aplicabilidad DSM (AISI S100): {'sí' if ok_aisi else 'NO'} {notes_aisi}")
    print(f"  Aplicabilidad EN 1993-1-3:     {'sí' if ok_ec3 else 'NO'} {notes_ec3}\n")

    res = aisi_distortional_buckling(sec, Fy_MPa=FY)
    print("Pandeo distorsional AISI S100:")
    for k, v in asdict(res).items():
        print(f"  {k:<28} {v}")

    print("\nEfecto del labio rigidizador:")
    print(f"  {'labio [mm]':>10} | resultado")
    for lip in (10.0, 15.0, 20.0, 25.0, 30.0):
        s = SectionGeometryCZ(h_mm=200.0, b_mm=60.0, lip_mm=lip, t_mm=2.0, shape="C")
        r = aisi_distortional_buckling(s, Fy_MPa=FY)
        d = asdict(r)
        # se imprimen las dos primeras magnitudes numéricas del resultado
        nums = [f"{k} = {v:.4g}" for k, v in d.items() if isinstance(v, (int, float))][:3]
        print(f"  {lip:10.0f} | " + ", ".join(nums))


if __name__ == "__main__":
    main()
