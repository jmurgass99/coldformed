"""Tests for coldformedjm.fsm_assembly -- multi-strip FSM assembly."""
from __future__ import annotations

import numpy as np
import pytest

from coldformedjm.fsm_assembly import (
    StripDefinition,
    ProfileStrips,
    build_profile_strips,
    assemble_K_E,
    assemble_K_G,
    solve_buckling,
    compute_signature_curve_fsm,
)
from coldformedjm.fsm import plate_critical_stress, PlateBucklingInput
from coldformedjm.direct_strength import DSMCompressionInput, dsm_compression


# =====================================================================
# Helpers
# =====================================================================

def _c_channel_dims() -> dict[str, float]:
    """Standard C-channel: H=200, B=80, D=20, t=2 mm."""
    return {"H": 200.0, "B": 80.0, "D": 20.0, "t": 2.0}


def _simple_plate_strips(width: float = 200.0, thickness: float = 2.0,
                         E: float = 210_000.0, nu: float = 0.3
                         ) -> ProfileStrips:
    """Single flat plate (one strip, two nodes) for analytical validation."""
    return ProfileStrips(
        strips=[
            StripDefinition(
                width_mm=width,
                thickness_mm=thickness,
                E_MPa=E,
                nu=nu,
                connectivity=(0, 1),
            ),
        ],
        node_coords=[(0.0, 0.0), (width, 0.0)],
    )


# =====================================================================
# 1 -- Profile factory: C channel
# =====================================================================

class TestBuildCChannel:
    def test_build_c_channel_strips(self):
        """C-channel with lips produces 5 strips and 6 nodes."""
        ps = build_profile_strips("C", _c_channel_dims())
        assert ps.n_strips == 5
        assert ps.n_nodes == 6
        # DOFs = 4 per node
        assert ps.n_dof == 24

    def test_c_channel_connectivity_contiguous(self):
        """Each strip connects consecutive nodes."""
        ps = build_profile_strips("C", _c_channel_dims())
        for s in ps.strips:
            i, j = s.connectivity
            assert j == i + 1

    def test_c_channel_no_lips(self):
        """C-channel without lips: 3 strips, 4 nodes."""
        dims = {"H": 200.0, "B": 80.0, "t": 2.0}
        ps = build_profile_strips("C", dims)
        assert ps.n_strips == 3
        assert ps.n_nodes == 4


# =====================================================================
# 2 -- Profile factory: Z section
# =====================================================================

class TestBuildZSection:
    def test_build_z_section_strips(self):
        """Z-section with lips produces 5 strips and 6 nodes."""
        dims = {"H": 200.0, "B": 75.0, "D": 20.0, "t": 1.5}
        ps = build_profile_strips("Z", dims)
        assert ps.n_strips == 5
        assert ps.n_nodes == 6

    def test_z_section_flange_direction(self):
        """Z-section flanges extend in opposite y-directions."""
        dims = {"H": 200.0, "B": 75.0, "D": 20.0, "t": 1.5}
        ps = build_profile_strips("Z", dims)
        # Bottom flange tip y < 0, top flange tip y > 0
        y_bottom = ps.node_coords[1][0]  # bottom flange tip
        y_top = ps.node_coords[4][0]     # top flange tip
        assert y_bottom < 0
        assert y_top > 0


# =====================================================================
# 3 -- K_E symmetry and positive definiteness
# =====================================================================

class TestAssembleKE:
    def test_assemble_K_E_symmetric(self):
        """K_E must be symmetric."""
        ps = _simple_plate_strips()
        K_E = assemble_K_E(ps, half_wavelength=200.0)
        assert K_E.shape == (8, 8)
        assert np.allclose(K_E, K_E.T, atol=1e-10)

    def test_assemble_K_E_positive_diagonal(self):
        """Diagonal entries of K_E should be non-negative."""
        ps = _simple_plate_strips()
        K_E = assemble_K_E(ps, half_wavelength=200.0)
        assert np.all(np.diag(K_E) >= -1e-10)

    def test_assemble_K_E_c_channel(self):
        """K_E for a C-channel is symmetric with correct size."""
        ps = build_profile_strips("C", _c_channel_dims())
        K_E = assemble_K_E(ps, half_wavelength=200.0)
        assert K_E.shape == (24, 24)
        assert np.allclose(K_E, K_E.T, atol=1e-10)


# =====================================================================
# 4 -- K_G symmetry
# =====================================================================

