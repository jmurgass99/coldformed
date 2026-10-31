"""Del catálogo de perfiles al polígono para el Section Designer de SAP2000.

`profile_catalog` lista perfiles C, Z y Σ (AISI y EN 1993-1-3); `to_cf_shape` construye
el `CFShape` con los puntos de la línea media y `to_sap_dict` el diccionario que
consume `fastsap` para `SetSDSection`. Sin `fastsap` instalado, `push_to_sap` devuelve
False sin lanzar error, así que el paquete sigue siendo útil para generar la geometría.

Ejecutar:  python examples/catalogue_to_sap2000_section_designer_polygon.py
"""
from coldformed.profile_catalog import list_profiles, lookup, to_cf_shape
from coldformed.sap_section_bridge import push_to_sap


def main() -> None:
    print(f"{'perfil':<16} {'norma':<12} {'forma':<6} {'h':>5} {'b':>5} {'labio':>5} {'t':>4} {'kg/m':>6}")
    for p in list_profiles():
        print(f"{p.name:<16} {p.standard:<12} {p.shape:<6} {p.h_mm:5.0f} {p.b_mm:5.0f} {p.lip_mm:5.0f} {p.t_mm:4.1f} {p.mass_kg_per_m:6.2f}")

    shape = to_cf_shape("EN C200x80x25")
    d = shape.to_sap_dict()
    print(f"\n{shape.name}: {len(shape.points_mm)} puntos, t = {shape.thickness_mm} mm, material {shape.material}")
    print("  polígono (x, y) [mm]:", d["polygon"])
    print(f"  push_to_sap(None, shape) sin fastsap → {push_to_sap(None, shape)}")
    print(f"  lookup('no existe') → {lookup('no existe')}")


if __name__ == "__main__":
    main()
