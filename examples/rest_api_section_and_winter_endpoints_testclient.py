"""API REST (extra `api`) sin servidor: evaluación de sección Clase 4 y ρ de Winter por HTTP.

Dos endpoints: POST /api/coldformed/section (clase, ε y W_eff de un cajón idealizado) y
POST /api/coldformed/effective-width/class4 (λ_p, ρ y b_eff de una placa interna). Las
entradas inválidas devuelven 422. La misma aplicación se sirve con
`uvicorn coldformed.api.app:app`.

Ejecutar:  python examples/rest_api_section_and_winter_endpoints_testclient.py
"""
import json
import warnings

warnings.filterwarnings("ignore")
from fastapi.testclient import TestClient  # noqa: E402

from coldformed.api.app import create_app  # noqa: E402


def main() -> None:
    client = TestClient(create_app())
    print("GET /api/coldformed/health →", client.get("/api/coldformed/health").json())

    r = client.post("/api/coldformed/section", json={"b": 300, "h": 900, "t": 6, "f_y": 355})
    print("\nPOST /api/coldformed/section →", r.status_code, json.dumps(r.json(), ensure_ascii=False))

    r = client.post("/api/coldformed/effective-width/class4",
                    json={"b_bar_mm": 1488, "t_mm": 10, "fy_MPa": 355, "k_sigma": 23.9, "psi": -1.0})
    print("\nPOST /api/coldformed/effective-width/class4 (alma W00777) →", r.status_code)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    r = client.post("/api/coldformed/section", json={"b": 300, "h": 900, "t": -6})
    print("\nt negativo →", r.status_code, "(validación de entrada)")


if __name__ == "__main__":
    main()
