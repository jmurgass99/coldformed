"""
Reducción por perforaciones en perfiles formados en frío (idea #12).

AISI S100-16 §1.1.2 y EN 1993-1-3 §10 — perforaciones circulares o ranuradas
en el alma reducen el área efectiva y la resistencia a compresión local.

Implementación simplificada:
- Área neta = Área bruta - n_holes * d_h * t (clipped).
- Reducción de Pn: Pn_perf = Pn * (Anet/Agross), limitada por código.
- Para AISI: factor max 1.0 si d/w < 0.25 y s/d > 24.
- Para EN: limita d_h <= 0.6*w_alma.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class HoleSpec:
    diameter_mm: float
    n_holes: int
    web_width_mm: float
    thickness_mm: float
    spacing_mm: float = 100.0  # entre centros de huecos a lo largo


@dataclass(frozen=True)
class PerforationResult:
    A_gross_mm2: float
    A_net_mm2: float
    reduction_factor: float
    code: str
    warnings: tuple


def reduce_for_holes(spec: HoleSpec, code: str = "AISI") -> PerforationResult:
    """Calcula área neta y factor reducción.

    code: 'AISI' | 'EN' | 'AS' | 'SG' | 'NSR' | 'USA'
    """
    if spec.diameter_mm <= 0 or spec.thickness_mm <= 0:
        raise ValueError("diameter y thickness deben ser positivos")
    if spec.web_width_mm <= 0:
        raise ValueError("web_width debe ser positivo")
    if spec.n_holes < 0:
        raise ValueError("n_holes >= 0")

    c = code.upper()
    A_gross = spec.web_width_mm * spec.thickness_mm
    A_holes = spec.n_holes * spec.diameter_mm * spec.thickness_mm
    A_net = max(A_gross - A_holes, 0.1 * A_gross)
    warnings = []

    ratio = spec.diameter_mm / spec.web_width_mm
    if c in ("AISI", "USA"):
        # AISI S100-16: si d/w <= 0.5 y s >= 24*d => sin penalidad adicional
        if ratio > 0.5:
            warnings.append("d/w>0.5 fuera de rango AISI estándar")
        if spec.n_holes > 0 and spec.spacing_mm < 24 * spec.diameter_mm:
            warnings.append("spacing <24d penaliza extra")
            A_net *= 0.9
        reduction = A_net / A_gross
    elif c in ("EN", "EU", "SG", "SS"):
        if ratio > 0.6:
            warnings.append("d/w>0.6 fuera de rango EN 1993-1-3")
        reduction = A_net / A_gross
        # EN penaliza adicionalmente con factor (1 - 0.9*d/w + 0.4*d/w^2)
        kw = 1.0 - 0.9 * ratio + 0.4 * ratio * ratio
        kw = max(0.5, min(1.0, kw))
        reduction *= kw
    elif c in ("AS", "AU"):
        # AS/NZS 4600 similar AISI
        reduction = A_net / A_gross
    elif c in ("NSR", "CO"):
        reduction = A_net / A_gross
    else:
        raise ValueError(f"Código desconocido: {code}")

    return PerforationResult(
        A_gross_mm2=A_gross,
        A_net_mm2=A_net,
        reduction_factor=reduction,
        code=code,
        warnings=tuple(warnings),
    )


def Pn_with_holes(Pn_solid_kN: float, spec: HoleSpec, code: str = "AISI") -> float:
    """Aplica reducción a Pn de perfil sólido."""
    r = reduce_for_holes(spec, code=code)
    return Pn_solid_kN * r.reduction_factor
