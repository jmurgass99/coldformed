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


class Class4WinterPayload(BaseModel):
    b_bar_mm: float = Field(..., gt=0, description="Ancho de la parte plana comprimida en mm")
    t_mm: float = Field(..., gt=0, description="Espesor de la chapa en mm")
    fy_MPa: float = Field(355.0, gt=0, description="Limite elastico en MPa")
    k_sigma: float = Field(4.0, gt=0, description="Coeficiente de abolladura de placa (4.0 compresión uniforme interna, 0.43 voladizo)")
    psi: float = Field(1.0, ge=-1.0, le=1.0, description="Relacion de tensiones sigma2/sigma1 (1.0 uniforme, -1.0 flexion pura)")


def create_router() -> Any:
    """Devuelve el APIRouter con los endpoints. Mountable en gateway."""
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/api/coldformed/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/api/coldformed/section", summary="Propiedades efectivas y pandeo local de perfiles conformados en frío según AISI S100 / EN 1993-1-3")
    def section(payload: SectionPayload) -> dict[str, Any]:
        from fastapi import HTTPException
        from ..exceptions import ValidationError
        from ..services.section_service import SectionInput, evaluate_section

        try:
            result = evaluate_section(
                SectionInput(b=payload.b, h=payload.h, t=payload.t, f_y=payload.f_y)
            )
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.to_dict()

    @router.post("/api/coldformed/effective-width/class4", summary="Factor de reducción de ancho eficaz rho de Winter según EN 1993-1-5 §4.4")
    def class4_winter(payload: Class4WinterPayload) -> dict[str, Any]:
        from fastapi import HTTPException
        from ..class4_evaluator import (
            plate_relative_slenderness, effective_width_factor_rho,
        )
        try:
            lambda_p = plate_relative_slenderness(
                b_bar=payload.b_bar_mm,
                t=payload.t_mm,
                fy=payload.fy_MPa,
                k_sigma=payload.k_sigma,
            )
            rho = effective_width_factor_rho(lambda_p=lambda_p, psi=payload.psi)
            b_eff = rho * payload.b_bar_mm
            return {
                "b_bar_mm": payload.b_bar_mm,
                "t_mm": payload.t_mm,
                "lambda_p": lambda_p,
                "rho": rho,
                "b_eff_mm": b_eff,
                "is_effective_reduced": rho < 1.0,
                "code": "EN 1993-1-5 §4.4 (Winter Eq. 4.2 / 4.3)",
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


def create_app() -> Any:
    """Crea y devuelve la app FastAPI standalone."""
    from fastapi import FastAPI

    app = FastAPI(title="ColdFormedJm API", version="1.0.0")
    app.include_router(create_router())
    return app

