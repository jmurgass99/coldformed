from __future__ import annotations

"""Aplicacion FastAPI ligera para ColdFormedJm.

Expone un unico endpoint principal de evaluacion de secciones Clase 4.
Las dependencias de FastAPI/Pydantic se importan de forma perezosa para
no forzar la instalacion del extra ``api`` en entornos sin REST.
"""
from typing import Any
from pydantic import BaseModel, Field


class SectionPayload(BaseModel):
    b: float = Field(..., gt=0, description="Ancho del ala en mm")
    h: float = Field(..., gt=0, description="Altura del alma en mm")
    t: float = Field(..., gt=0, description="Espesor en mm")
    f_y: float = Field(355.0, gt=0, description="Limite elastico en MPa")


def create_router() -> Any:
    """Devuelve el APIRouter con los endpoints. Mountable en gateway."""
    from fastapi import APIRouter, HTTPException

    from ..exceptions import ValidationError
    from ..services import SectionInput, evaluate_section

    router = APIRouter()

    @router.get("/api/coldformed/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/api/coldformed/section", summary="Propiedades efectivas y pandeo local de perfiles conformados en frío según AISI S100 / EN 1993-1-3")
    def section(payload: SectionPayload) -> dict[str, Any]:
        try:
            result = evaluate_section(
                SectionInput(b=payload.b, h=payload.h, t=payload.t, f_y=payload.f_y)
            )
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.to_dict()

    return router


def create_app() -> Any:
    """Crea y devuelve la app FastAPI standalone."""
    from fastapi import FastAPI

    app = FastAPI(title="ColdFormedJm API", version="1.0.0")
    app.include_router(create_router())
    return app

