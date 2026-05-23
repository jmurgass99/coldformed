"""Wrapper sectionproperties para perfiles arbitrarios.

Proporciona propiedades geometricas (Ag, Ix, Iy, J, Zx_pl, Zy_pl, rx, ry,
cw, x_c, y_c, ...) para perfiles definidos por poligono. Complementa el
class4_evaluator existente que asume formas estandar.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field

try:
    from sectionproperties.pre.geometry import Geometry
    try:
        from sectionproperties.pre.library.standard_sections import (
            i_section, channel_section, rectangular_hollow_section,
        )
    except ImportError:
        from sectionproperties.pre.library.steel_sections import (
            i_section, channel_section, rectangular_hollow_section,
        )
    from sectionproperties.analysis.section import Section
    _HAS_SECTPROPS = True
except ImportError:
    _HAS_SECTPROPS = False

log = logging.getLogger("coldformedjm.sectprops_wrapper")


@dataclass
class SectionProperties:
    """Propiedades geometricas calculadas por sectionproperties."""
    name: str
    area_mm2: float
    Ixx_mm4: float           # momento inercia eje fuerte
    Iyy_mm4: float           # momento inercia eje debil
    J_torsion_mm4: float      # constante torsional
    Cw_warping_mm6: float     # constante alabeo
    Zxx_plastic_mm3: float    # modulo plastico fuerte
    Zyy_plastic_mm3: float    # modulo plastico debil
    rxx_mm: float             # radio de giro
    ryy_mm: float
    x_centroid_mm: float
    y_centroid_mm: float
    notes: list[str] = field(default_factory=list)


def _build_section_from_geometry(geom):
    """Mesh + analisis estandar."""
    geom.create_mesh(mesh_sizes=10.0)
    sec = Section(geometry=geom)
    sec.calculate_geometric_properties()
    sec.calculate_warping_properties()
    sec.calculate_plastic_properties()
    return sec


def analyze_i_section(d, b, tf, tw, name="custom_I"):
    """Perfil I custom (cold-formed o laminado).

    Args:
        d: peralte total (mm)
        b: ancho ala (mm)
        tf: espesor ala (mm)
        tw: espesor alma (mm)
    """
    if not _HAS_SECTPROPS:
        raise ImportError("sectionproperties no instalado")
    if any(v <= 0 for v in (d, b, tf, tw)):
        raise ValueError("dimensiones deben ser positivas")
    if d <= 2 * tf:
        raise ValueError("d debe ser > 2*tf")

    geom = i_section(d=d, b=b, t_f=tf, t_w=tw, r=0, n_r=1)
    sec = _build_section_from_geometry(geom)

    return SectionProperties(
        name=name,
        area_mm2=float(sec.get_area()),
        Ixx_mm4=float(sec.get_ic()[0]),
        Iyy_mm4=float(sec.get_ic()[1]),
        J_torsion_mm4=float(sec.get_j()),
        Cw_warping_mm6=float(sec.get_gamma()),
        Zxx_plastic_mm3=float(sec.get_s()[0]),
        Zyy_plastic_mm3=float(sec.get_s()[1]),
        rxx_mm=float(sec.get_rc()[0]),
        ryy_mm=float(sec.get_rc()[1]),
        x_centroid_mm=float(sec.get_c()[0]),
        y_centroid_mm=float(sec.get_c()[1]),
        notes=[
            f"I-section d={d:.0f} b={b:.0f} tf={tf:.1f} tw={tw:.1f} mm",
            f"Area = {sec.get_area():.0f} mm2",
            f"Ixx = {sec.get_ic()[0]/1e6:.1f} x10^6 mm4",
        ],
    )


def analyze_channel_section(d, b, tf, tw, name="custom_C"):
    """Perfil C (cold-formed channel)."""
    if not _HAS_SECTPROPS:
        raise ImportError("sectionproperties no instalado")
    if any(v <= 0 for v in (d, b, tf, tw)):
        raise ValueError("dimensiones deben ser positivas")

    geom = channel_section(d=d, b=b, t_f=tf, t_w=tw, r=0, n_r=1)
    sec = _build_section_from_geometry(geom)

    return SectionProperties(
        name=name,
        area_mm2=float(sec.get_area()),
        Ixx_mm4=float(sec.get_ic()[0]),
        Iyy_mm4=float(sec.get_ic()[1]),
        J_torsion_mm4=float(sec.get_j()),
        Cw_warping_mm6=float(sec.get_gamma()),
        Zxx_plastic_mm3=float(sec.get_s()[0]),
        Zyy_plastic_mm3=float(sec.get_s()[1]),
        rxx_mm=float(sec.get_rc()[0]),
        ryy_mm=float(sec.get_rc()[1]),
        x_centroid_mm=float(sec.get_c()[0]),
        y_centroid_mm=float(sec.get_c()[1]),
        notes=[
            f"Channel d={d:.0f} b={b:.0f} tf={tf:.1f} tw={tw:.1f} mm",
            f"Area = {sec.get_area():.0f} mm2",
        ],
    )


def analyze_hollow_rect_section(d, b, t, name="custom_HSS"):
    """HSS rectangular (Hollow Structural Section)."""
    if not _HAS_SECTPROPS:
        raise ImportError("sectionproperties no instalado")
    if any(v <= 0 for v in (d, b, t)):
        raise ValueError("dimensiones deben ser positivas")
    if t >= min(d, b) / 2:
        raise ValueError("espesor t excede la mitad de la dimension")

    geom = rectangular_hollow_section(d=d, b=b, t=t, r_out=0, n_r=1)
    sec = _build_section_from_geometry(geom)

    return SectionProperties(
        name=name,
        area_mm2=float(sec.get_area()),
        Ixx_mm4=float(sec.get_ic()[0]),
        Iyy_mm4=float(sec.get_ic()[1]),
        J_torsion_mm4=float(sec.get_j()),
        Cw_warping_mm6=float(sec.get_gamma()),
        Zxx_plastic_mm3=float(sec.get_s()[0]),
        Zyy_plastic_mm3=float(sec.get_s()[1]),
        rxx_mm=float(sec.get_rc()[0]),
        ryy_mm=float(sec.get_rc()[1]),
        x_centroid_mm=float(sec.get_c()[0]),
        y_centroid_mm=float(sec.get_c()[1]),
        notes=[
            f"HSS d={d:.0f} b={b:.0f} t={t:.1f} mm",
            f"Area = {sec.get_area():.0f} mm2",
        ],
    )
