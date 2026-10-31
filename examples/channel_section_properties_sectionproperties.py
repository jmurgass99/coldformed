"""Propiedades geométricas de un canal con `sectionproperties`: área, inercias, J, C_w, módulos plásticos.

`analyze_channel_section` malla la sección y devuelve un `SectionProperties` con las
propiedades que necesita el DSM (módulos, radios de giro) y la torsión (J, C_w). Canal
200x75 con alas y alma de 3 mm, comparado con el canal 250x80 del catálogo. La malla
tarda unos segundos.

Ejecutar:  python examples/channel_section_properties_sectionproperties.py
"""
from coldformed.sectprops_wrapper import analyze_channel_section


def main() -> None:
    for d, b, t in ((200.0, 75.0, 3.0), (250.0, 80.0, 2.5)):
        p = analyze_channel_section(d=d, b=b, tf=t, tw=t, name=f"C{d:.0f}x{b:.0f}x{t}")
        print(f"{p.name}: A = {p.area_mm2:.0f} mm², I_xx = {p.Ixx_mm4:.3e} mm⁴, I_yy = {p.Iyy_mm4:.3e} mm⁴")
        print(f"  J = {p.J_torsion_mm4:.1f} mm⁴, C_w = {p.Cw_warping_mm6:.3e} mm⁶, "
              f"Z_xx,pl = {p.Zxx_plastic_mm3:.3e} mm³, r_xx = {p.rxx_mm:.1f} mm, r_yy = {p.ryy_mm:.1f} mm")
        print(f"  centroide: x = {p.x_centroid_mm:.1f} mm, y = {p.y_centroid_mm:.1f} mm  {p.notes if p.notes else ''}\n")


if __name__ == "__main__":
    main()
