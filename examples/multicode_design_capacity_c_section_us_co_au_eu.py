"""Capacidad de diseño de una correa C según AISI S100 (US, CO, AU) y EN 1993-1-3 (EU, SG).

`design_capacity_cz` separa los métodos: para US, CO y AU aplica el Método de la
Resistencia Directa de AISI (con φ_c = 0,85 y φ_b = 0,90); para EU y SG aplica el
método del ancho eficaz con rigidizador de borde de EN 1993-1-3 §5.5.3 (γ_M0 = 1,00).
Sección C 200x65x20x2,0 en S350, compresión y flexión. Las dos normas no dan el mismo
número porque no son el mismo método; la tabla deja ver la diferencia.

Ejecutar:  python examples/multicode_design_capacity_c_section_us_co_au_eu.py
"""
from coldformed.codes_multi import code_description, design_capacity_cz
from coldformed.distortional import SectionGeometryCZ

SEC = SectionGeometryCZ(h_mm=200.0, b_mm=65.0, lip_mm=20.0, t_mm=2.0, shape="C")
FY = 350.0


def main() -> None:
    print(f"C {SEC.h_mm:.0f}x{SEC.b_mm:.0f}x{SEC.lip_mm:.0f}x{SEC.t_mm:.1f}, f_y = {FY:.0f} MPa\n")
    for code in ("US", "CO", "AU", "EU", "SG"):
        print(f"{code}: {code_description(code)}")
        for loading in ("compression", "bending"):
            r = design_capacity_cz(code, SEC, Fy_MPa=FY, loading=loading)
            print(f"   {loading:<12} nominal = {r['nominal_capacity']:8.2f} {r['unit']:<4} "
                  f"diseño = {r['design_capacity']:8.2f} {r['unit']:<4} método: {r['method']}"
                  f"{'' if r['is_valid'] else '  (fuera de límites: ' + '; '.join(r['validity_notes']) + ')'}")


if __name__ == "__main__":
    main()
