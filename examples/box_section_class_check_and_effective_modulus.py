"""Clasificación y módulo eficaz de una sección cajón soldada para varios espesores de chapa.

`Class4Section` idealiza un cajón (o una I) por su ala b, su alma h y un espesor (o `t_f` y `t_w` distintos):
comprueba si alma o ala superan los límites de Clase 3 (124·ε para el alma en flexión,
42·ε para el ala) y, si la sección es Clase 4, reduce alma y ala con el factor ρ de
Winter (ψ = −1 y k_σ = 23,9 en el alma; ψ = +1 y k_σ = 4 en el ala) para obtener un
módulo resistente eficaz aproximado. El servicio `evaluate_section` envuelve lo mismo
con validación y resultado serializable.

Ejecutar:  python examples/box_section_class_check_and_effective_modulus.py
"""
from coldformed.class4_evaluator import Class4Section
from coldformed.services.section_service import SectionInput, evaluate_section

B, H, FY = 400.0, 1000.0, 355.0


def main() -> None:
    print(f"Cajón b = {B:.0f} mm, h = {H:.0f} mm, S{FY:.0f} (ε = {(235 / FY) ** 0.5:.3f}, "
          f"límites Clase 3: alma {124 * (235 / FY) ** 0.5:.1f}, ala {42 * (235 / FY) ** 0.5:.1f})\n")
    print(f"{'t [mm]':>7} {'h/t':>7} {'b/t':>6} {'clase':>6} {'W_eff [cm³]':>12}")
    for t in (6.0, 8.0, 10.0, 12.0, 15.0, 20.0):
        s = Class4Section(b=B, h=H, t=t, f_y=FY)
        print(f"{t:7.1f} {H / t:7.1f} {B / t:6.1f} {s.check_class():6d} {s.calculate_effective_modulus():12.1f}")

    for tf, tw in ((8.0, 8.0), (15.0, 8.0), (8.0, 12.0)):
        s = Class4Section(b=B, h=H, t=8.0, f_y=FY, t_f=tf, t_w=tw)
        print(f"t_f = {tf:4.1f}, t_w = {tw:4.1f} mm → clase {s.check_class()}, W_eff = {s.calculate_effective_modulus():8.1f} cm³")

    res = evaluate_section(SectionInput(b=B, h=H, t=8.0, f_y=FY))
    print(f"\nServicio evaluate_section (t = 8 mm): {res.to_dict()}")
    try:
        evaluate_section(SectionInput(b=B, h=H, t=0.0, f_y=FY))
    except Exception as exc:          # GeometryError del paquete
        print(f"Entrada inválida (t = 0): {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
