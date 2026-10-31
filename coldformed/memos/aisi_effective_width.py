"""
Memoria handcalcs — ancho efectivo AISI / EN 1993-1-5 para placa
comprimida (Clase 4). Produce LaTeX y Markdown paso a paso.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Any


@dataclass(frozen=True)
class EffectiveWidthMemoInput:
    b_mm: float
    t_mm: float
    sigma_act_MPa: float
    E_MPa: float = 210_000.0
    nu: float = 0.30
    k_plate: float = 4.0   # ss-ss alma


@dataclass(frozen=True)
class EffectiveWidthMemoResult:
    sigma_cr_MPa: float
    lambda_p: float
    rho: float
    b_eff_mm: float
    markdown: str
    latex: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sigma_cr_MPa": self.sigma_cr_MPa,
            "lambda_p": self.lambda_p,
            "rho": self.rho,
            "b_eff_mm": self.b_eff_mm,
        }


def render_effective_width_memo(data: EffectiveWidthMemoInput
                                  ) -> EffectiveWidthMemoResult:
    b, t = data.b_mm, data.t_mm
    sigma_cr = (data.k_plate * pi ** 2 * data.E_MPa) / (
        12.0 * (1.0 - data.nu ** 2) * (b / t) ** 2
    )
    lambda_p = sqrt(data.sigma_act_MPa / sigma_cr)
    if lambda_p <= 0.673:
        rho = 1.0
    else:
        rho = (lambda_p - 0.22) / (lambda_p ** 2)
    b_eff = rho * b

    md = (
        "# Memoria — Ancho efectivo (EN 1993-1-5 / AISI)\n\n"
        f"**Geometría:** b = {b:.1f} mm, t = {t:.2f} mm, b/t = {b/t:.1f}\n"
        f"**Esfuerzo actuante:** σ = {data.sigma_act_MPa:.1f} MPa\n\n"
        "## Paso 1 — Esfuerzo crítico de placa (Bryan)\n\n"
        f"σ_cr = k · π² · E / [12 · (1-ν²) · (b/t)²]\n"
        f"σ_cr = {data.k_plate:.1f} · π² · {data.E_MPa:.0f} / "
        f"[12 · (1 - {data.nu}²) · {b/t:.1f}²]\n"
        f"**σ_cr = {sigma_cr:.1f} MPa**\n\n"
        "## Paso 2 — Esbeltez de placa\n\n"
        f"λ_p = √(σ/σ_cr) = √({data.sigma_act_MPa:.1f}/{sigma_cr:.1f}) "
        f"= {lambda_p:.3f}\n\n"
        "## Paso 3 — Factor de reducción\n\n"
        + (
            f"λ_p = {lambda_p:.3f} ≤ 0.673 → **ρ = 1.0** (sección efectiva = bruta)\n"
            if rho == 1.0 else
            f"λ_p = {lambda_p:.3f} > 0.673 → "
            f"ρ = (λ_p - 0.22)/λ_p² = ({lambda_p:.3f} - 0.22)/{lambda_p:.3f}² = "
            f"**{rho:.3f}**\n"
        )
        + f"\n## Paso 4 — Ancho efectivo\n\n"
        f"**b_eff = ρ · b = {rho:.3f} · {b:.1f} = {b_eff:.1f} mm**\n"
    )

    latex = (
        rf"\sigma_{{cr}} = \frac{{k\pi^2 E}}{{12(1-\nu^2)(b/t)^2}} = "
        rf"{sigma_cr:.1f}\;\text{{MPa}}\\"
        rf"\lambda_p = \sqrt{{\sigma/\sigma_{{cr}}}} = {lambda_p:.3f}\\"
        rf"\rho = {rho:.3f}\\"
        rf"b_{{eff}} = \rho\,b = {b_eff:.1f}\;\text{{mm}}"
    )
    return EffectiveWidthMemoResult(
        sigma_cr_MPa=sigma_cr, lambda_p=lambda_p, rho=rho,
        b_eff_mm=b_eff, markdown=md, latex=latex,
    )


__all__ = [
    "EffectiveWidthMemoInput", "EffectiveWidthMemoResult",
    "render_effective_width_memo",
]
