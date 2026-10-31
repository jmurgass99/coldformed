"""Tests minimos para fsm_master_seed (Master IEG seed)."""
from __future__ import annotations

import numpy as np

from coldformed.fsm_master_seed import FiniteStripMethodSeed


def test_plate_critical_stress_known_value():
    # Placa 200 mm x 2 mm, k=4, E=200000, nu=0.3 -> ~72.3 MPa (Bryan)
    fsm = FiniteStripMethodSeed()
    fcr = fsm.calculate_plate_critical_stress(width=200.0, thickness=2.0, k_factor=4.0)
    assert 60.0 < fcr < 90.0


def test_plate_critical_stress_thicker_is_higher():
    fsm = FiniteStripMethodSeed()
    f_thin = fsm.calculate_plate_critical_stress(200.0, 2.0)
    f_thick = fsm.calculate_plate_critical_stress(200.0, 4.0)
    assert f_thick > f_thin


def test_geometric_stiffness_matrix_shape():
    fsm = FiniteStripMethodSeed()
    K_G = fsm.build_geometric_stiffness_matrix([0.0, 50.0, 100.0])
    assert K_G.shape == (4, 4)
    assert np.allclose(K_G, np.eye(4))
