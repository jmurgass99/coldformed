"""Tests de integración y golden analítico para ancho eficaz Clase 4 según EN 1993-1-5 §4.4.

Norma: EN 1993-1-5 §4.4 Eq. (4.2) y (4.3) (Fórmula de reducción de Winter).
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from coldformedjm.api.app import create_router
from coldformedjm.class4_evaluator import plate_relative_slenderness, effective_width_factor_rho


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(create_router())
    return TestClient(app)


def test_plate_relative_slenderness_and_rho_golden():
    """Golden analítico exacto para elemento comprimido uniforme según EN 1993-1-5 §4.4.

    b = 200 mm, t = 2.0 mm, fy = 355 MPa, k_sigma = 4.0, psi = 1.0 (compresión uniforme):
      epsilon = sqrt(235 / 355) = 0.813617
      lambda_p = (200 / 2) / (28.4 * 0.813617 * 2.0) = 100 / 46.2135 = 2.16387
      threshold = 0.5 + sqrt(0.085 - 0.055*1) = 0.6732
      rho = (2.16387 - 0.055 * 4) / (2.16387²) = 1.94387 / 4.68234 = 0.41515
    """
    b = 200.0
    t = 2.0
    fy = 355.0
    k_sigma = 4.0
    psi = 1.0

    lambda_p = plate_relative_slenderness(b_bar=b, t=t, fy=fy, k_sigma=k_sigma)
    assert lambda_p == pytest.approx(2.16387, rel=1e-4)

    rho = effective_width_factor_rho(lambda_p=lambda_p, psi=psi)
    assert rho == pytest.approx(0.41515, rel=1e-4)
    assert rho < 1.0


def test_class4_winter_api_endpoint(client):
    """Verifica endpoint HTTP /api/coldformed/effective-width/class4."""
    payload = {
        "b_bar_mm": 200.0,
        "t_mm": 2.0,
        "fy_MPa": 355.0,
        "k_sigma": 4.0,
        "psi": 1.0,
    }
    resp = client.post("/api/coldformed/effective-width/class4", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["lambda_p"] == pytest.approx(2.16387, rel=1e-4)
    assert data["rho"] == pytest.approx(0.41515, rel=1e-4)
    assert data["b_eff_mm"] == pytest.approx(83.03, rel=1e-3)
    assert data["is_effective_reduced"] is True
