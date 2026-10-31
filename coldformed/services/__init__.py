"""Capa de servicios: funciones puras tipadas que envuelven la API existente."""
from .section_service import (
    SectionInput,
    SectionResult,
    evaluate_section,
)
from .fsm_service import (
    PlateBucklingInput,
    PlateBucklingResult,
    evaluate_plate_buckling,
)

__all__ = [
    "SectionInput",
    "SectionResult",
    "evaluate_section",
    "PlateBucklingInput",
    "PlateBucklingResult",
    "evaluate_plate_buckling",
]
