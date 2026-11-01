"""FSM seed integrado desde Master_IEG_Integrations/cold_formed_fsm.py.

Motor para pandeo elastico local de placas (Bryan / Timoshenko) y matriz
de rigidez geometrica consistente de franja finita. La version multi-franja
con conectividad transversal vive en `coldformed.fsm_assembly`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np

from .fsm import strip_geometric_stiffness


def _bootstrap_sibling_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    if root.name != "APIS Structural JM":
        return
    siblings = [root / "_platform"]
    for s in siblings:
        if s.exists() and str(s) not in sys.path:
            sys.path.insert(0, str(s))


_bootstrap_sibling_paths()


class FiniteStripMethodSeed:
    """FSM-base (IEG 3120) para Class 4 cold-formed. Ver `fsm.py` y `fsm_assembly.py`."""

    def __init__(self, E: float = 200_000.0, nu: float = 0.3):
        self.E = E
        self.nu = nu
        self.G = E / (2.0 * (1.0 + nu))

    def calculate_plate_critical_stress(
        self, width: float, thickness: float, k_factor: float = 4.0,
    ) -> float:
        """Esfuerzo critico elastico de pandeo local de una placa simple [MPa].

        k_factor = 4.0 para placa simplemente apoyada.
        """
        D = (self.E * thickness ** 3) / (12.0 * (1.0 - self.nu ** 2))
        f_cr = (k_factor * np.pi ** 2 * D) / (width ** 2 * thickness)
        return float(f_cr)

    def build_geometric_stiffness_matrix(
        self,
        strip_nodes: List[float],
        thickness: float = 1.0,
        length: float = 100.0,
        sigma_x: float = 1.0,
    ) -> np.ndarray:
        """Calcula la matriz de rigidez geometrica consistente 4x4 (bloque Hermite
        de flexion transversal ``[w_i, theta_i, w_j, theta_j]``) para una franja
        definida por ``strip_nodes`` [mm] (ancho total ``b = max(strip_nodes) - min(strip_nodes)``).
        """
        if len(strip_nodes) < 2:
            raise ValueError("strip_nodes debe tener al menos 2 coordenadas nodales")
        b = float(max(strip_nodes) - min(strip_nodes))
        if b <= 0.0:
            raise ValueError("El ancho total de strip_nodes debe ser > 0")
        kg_8 = strip_geometric_stiffness(
            width=b, length=length, thickness=thickness, sigma_x=sigma_x,
        )
        return kg_8[:4, :4].copy()


__all__ = ["FiniteStripMethodSeed"]
