"""Tests para iteración de propiedades efectivas (gotcha #18)."""
import pytest

from coldformedjm.effective_iter import (
    EffectiveIterInput,
    _b_eff_aisi,
    iterate_effective,
)


def test_b_eff_aisi_compacto_no_reduce():
    # b/t = 50 con sigma_act bajo → ρ ≈ 1
    b = _b_eff_aisi(b=200, t=4, sigma_act=50, sigma_y=350, E=210_000)
    assert b == 200


def test_b_eff_aisi_esbelto_reduce():
    # b/t = 200, σ_act = σ_y → λ_p > 0.673 → reducción
    b = _b_eff_aisi(b=400, t=2, sigma_act=350, sigma_y=350, E=210_000)
    assert b < 400


def test_iter_convergente_sin_redistribucion():
    # sigma_act constante → converge en 2 iteraciones
    def provider(ratio: float) -> float:
        return 200.0  # σ_act fija independiente del ratio

    res = iterate_effective(EffectiveIterInput(
        b_gross=300, t=2, sigma_demand_provider=provider, sigma_y=350,
    ))
    assert res.converged
    assert res.iterations <= 3


def test_iter_con_redistribucion_realista():
    # σ_act baja cuando b_eff baja (más rigidez → menos demanda)
    # σ ∝ 1/ratio simplificado
    def provider(ratio: float) -> float:
        return 200.0 / max(ratio, 0.1)

    res = iterate_effective(EffectiveIterInput(
        b_gross=400, t=2, sigma_demand_provider=provider, sigma_y=350,
        max_iter=15,
    ))
    assert 0 < res.final_ratio <= 1.0


def test_iter_no_converge_devuelve_flag():
    # Provider oscilante
    flip = [False]

    def provider(_: float) -> float:
        flip[0] = not flip[0]
        return 50.0 if flip[0] else 500.0

    res = iterate_effective(EffectiveIterInput(
        b_gross=400, t=2, sigma_demand_provider=provider,
        max_iter=4,
    ))
    assert not res.converged
    assert res.iterations == 4
