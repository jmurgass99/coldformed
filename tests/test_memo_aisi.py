"""Tests para memoria AISI effective width."""
import pytest

from coldformedjm.memos import (
    EffectiveWidthMemoInput,
    render_effective_width_memo,
)


def test_compacto_no_reduce():
    r = render_effective_width_memo(EffectiveWidthMemoInput(
        b_mm=100, t_mm=4, sigma_act_MPa=50,
    ))
    assert r.rho == 1.0
    assert r.b_eff_mm == 100


def test_esbelto_reduce():
    r = render_effective_width_memo(EffectiveWidthMemoInput(
        b_mm=400, t_mm=2, sigma_act_MPa=350,
    ))
    assert r.rho < 1.0
    assert r.b_eff_mm < 400


def test_markdown_contiene_pasos():
    r = render_effective_width_memo(EffectiveWidthMemoInput(
        b_mm=300, t_mm=2, sigma_act_MPa=250,
    ))
    for kw in ("Paso 1", "Paso 2", "Paso 3", "Paso 4", "b_eff"):
        assert kw in r.markdown