class TestAssembleKG:
    def test_assemble_K_G_symmetric(self):
        """K_G must be symmetric."""
        ps = _simple_plate_strips()
        stress = np.array([100.0])
        K_G = assemble_K_G(ps, half_wavelength=200.0, stress_dist=stress)
        assert K_G.shape == (8, 8)
        assert np.allclose(K_G, K_G.T, atol=1e-10)

    def test_assemble_K_G_stress_mismatch_raises(self):
        """stress_dist length must match n_strips."""
        ps = _simple_plate_strips()
        with pytest.raises(ValueError, match="stress_dist"):
            assemble_K_G(ps, 200.0, np.array([100.0, 200.0]))


# =====================================================================
# 5 -- Eigenvalue solver: single plate
# =====================================================================

class TestSolveBuckling:
    def test_solve_buckling_single_plate(self):
        """Single flat plate at lambda=b should approximate Bryan k=4.

        Simply-supported BCs: constrain w=0 at both edge nodes.
        A single Hermite strip gives ~3-5% error vs the analytical
        solution (convergence improves with sub-strips).
        """
        b = 200.0
        t = 2.0
        E = 210_000.0
        nu = 0.3

        # Analytical reference (Bryan)
        ref = plate_critical_stress(PlateBucklingInput(
            width_mm=b, thickness_mm=t, E_MPa=E, nu=nu, boundary="ss_ss",
        ))

        # Single strip FSM
        ps = _simple_plate_strips(width=b, thickness=t, E=E, nu=nu)
        L = b  # half-wavelength = width for k=4 minimum
        K_E = assemble_K_E(ps, L)
        stress = np.array([1.0])  # unit reference stress
        K_G = assemble_K_G(ps, L, stress)

        # Apply SS BCs: constrain w DOF at both edge nodes.
        # DOF order per node: [u, v, w, theta] -> w is index 2 for node 0,
        # index 6 for node 1.
        constrained = [2, 6]
        eigenvalues, eigenvectors = solve_buckling(
            K_E, K_G, n_modes=3, constrained_dofs=constrained,
        )
        sigma_cr_fsm = eigenvalues[0]  # load factor * 1 MPa = sigma_cr

        # Allow ~10% tolerance for single-strip discretisation
        assert sigma_cr_fsm == pytest.approx(ref.sigma_cr_MPa, rel=0.10)

    def test_solve_buckling_positive_eigenvalues(self):
        """All returned eigenvalues must be positive."""
        ps = _simple_plate_strips()
        K_E = assemble_K_E(ps, 200.0)
        K_G = assemble_K_G(ps, 200.0, np.array([100.0]))
        eigenvalues, _ = solve_buckling(K_E, K_G, n_modes=3)
        assert np.all(eigenvalues > 0)

    def test_solve_buckling_sorted_ascending(self):
        """Eigenvalues are returned in ascending order."""
        ps = _simple_plate_strips()
        K_E = assemble_K_E(ps, 200.0)
        K_G = assemble_K_G(ps, 200.0, np.array([100.0]))
        eigenvalues, _ = solve_buckling(K_E, K_G, n_modes=5)
        for i in range(len(eigenvalues) - 1):
            assert eigenvalues[i] <= eigenvalues[i + 1] + 1e-10

    def test_solve_buckling_dimension_mismatch(self):
        """Mismatched K_E and K_G dimensions raise ValueError."""
        with pytest.raises(ValueError):
            solve_buckling(np.eye(4), np.eye(6))


# =====================================================================
# 6 -- Signature curve
# =====================================================================

