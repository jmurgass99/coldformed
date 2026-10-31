"""
Bridge ColdFormed → SAP Section Designer.

Genera el payload de polígono cerrado a partir de un perfil arbitrario
para enviarlo via fastsap.OAPI (`SetSDSection`).

Soporta:
- C-section (canal)
- Z-section
- Sigma section (perfil sigma cold-formed)
- Custom polygon definido por puntos
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin
from typing import Any


@dataclass(frozen=True)
class CFShape:
    name: str
    points_mm: list[tuple[float, float]]
    thickness_mm: float
    material: str = "S350"

    def to_sap_dict(self) -> dict[str, Any]:
        """Diccionario listo para fastsap.OAPI.SDSection.SetByPoints."""
        return {
            "name": self.name,
            "material": self.material,
            "polygon": [(round(x, 3), round(y, 3))
                        for x, y in self.points_mm],
            "thickness_mm": self.thickness_mm,
        }


def channel(h: float, b: float, t: float, lip: float = 0.0, name: str = "C") -> CFShape:
    """Perfil C (canal con o sin pestaña/labio) cold-formed."""
    if lip <= 0.0:
        pts = [
            (0, 0), (b, 0), (b, t), (t, t),
            (t, h - t), (b, h - t), (b, h), (0, h),
        ]
    else:
        pts = [
            (0, 0), (b, 0), (b, lip), (b - t, lip), (b - t, t), (t, t),
            (t, h - t), (b - t, h - t), (b - t, h - lip), (b, h - lip),
            (b, h), (0, h),
        ]
    return CFShape(name=name, points_mm=pts, thickness_mm=t)


def z_section(h: float, b_top: float, b_bot: float, t: float,
              lip_top: float = 0.0, lip_bot: float = 0.0,
              name: str = "Z") -> CFShape:
    """Perfil Z (alas opuestas con o sin pestaña/labio)."""
    if lip_top <= 0.0 and lip_bot <= 0.0:
        pts = [
            (-b_bot, 0), (0, 0), (0, h), (b_top, h),
            (b_top, h - t), (t, h - t), (t, t),
            (-b_bot, t),
        ]
    else:
        pts = [
            (-b_bot, lip_bot), (-b_bot, 0), (0, 0), (0, h),
            (b_top, h), (b_top, h - lip_top), (b_top - t, h - lip_top),
            (b_top - t, h - t), (t, h - t), (t, t),
            (-b_bot + t, t), (-b_bot + t, lip_bot),
        ]
    return CFShape(name=name, points_mm=pts, thickness_mm=t)


def sigma_section(h: float, b: float, lip: float, t: float,
                   name: str = "Σ") -> CFShape:
    """Perfil sigma cold-formed con labios."""
    pts = [
        (0, 0), (b, 0), (b, lip),
        (b - t, lip), (b - t, t),
        (t, t), (t, h/2 - t), (b/2, h/2 - t),
        (b/2, h/2 + t), (t, h/2 + t), (t, h - t),
        (b - t, h - t), (b - t, h - lip),
        (b, h - lip), (b, h), (0, h),
    ]
    return CFShape(name=name, points_mm=pts, thickness_mm=t)


def push_to_sap(sap, shape: CFShape) -> bool:
    """Envía la sección a SAP Section Designer vía OAPI.

    Si OAPI no está disponible (mock), devuelve False sin levantar.
    """
    try:
        from fastsap import sections  # type: ignore
        sections.create_sd_section_from_points(
            sap, shape.name, shape.to_sap_dict(),
        )
        return True
    except Exception:
        return False


__all__ = ["CFShape", "channel", "z_section", "sigma_section", "push_to_sap"]
