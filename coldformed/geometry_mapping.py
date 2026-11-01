"""Mapeo semántico -> malla de franjas finitas (``StripGeometryMapping``):
``corner_to_nodes`` y ``wall_to_strips`` para secciones C/Z conformadas en frío.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class StripGeometryMapping:
    """Mapeo entre esquinas/paredes semánticas y nudos/franjas discretas FSM."""

    corner_to_nodes: Dict[str, int] = field(default_factory=dict)
    wall_to_strips: Dict[str, List[int]] = field(default_factory=dict)
    nodes_yz_mm: List[Tuple[float, float]] = field(default_factory=list)
    strips: List[Tuple[int, int, float]] = field(default_factory=list)


def build_lipped_c_strip_mesh(
    h_mm: float = 200.0,
    b_mm: float = 75.0,
    c_lip_mm: float = 20.0,
    t_mm: float = 2.0,
    divisions_per_wall: int = 4,
) -> StripGeometryMapping:
    """Subdivide las 5 paredes de un perfil C rigidizado (labio inferior, ala inferior,
    alma, ala superior, labio superior) en ``divisions_per_wall`` franjas finitas.
    """
    n_div = max(1, int(divisions_per_wall))
    half_h = 0.5 * h_mm
    corners: List[Tuple[str, Tuple[float, float]]] = [
        ("bot_lip_tip", (b_mm, -half_h + c_lip_mm)),
        ("bot_flange_lip", (b_mm, -half_h)),
        ("bot_web_flange", (0.0, -half_h)),
        ("top_web_flange", (0.0, half_h)),
        ("top_flange_lip", (b_mm, half_h)),
        ("top_lip_tip", (b_mm, half_h - c_lip_mm)),
    ]
    wall_names = ["bottom_lip", "bottom_flange", "web", "top_flange", "top_lip"]

    corner_to_nodes: Dict[str, int] = {}
    wall_to_strips: Dict[str, List[int]] = {}
    nodes_yz_mm: List[Tuple[float, float]] = []
    strips: List[Tuple[int, int, float]] = []

    corner_to_nodes[corners[0][0]] = 0
    nodes_yz_mm.append(corners[0][1])

    for w_idx, w_name in enumerate(wall_names):
        _, c_start = corners[w_idx]
        c_end_name, c_end = corners[w_idx + 1]
        s_ids: List[int] = []
        for k in range(1, n_div + 1):
            alpha = k / float(n_div)
            pt = (
                round(c_start[0] + alpha * (c_end[0] - c_start[0]), 5),
                round(c_start[1] + alpha * (c_end[1] - c_start[1]), 5),
            )
            n_prev = len(nodes_yz_mm) - 1
            nodes_yz_mm.append(pt)
            n_curr = len(nodes_yz_mm) - 1
            s_ids.append(len(strips))
            strips.append((n_prev, n_curr, float(t_mm)))
        corner_to_nodes[c_end_name] = len(nodes_yz_mm) - 1
        wall_to_strips[w_name] = s_ids

    return StripGeometryMapping(
        corner_to_nodes=corner_to_nodes,
        wall_to_strips=wall_to_strips,
        nodes_yz_mm=nodes_yz_mm,
        strips=strips,
    )
