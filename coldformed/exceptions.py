"""Jerarquia de excepciones de ColdFormed.

Todas las excepciones del paquete heredan de :class:`ColdFormedError` para
facilitar el manejo agrupado por consumidores externos (REST, CLI, GUI).
"""
from __future__ import annotations


class ColdFormedError(Exception):
    """Excepcion base para todos los errores del paquete ColdFormed."""


class ValidationError(ColdFormedError):
    """Error de validacion de datos de entrada (geometria o material)."""


class GeometryError(ValidationError):
    """Error especifico de geometria invalida (dimensiones <= 0, etc.)."""


class MaterialError(ValidationError):
    """Error especifico de propiedades de material invalidas (f_y <= 0)."""
