"""Servicio FSM para ColdFormed."""
from __future__ import annotations

from ..fsm import (
    PlateBucklingInput,
    PlateBucklingResult,
    plate_critical_stress,
)


def evaluate_plate_buckling(data: PlateBucklingInput) -> PlateBucklingResult:
    return plate_critical_stress(data)


__all__ = ["PlateBucklingInput", "PlateBucklingResult", "evaluate_plate_buckling"]
