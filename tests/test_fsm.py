"""Tests para coldformedjm.fsm — Finite Strip Method base."""
import numpy as np
import pytest

from coldformedjm.fsm import (
    FiniteStripMethod,
    PLATE_K,
    PlateBucklingInput,
    plate_critical_stress,
    solve_buckling_eigenvalue,
    strip_geometric_stiffness,
)


class TestPlateCriticalStress:
    def test_caso_referencia_alma_ss(self):
        # Bryan: σ_cr = 4 π² · 210000 / (12·(1-0.09)) · (2/200)² ≈ 75.9 MPa
        res = plate_critical_stress(PlateBucklingInput(
            width_mm=200, thickness_mm=2, boundary="ss_ss",
        ))
        # Verificación manual: D = 210000·8/(12·0.91) = 153846
        # σ_cr = 4·π²·D / (200²·2) = 4·π²·153846 / 80000 ≈ 75.94
        assert res.sigma_cr_MPa == pytest.approx(75.94, rel=1e-2)
        assert res.k == 4.0

    def test_k_override(self):
        res = plate_critical_stress(PlateBucklingInput(
            width_mm=200, thickness_mm=2, k_override=6.97,
        ))
        assert res.k == 6.97

    def test_validacion(self):
        with pytest.raises(ValueError):
            plate_critical_stress(PlateBucklingInput(
                width_mm=-1, thickness_mm=2,
            )).validate()  # type: ignore[attr-defined]
        with pytest.raises(ValueError):
            plate_critical_stress(PlateBucklingInput(
                width_mm=200, thickness_mm=2, boundary="???",
            ))

    def test_boundary_alters_resultado(self):
        ss = plate_critical_stress(PlateBucklingInput(
            width_mm=100, thickness_mm=2, boundary="ss_ss",
        )).sigma_cr_MPa
        cc = plate_critical_stress(PlateBucklingInput(
            width_mm=100, thickness_mm=2, boundary="cc",
        )).sigma_cr_MPa
        # k_cc > k_ss → σ_cr mayor
        assert cc > ss


class TestStripGeometricStiffness:
    def test_simetria_y_tamano(self):
        KG = strip_geometric_stiffness(width=100, length=500,
                                        thickness=2, sigma_x=100)
        assert KG.shape == (8, 8)
        # Bloque w (4×4) debe ser simétrico
        block = KG[:4, :4]
        assert np.allclose(block, block.T)

    def test_input_invalido(self):
        with pytest.raises(ValueError):
            strip_geometric_stiffness(0, 100, 2, 100)


class TestEigenvalueSolver:
    def test_problema_simple(self):
        # K_E = I, K_G = diag(0.5, 0.2) → λ_min = 1/0.5 = 2
        K_E = np.eye(2)
        K_G = np.diag([0.5, 0.2])
        lam, mode = solve_buckling_eigenvalue(K_E, K_G)
        assert lam == pytest.approx(2.0, rel=1e-6)
        assert mode.shape == (2,)

    def test_dimensiones_incompatibles(self):
        with pytest.raises(ValueError):
            solve_buckling_eigenvalue(np.eye(3), np.eye(2))


class TestFiniteStripMethodFacade:
    def test_compat_seed(self):
        # Compat con la firma original del seed
        fsm = FiniteStripMethod()
        fcr = fsm.plate_critical_stress(width=200, thickness=2, k_factor=4.0)
        assert fcr == pytest.approx(75.94, rel=1e-2)

    def test_strip_kg_via_facade(self):
        fsm = FiniteStripMethod()
        KG = fsm.strip_geometric_stiffness(width=100, length=500,
                                            thickness=2, sigma_x=100)
        assert KG.shape == (8, 8)


def test_plate_k_constantes():
    # Garantía de que los k de referencia están registrados
    for key in ("ss_ss", "ss_free", "cc", "cs"):
        assert key in PLATE_K
        assert PLATE_K[key] > 0
