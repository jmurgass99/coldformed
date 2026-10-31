"""Reducciones por perforaciones del alma (AISI §1.1.2 / EN 1993-1-3) y por galvanizado.

Montante de 150 mm de alma y 1,5 mm con huecos de servicio de 40 mm cada 300 mm:
área neta, factor de reducción y avisos según AISI y según EN (que añade el factor
k_w = 1 − 0,9·d/w + 0,4·(d/w)²). Después se aplica la reducción a una P_n de 90 kN y
se muestra el límite elástico ajustado por el proceso de recubrimiento y el espesor
mínimo de zinc según EN ISO 1461.

Ejecutar:  python examples/perforated_web_and_galvanized_yield_reductions.py
"""
from coldformed.galvanizing import adjusted_yield, coating_thickness_required_iso1461
from coldformed.perforations import HoleSpec, Pn_with_holes, reduce_for_holes

PN_SOLID = 90.0


def main() -> None:
    for d, s in ((40.0, 300.0), (40.0, 600.0), (100.0, 300.0)):
        spec = HoleSpec(diameter_mm=d, n_holes=1, web_width_mm=150.0, thickness_mm=1.5, spacing_mm=s)
        print(f"Hueco d = {d:.0f} mm, separación {s:.0f} mm (d/w = {d / 150:.2f}):")
        for code in ("AISI", "EN"):
            r = reduce_for_holes(spec, code=code)
            print(f"  {code:<5} A_bruta = {r.A_gross_mm2:.0f}, A_neta = {r.A_net_mm2:.0f} mm², factor = {r.reduction_factor:.3f}, "
                  f"P_n = {Pn_with_holes(PN_SOLID, spec, code):.1f} kN  {list(r.warnings) if r.warnings else ''}")

    print("\nLímite elástico ajustado por recubrimiento (f_y = 350 MPa):")
    for proc in ("hot_dip_galvanized", "electrogalvanized", "aluminized", "duplex", "painted"):
        print(f"  {proc:<20} f_y,adj = {adjusted_yield(350.0, proc):.1f} MPa")
    print("\nEspesor mínimo de zinc EN ISO 1461:")
    for t in (1.2, 2.0, 4.0, 8.0):
        print(f"  t = {t} mm → {coating_thickness_required_iso1461(t)} μm")


if __name__ == "__main__":
    main()