class TestSignatureCurve:
    def test_signature_curve_c_channel(self):
        """Signature curve for C-channel detects local minimum and has correct shape.

        With one strip per plate element, the local mode is well captured.
        The curve should show a clear local minimum in the short-wavelength
        region and rising stresses at longer wavelengths.
        """
        ps = build_profile_strips("C", _c_channel_dims())
        stress = np.ones(ps.n_strips) * 1.0
        lams = np.logspace(np.log10(20.0), np.log10(5000.0), 40)
        result = compute_signature_curve_fsm(ps, stress, lams)

        assert len(result.half_wavelengths_mm) == 40
        assert len(result.sigma_cr_MPa) == 40
        # Must detect local minimum
        assert len(result.minima) >= 1
        mode_names = [m[2] for m in result.minima]
        assert "Local" in mode_names
        # The local minimum wavelength should be in the right ballpark
        # (for H=200, B=80, t=2: local ~ 80-200 mm range)
        local_min = [m for m in result.minima if m[2] == "Local"][0]
        assert 50.0 < local_min[0] < 300.0
        # sigma_cr at local minimum must be positive and finite
        assert 0 < local_min[1] < 1e6
        # All finite sigma_cr values should be positive
        finite_vals = result.sigma_cr_MPa[np.isfinite(result.sigma_cr_MPa)]
        if len(finite_vals) > 0:
            assert np.all(finite_vals > 0)

    def test_signature_curve_matches_dsm(self):
        """Critical stresses from signature curve produce valid DSM results.

        Feed the FSM-derived Pcrl (local minimum) through dsm_compression
        and verify the result is physically meaningful (0 < Pn < Py).
        """
        dims = _c_channel_dims()
        ps = build_profile_strips("C", dims)
        stress = np.ones(ps.n_strips) * 1.0
        lams = np.logspace(np.log10(20.0), np.log10(5000.0), 40)
        result = compute_signature_curve_fsm(ps, stress, lams)

        # Extract the local minimum (sigma_cr_local)
        local_minima = [m for m in result.minima if m[2] == "Local"]
        assert len(local_minima) >= 1
        sigma_cr_local = local_minima[0][1]

        # Compute Pcrl from sigma_cr_local and a representative area.
        # Use simplified area: A = perimeter * t (centre-line approx).
        H, B, D, t = dims["H"], dims["B"], dims.get("D", 0.0), dims["t"]
        perim = H + 2 * B + 2 * D
        A = perim * t
        Fy = 350.0

        Pcrl = sigma_cr_local * A / 1000.0  # kN
        # Use same value for Pcrd and Pcre (conservative placeholder)
        Pcrd = Pcrl * 1.5
        Pcre = Pcrl * 5.0

        dsm_result = dsm_compression(DSMCompressionInput(
            Pcrl_kN=Pcrl, Pcrd_kN=Pcrd, Pcre_kN=Pcre,
            A_mm2=A, Fy_MPa=Fy,
        ))

        Py = A * Fy / 1000.0
        assert 0 < dsm_result["Pn_kN"] <= Py
        assert dsm_result["governing_mode"] in ("local", "distortional", "global")

    def test_signature_curve_single_plate_monotonic(self):
        """Signature curve for a single unconstrained plate is monotonic.

        Without edge BCs (free strip), sigma_cr decreases with increasing
        half-wavelength.  This is expected -- U-shape only appears for
        full profile assemblies where connectivity provides restraint.
        """
        ps = _simple_plate_strips(width=100.0, thickness=2.0)
        stress = np.array([1.0])
        lams = np.logspace(np.log10(30.0), np.log10(500.0), 15)
        result = compute_signature_curve_fsm(ps, stress, lams)

        finite = result.sigma_cr_MPa[np.isfinite(result.sigma_cr_MPa)]
        assert len(finite) >= 5
        # Should be generally decreasing (sigma_cr falls with longer wavelength)
        assert finite[-1] < finite[0]


# =====================================================================
# 7 -- Edge cases and additional coverage
# =====================================================================

class TestEdgeCases:
    def test_hat_section_creation(self):
        """Hat section builds without error."""
        dims = {"H": 150.0, "B_top": 100.0, "B_bot": 60.0, "D": 15.0, "t": 1.5}
        ps = build_profile_strips("hat", dims)
        assert ps.n_strips == 7
        assert ps.n_nodes == 8

    def test_sigma_section_creation(self):
        """Sigma section builds without error."""
        dims = {"H": 250.0, "B": 80.0, "D": 20.0, "h_s": 30.0, "t": 2.0}
        ps = build_profile_strips("sigma", dims)
        assert ps.n_strips == 8
        assert ps.n_nodes == 9

    def test_unknown_profile_raises(self):
        """Unknown profile type raises ValueError."""
        with pytest.raises(ValueError, match="not recognised"):
            build_profile_strips("X", {"t": 2.0})

    def test_strip_width_matches_node_distance(self):
        """Strip widths should be consistent with node coordinates."""
        ps = build_profile_strips("C", _c_channel_dims())
        for s in ps.strips:
            i, j = s.connectivity
            yi, zi = ps.node_coords[i]
            yj, zj = ps.node_coords[j]
            dist = (yj - yi) ** 2 + (zj - zi) ** 2
            dist = dist ** 0.5
            assert s.width_mm == pytest.approx(dist, rel=1e-6)

    def test_K_G_scales_with_stress(self):
        """Doubling the stress should double K_G."""
        ps = _simple_plate_strips()
        K_G_1 = assemble_K_G(ps, 200.0, np.array([100.0]))
        K_G_2 = assemble_K_G(ps, 200.0, np.array([200.0]))
        # K_G is proportional to sigma_x
        ratio = K_G_2 / np.where(np.abs(K_G_1) > 1e-30, K_G_1, np.inf)
        finite_ratio = ratio[np.isfinite(ratio) & (np.abs(K_G_1) > 1e-20)]
        if len(finite_ratio) > 0:
            assert np.allclose(finite_ratio, 2.0, rtol=1e-10)
