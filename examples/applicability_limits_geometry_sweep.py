"""Límites de aplicabilidad de perfiles C y Z: AISI S100 Tabla B4.1-1 frente a EN 1993-1-3 Tabla 5.1.

Antes de calcular, cada norma exige que la geometría esté dentro de su campo de
validación: h/t ≤ 200 (AISI) o ≤ 500 (EC3), b/t ≤ 60, c/t ≤ 50, labio presente,
f_y ≤ 550 MPa, y rangos recomendados de h/b y c/b. Se prueban seis geometrías,
algunas a propósito fuera de rango, y se listan los avisos de cada método.

Ejecutar:  python examples/applicability_limits_geometry_sweep.py
"""
from coldformed.distortional import SectionGeometryCZ, check_aisi_dsm_applicability, check_ec3_applicability

CASES = [
    ("C 200x60x20x2,0 (habitual)", SectionGeometryCZ(200, 60, 20, 2.0, "C"), 350.0),
    ("C 300x60x15x1,2 (alma muy esbelta)", SectionGeometryCZ(300, 60, 15, 1.2, "C"), 350.0),
    ("C 150x90x10x1,5 (ala ancha, labio corto)", SectionGeometryCZ(150, 90, 10, 1.5, "C"), 350.0),
    ("Z 250x75x25x2,5", SectionGeometryCZ(250, 75, 25, 2.5, "Z"), 350.0),
    ("C 200x60x0x2,0 (sin labio)", SectionGeometryCZ(200, 60, 0.0, 2.0, "C"), 350.0),
    ("C 200x60x20x2,0 en f_y = 600", SectionGeometryCZ(200, 60, 20, 2.0, "C"), 600.0),
]


def main() -> None:
    for name, sec, fy in CASES:
        ok_a, notes_a = check_aisi_dsm_applicability(sec, fy)
        ok_e, notes_e = check_ec3_applicability(sec, fy)
        print(f"{name}: h/t = {sec.h_t:.0f}, b/t = {sec.b_t:.0f}, c/t = {sec.lip_t:.0f}, h/b = {sec.h_b:.2f}, c/b = {sec.lip_b:.2f}")
        print(f"   AISI DSM  {'válido' if ok_a else 'NO válido'}: {notes_a if notes_a else 'sin avisos'}")
        print(f"   EN 1993-1-3 {'válido' if ok_e else 'NO válido'}: {notes_e if notes_e else 'sin avisos'}")


if __name__ == "__main__":
    main()
