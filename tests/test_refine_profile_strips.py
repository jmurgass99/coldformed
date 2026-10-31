"""refine_profile_strips: subdividir franjas baja el mínimo local hacia la solución de placa."""
from __future__ import annotations

import numpy as np
import pytest

from coldformed.fsm_assembly import build_profile_strips, compute_signature_curve_fsm, refine_profile_strips

DIMS = {"H": 200.0, "B": 60.0, "D": 20.0, "t": 2.0}


def test_counts_and_connectivity():
    base = build_profile_strips("C", DIMS)
    ref = refine_profile_strips(base, n_sub=4)
    assert ref.n_strips == 4 * base.n_strips
    assert ref.n_nodes == base.n_nodes + base.n_strips * 3
    assert sum(s.width_mm for s in ref.strips) == pytest.approx(sum(s.width_mm for s in base.strips))
    for s in ref.strips:
        i, j = s.connectivity
        (x0, y0), (x1, y1) = ref.node_coords[i], ref.node_coords[j]
        assert np.hypot(x1 - x0, y1 - y0) == pytest.approx(s.width_mm)


def test_n_sub_one_returns_same_object_and_invalid_raises():
    base = build_profile_strips("C", DIMS)
    assert refine_profile_strips(base, 1) is base
    with pytest.raises(ValueError):
        refine_profile_strips(base, 0)


def test_local_minimum_drops_with_refinement():
    base = build_profile_strips("C", DIMS)
    lams = np.logspace(np.log10(60.0), np.log10(400.0), 25)
    coarse = compute_signature_curve_fsm(base, np.ones(base.n_strips), lams).sigma_cr_MPa.min()
    fine = compute_signature_curve_fsm(refine_profile_strips(base, 4),
                                       np.ones(4 * base.n_strips), lams).sigma_cr_MPa.min()
    assert fine < coarse
    # cota: nunca por debajo del alma aislada apoyada-apoyada (k = 4, 200x2 → 75,9 MPa)
    assert fine > 75.0
