"""Smoke tests del endpoint HTTP de ColdFormedJm.

Razón de existir: previene la regresión del bug `from __future__ import
annotations` + Pydantic local que hacía que FastAPI tratara el body como
query param (422 en lugar de 200). Los tests de servicios sí cubrían la
lógica de negocio pero NO la capa HTTP. Este archivo cierra ese hueco.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from coldformedjm.api.app import create_app, create_router


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_endpoint(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_section_evaluation_returns_200_with_valid_body(client: TestClient):
    """Caso de regresión: el body Pydantic NO debe ser tratado como query param."""
    r = client.post(
        "/api/coldformed/section",
        json={"b": 200.0, "h": 400.0, "t": 6.0, "f_y": 355.0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Resultado de evaluate_section incluye section_class
    assert "section_class" in body or "Wc" in body or "epsilon" in body, body


def test_section_endpoint_rejects_missing_required_field(client: TestClient):
    """Si falta un campo requerido (b, h, t), debe ser 422 — no 500."""
    r = client.post("/api/coldformed/section", json={"h": 400, "t": 6, "f_y": 355})
    assert r.status_code == 422


def test_create_router_exposes_routes(client: TestClient):
    """El gateway depende de que create_router() devuelva las rutas correctas."""
    router = create_router()
    paths = {r.path for r in router.routes if hasattr(r, "path")}
    assert "/api/coldformed/section" in paths
    assert "/health" in paths
