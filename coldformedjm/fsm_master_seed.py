"""FSM seed integrado desde Master_IEG_Integrations/cold_formed_fsm.py.

Motor minimo para pandeo elastico local de placas (Bryan / Timoshenko).
La version completa con multiples franjas y conectividad transversal vive
en `coldformedjm.fsm`; este modulo conserva la API "seed" de IEG 3120 para
uso docente / quick-look y como referencia historica de integracion.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np


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
    """FSM-base (IEG 3120) para Class 4 cold-formed. Ver `fsm.py` para version full."""

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

    def build_geometric_stiffness_matrix(self, strip_nodes: List[float]) -> np.ndarray:
        """Stub: matriz K_G placeholder hasta integracion con `fsm.py` completo."""
        # TODO: integrar con coldformedjm.fsm.build_geometric_stiffness_matrix
        return np.eye(4)


__all__ = ["FiniteStripMethodSeed"]
