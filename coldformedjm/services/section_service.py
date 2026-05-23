"""Servicio de evaluacion de secciones Clase 4.

Envuelve :class:`coldformedjm.class4_evaluator.Class4Section` con funciones
puras tipadas, validacion y dataclasses serializables.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..exceptions import GeometryError, MaterialError


@dataclass(frozen=True)
class SectionInput:
    """Datos de entrada de la seccion."""

    b: float
    h: float
    t: float
    f_y: float = 355.0

    def validate(self) -> None:
        """Valida geometria y material; lanza excepciones del paquete."""
        for nombre, valor in (("b", self.b), ("h", self.h), ("t", self.t)):
            if valor <= 0:
                raise GeometryError(f"{nombre} debe ser > 0 (recibido {valor})")
        if self.f_y <= 0:
            raise MaterialError(f"f_y debe ser > 0 (recibido {self.f_y})")


@dataclass(frozen=True)
class SectionResult:
    """Resultado de la evaluacion de la seccion."""

    section_class: int
    epsilon: float
    w_eff_cm3: float

    def to_dict(self) -> dict[str, Any]:
        """Devuelve un diccionario serializable."""
        return asdict(self)


def evaluate_section(data: SectionInput) -> SectionResult:
    """Evalua una seccion Clase 4 y devuelve clase, epsilon y W_eff."""
    data.validate()
    # Lazy import para mantener ligero el modulo de servicios.
    from ..class4_evaluator import Class4Section

    section = Class4Section(b=data.b, h=data.h, t=data.t, f_y=data.f_y)
    return SectionResult(
        section_class=section.check_class(),
        epsilon=round(section.calculate_epsilon(), 6),
        w_eff_cm3=float(section.calculate_effective_modulus()),
    )
