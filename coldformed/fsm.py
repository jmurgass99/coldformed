"""
Finite Strip Method (FSM) — motor base para pandeo elástico local y
distorsional en perfiles conformados en frío Clase 4.

Cubre la solución cerrada para placas (esfuerzo crítico de Euler para placas)
y el armado de la matriz de rigidez geométrica consistente K_G (flexión de
placa Hermite + membrana lineal en el plano) para una franja finita. El
ensamblado multi-franja con conectividad transversal y curva firma completa
vive en ``coldformed.fsm_assembly``.

Referencias:
    Schafer, B. W. (2008) — CUFSM and the Direct Strength Method.
    Hancock, G.J. (2006) — Cold-Formed Steel Structures, 4th ed.
    Eurocódigo EN 1993-1-5 §4 — placas comprimidas.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np


# ----------------------------------------------------------------------
# Esfuerzo crítico de placa (Bryan 1891 / Timoshenko)
# ----------------------------------------------------------------------

PLATE_K = {
    "ss_ss": 4.0,        # apoyada-apoyada (alma común)
    "ss_free": 0.425,    # apoyada-libre (ala outstand)
    "cc": 6.97,          # empotrada-empotrada
    "cs": 5.42,          # empotrada-apoyada
}


@dataclass(frozen=True)
class PlateBucklingInput:
    width_mm: float
    thickness_mm: float
    E_MPa: float = 210_000.0
    nu: float = 0.30
    boundary: str = "ss_ss"  # ver PLATE_K
    k_override: float | None = None  # k del usuario (rompe el lookup)

    def validate(self) -> None:
        if self.width_mm <= 0:
            raise ValueError("width_mm debe ser > 0")
        if self.thickness_mm <= 0:
            raise ValueError("thickness_mm debe ser > 0")
        if self.E_MPa <= 0:
            raise ValueError("E_MPa debe ser > 0")
        if not (0 < self.nu < 0.5):
            raise ValueError("nu debe estar en (0, 0.5)")
        if self.k_override is None and self.boundary not in PLATE_K:
            raise ValueError(
                f"boundary '{self.boundary}' no reconocido; "
                f"válidos: {sorted(PLATE_K)}"
            )


@dataclass(frozen=True)
class PlateBucklingResult:
    sigma_cr_MPa: float
    k: float
    D_Nmm: float           # rigidez flexional D = E·t³/(12(1-ν²)) [N·mm]
    slenderness: float     # esbeltez de placa λ_p
    method: str = "Bryan/Timoshenko — placa simple"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sigma_cr_MPa": self.sigma_cr_MPa,
            "k": self.k,
            "D_Nmm": self.D_Nmm,
            "slenderness": self.slenderness,
            "method": self.method,
        }


def plate_critical_stress(data: PlateBucklingInput) -> PlateBucklingResult:
    """σ_cr = k·π²·E / (12·(1-ν²))·(t/b)² — solución clásica (placa simple)."""
    data.validate()
    k = data.k_override if data.k_override is not None else PLATE_K[data.boundary]
    D = data.E_MPa * data.thickness_mm ** 3 / (12.0 * (1.0 - data.nu ** 2))
    sigma_cr = (k * pi ** 2 * D) / (data.width_mm ** 2 * data.thickness_mm)
    slenderness = data.width_mm / data.thickness_mm
    return PlateBucklingResult(
        sigma_cr_MPa=sigma_cr, k=k, D_Nmm=D, slenderness=slenderness,
    )


# ----------------------------------------------------------------------
# K_G de una franja FSM (semi-analítica, modo m=1, half-wavelength dado)
# ----------------------------------------------------------------------

def strip_geometric_stiffness(
    width: float,
    length: float,
    thickness: float,
    sigma_x: float,
    n_dof_per_node: int = 4,
    include_membrane: bool = True,
) -> np.ndarray:
    """Matriz de rigidez geométrica K_G de una franja FSM (8 GDL: 4 flexión + 4 membrana).

    Modo longitudinal sinusoidal (m=1) en la semilongitud de onda ``length``,
    placa rectangular de ancho ``width`` y espesor ``thickness``, esfuerzo axial
    uniforme ``sigma_x`` (compresión positiva). Devuelve la K_G consistente para
    los 8 GDL de la franja: bloque ``[:4, :4]`` de flexión transversal Hermite
    ``[w_i, θ_i, w_j, θ_j]`` y bloque ``[4:, 4:]`` de membrana lineal
    ``[u_i, v_i, u_j, v_j]`` (Cheung 1976 / Schafer 2008 Eq. 26).

    Returns:
        K_G: array 8x8 simétrico.
    """
    if width <= 0 or length <= 0 or thickness <= 0:
        raise ValueError("width, length y thickness deben ser > 0")
    Nx = sigma_x * thickness  # fuerza por unidad de longitud
    b = width
    L = length

    # Bloque de flexión transversal w (4×4) — Hermite cúbico.
    kg_w = (Nx * b / (420.0 * L)) * np.array([
        [156.0,  22.0 * b,   54.0, -13.0 * b],
        [ 22.0 * b,   4.0 * b * b,  13.0 * b, -3.0 * b * b],
        [ 54.0,  13.0 * b,  156.0, -22.0 * b],
        [-13.0 * b, -3.0 * b * b, -22.0 * b,   4.0 * b * b],
    ])

    # Bloque de membrana (u_i, v_i, u_j, v_j) con funciones de forma lineales (1 - y/b, y/b):
    if include_membrane:
        kg_uv = (Nx * b / (6.0 * L)) * np.array([
            [2.0, 0.0, 1.0, 0.0],
            [0.0, 2.0, 0.0, 1.0],
            [1.0, 0.0, 2.0, 0.0],
            [0.0, 1.0, 0.0, 2.0],
        ])
    else:
        kg_uv = np.zeros((4, 4))

    n = 2 * n_dof_per_node  # 8
    KG = np.zeros((n, n))
    KG[:4, :4] = kg_w
    if n >= 8:
        KG[4:8, 4:8] = kg_uv
    return KG


# ----------------------------------------------------------------------
# Solver de autovalor de pandeo
# ----------------------------------------------------------------------

def solve_buckling_eigenvalue(K_E: np.ndarray, K_G: np.ndarray
                              ) -> tuple[float, np.ndarray]:
    """Resuelve ``(K_E - λ·K_G)·φ = 0`` y devuelve el menor autovalor positivo.

    Args:
        K_E: matriz de rigidez elástica.
        K_G: matriz de rigidez geométrica (signo: compresión positiva).

    Returns:
        (lambda_cr, mode): factor crítico de pandeo y modo asociado.
    """
    if K_E.shape != K_G.shape or K_E.ndim != 2:
        raise ValueError("K_E y K_G deben ser matrices cuadradas del mismo tamaño")
    from scipy.linalg import eig
    w, v = eig(K_E, K_G)
    w_real = w.real
    pos = w_real[np.isfinite(w_real) & (w_real > 0)]
    if pos.size == 0:
        raise RuntimeError("No se encontró autovalor positivo finito")
    idx = int(np.argmin(np.where(w_real > 0, w_real, np.inf)))
    return float(w_real[idx]), v[:, idx].real


# ----------------------------------------------------------------------
# Clase fachada
# ----------------------------------------------------------------------

class FiniteStripMethod:
    """Fachada del FSM con E y ν fijos para la sección bajo análisis."""

    def __init__(self, E_MPa: float = 210_000.0, nu: float = 0.30):
        if E_MPa <= 0 or not (0 < nu < 0.5):
            raise ValueError("E_MPa > 0 y nu en (0, 0.5)")
        self.E = E_MPa
        self.nu = nu
        self.G = E_MPa / (2.0 * (1.0 + nu))

    def plate_critical_stress(self, width: float, thickness: float,
                              k_factor: float = 4.0) -> float:
        """σ_cr de placa (compat seed). Para más detalle ver
        :func:`plate_critical_stress`."""
        res = plate_critical_stress(PlateBucklingInput(
            width_mm=width, thickness_mm=thickness,
            E_MPa=self.E, nu=self.nu, k_override=k_factor,
        ))
        return res.sigma_cr_MPa

    def strip_geometric_stiffness(self, width: float, length: float,
                                  thickness: float, sigma_x: float
                                  ) -> np.ndarray:
        """Wrapper de :func:`strip_geometric_stiffness`."""
        return strip_geometric_stiffness(width, length, thickness, sigma_x)


__all__ = [
    "PLATE_K",
    "PlateBucklingInput",
    "PlateBucklingResult",
    "plate_critical_stress",
    "strip_geometric_stiffness",
    "solve_buckling_eigenvalue",
    "FiniteStripMethod",
]
