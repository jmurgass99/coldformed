# -*- coding: utf-8 -*-
"""Fallo PARCIAL del barrido de longitudes en el FSM de pandeo local.

Defecto cubierto: dentro de ``local_critical_stress_fsm`` el barrido hacia el
minimo de la signature curve capturaba ``RuntimeError`` del eigensolver y hacia
``continue``. Como ``sigma_cr`` es el MINIMO sobre las longitudes, saltarse una
longitud solo puede SUBIR el resultado -> capacidad sobrestimada, y nada
registraba cuantas longitudes se perdieron.

MEDICION que fija el diseno (ver la tabla en ``TestSobrestimacionMedida``):
la FRACCION de longitudes perdidas NO predice el error. Medido en b=200, t=6:

    perdidas  donde                          sobrestimacion de sigma_cr
    44/60     lejos del minimo (ss_ss)        0.000 %
    30/60     lejos del minimo (ss_free)      0.000 %
     7/60     sobre el minimo (ss_ss)         1.815 %
    31/60     sobre el minimo (ss_ss)        20.515 %

Dos perdidas de tamano casi igual (44 y 31) dan 0.000 % y 20.515 %. Por eso la
guarda NO es un umbral sobre la fraccion perdida sino sobre la INTEGRIDAD DE
REJILLA alrededor del minimo retenido (ver el docstring de la funcion).
"""
from __future__ import annotations

import numpy as np
import pytest

import coldformed.local_buckling as lb
from coldformed.local_buckling import (
    local_critical_stress,
    local_critical_stress_fsm,
)

_REAL_SOLVER = lb.solve_buckling_eigenvalue


def _con_fallos(fail_idx, monkeypatch, lam_override=None):
    """Fuerza el fallo del eigensolver en los indices dados del barrido.

    No toca ``fsm.py``: parchea el nombre ya importado en ``local_buckling``.
    ``lam_override``: si se da, en vez de lanzar devuelve ese lambda (para
    ejercitar el camino "converge pero devuelve un autovalor no positivo").
    """
    estado = {"i": -1}

    def falso(KE, KG):
        estado["i"] += 1
        if estado["i"] in fail_idx:
            if lam_override is not None:
                return lam_override, np.zeros(KE.shape[0])
            raise RuntimeError("mock: el eigensolver no convergio")
        return _REAL_SOLVER(KE, KG)

    monkeypatch.setattr(lb, "solve_buckling_eigenvalue", falso)
    return estado


# Configuraciones sanas medidas: las 5 que usan los tests existentes convergen
# en 60/60 longitudes, luego la guarda nueva no puede disparar en verde.
_SS_SS = dict(width_mm=200.0, thickness_mm=6.0, boundary="ss_ss", n_strips=8)
_SS_FREE = dict(width_mm=200.0, thickness_mm=6.0, boundary="ss_free", n_strips=16)


class TestGuardaDeFalloTotal:
    """La auditoria dijo que esta guarda YA existia. Se fija como regresion."""

    def test_fallo_total_lanza_runtimeerror(self, monkeypatch):
        _con_fallos(set(range(60)), monkeypatch)
        with pytest.raises(RuntimeError, match="no encontro un modo de pandeo positivo"):
            local_critical_stress_fsm(**_SS_SS)


class TestDiagnosticoDelBarrido:
    """El resultado tiene que decir cuantas longitudes se intentaron/convergieron."""

    def test_barrido_sano_reporta_60_de_60(self):
        r = local_critical_stress_fsm(**_SS_SS)
        assert r.n_lengths_attempted == 60
        assert r.n_lengths_converged == 60
        assert r.failed_ratios == ()

    def test_respeta_n_lengths_del_llamante(self):
        r = local_critical_stress_fsm(**_SS_SS, n_lengths=25)
        assert r.n_lengths_attempted == 25
        assert r.n_lengths_converged == 25

    def test_perdida_lejos_del_minimo_se_reporta_aunque_pase(self, monkeypatch):
        """Pasa la guarda (valor exacto) pero la perdida NO queda invisible."""
        base = local_critical_stress_fsm(**_SS_SS)
        _con_fallos({57, 58, 59}, monkeypatch)
        r = local_critical_stress_fsm(**_SS_SS)
        assert r.sigma_cr_MPa == base.sigma_cr_MPa      # 0.000 % de efecto
        assert r.n_lengths_attempted == 60
        assert r.n_lengths_converged == 57
        assert len(r.failed_ratios) == 3
        # Los ratios perdidos son L/b, no indices.
        assert r.failed_ratios[-1] == pytest.approx(2.5)

    def test_analitico_no_inventa_ceros_la_ausencia_es_None(self):
        """``local_critical_stress`` no hace barrido: 0/0 seria mentira."""
        r = local_critical_stress(200.0, 6.0, boundary="ss_ss")
        assert r.n_lengths_attempted is None
        assert r.n_lengths_converged is None
        assert r.failed_ratios is None


class TestGuardaDeIntegridadDeRejilla:
    """Perder una longitud PEGADA al minimo retenido invalida el resultado."""

    def test_perder_solo_el_minimo_lanza(self, monkeypatch):
        # idx 15 es el argmin medido de ss_ss (r*=1.0085).
        _con_fallos({15}, monkeypatch)
        with pytest.raises(RuntimeError, match="minimo"):
            local_critical_stress_fsm(**_SS_SS)

    def test_perder_7_longitudes_sobre_el_minimo_lanza(self, monkeypatch):
        # Medido: dejaria pasar 695.7399 MPa frente a 683.3347 -> +1.815 %.
        _con_fallos(set(range(12, 19)), monkeypatch)
        with pytest.raises(RuntimeError):
            local_critical_stress_fsm(**_SS_SS)

    def test_perder_31_longitudes_sobre_el_minimo_lanza(self, monkeypatch):
        # Medido: dejaria pasar 823.5211 MPa frente a 683.3347 -> +20.515 %.
        _con_fallos(set(range(0, 31)), monkeypatch)
        with pytest.raises(RuntimeError):
            local_critical_stress_fsm(**_SS_SS)

    def test_curva_aun_bajando_al_borde_de_lo_conocido_lanza(self, monkeypatch):
        """Conservadurismo declarado: el minimo retenido cae en idx 15 y el 16
        se perdio. El valor resultaria exacto (0.000 %) por suerte, pero la
        curva todavia venia BAJANDO, luego no esta demostrado que 15 sea el
        minimo. Se lanza."""
        _con_fallos(set(range(16, 60)), monkeypatch)
        with pytest.raises(RuntimeError):
            local_critical_stress_fsm(**_SS_SS)

    def test_mensaje_de_error_lleva_el_diagnostico(self, monkeypatch):
        _con_fallos({15}, monkeypatch)
        with pytest.raises(RuntimeError) as exc:
            local_critical_stress_fsm(**_SS_SS)
        msg = str(exc.value)
        assert "59/60" in msg          # cuantas convergieron
        assert "1.0085" in msg or "1.008" in msg   # el L/b perdido, no un indice


class TestMinimoEnElExtremoDelBarrido:
    """ss_free: el minimo esta en el ULTIMO punto (asintota del voladizo)."""

    def test_ss_free_sano_pasa_con_argmin_en_el_extremo(self):
        """El extremo no tiene vecino derecho: eso NO puede ser un fallo."""
        r = local_critical_stress_fsm(**_SS_FREE)
        assert r.k == pytest.approx(0.425, abs=0.01)
        assert r.n_lengths_converged == 60

    def test_ss_free_perder_los_primeros_pasa(self, monkeypatch):
        """Medido 0.000 %: la mitad baja del barrido no toca la asintota."""
        base = local_critical_stress_fsm(**_SS_FREE)
        _con_fallos(set(range(0, 30)), monkeypatch)
        r = local_critical_stress_fsm(**_SS_FREE)
        assert r.sigma_cr_MPa == base.sigma_cr_MPa
        assert r.n_lengths_converged == 30

    def test_ss_free_perder_la_asintota_lanza(self, monkeypatch):
        """Conservadurismo declarado: efecto medido 0.005 %, pero la asintota
        del voladizo queda sin evaluar y la curva seguia bajando."""
        _con_fallos({59}, monkeypatch)
        with pytest.raises(RuntimeError):
            local_critical_stress_fsm(**_SS_FREE)


class TestAutovalorNoPositivo:
    """Convergir y devolver lambda <= 0 tambien es una longitud perdida."""

    def test_lambda_no_positivo_cuenta_como_fallo_no_como_salto_mudo(self, monkeypatch):
        _con_fallos({57, 58, 59}, monkeypatch, lam_override=-1.0)
        r = local_critical_stress_fsm(**_SS_SS)
        assert r.n_lengths_converged == 57
        assert len(r.failed_ratios) == 3


class TestSobrestimacionMedida:
    """CARACTERIZACION (no golden): la tabla sale de la implementacion, medida
    con el eigensolver real y fallos forzados. Fija la propiedad central:

        la guarda NUNCA deja pasar un numero materialmente equivocado.

    Todo caso que PASA tiene 0.000 % de error medido; todo caso con error > 0
    lanza. Descansa en la unimodalidad MEDIDA de la signature curve (ss_ss:
    1 cambio de signo de la pendiente; ss_free: 0), no en una suposicion.
    """

    # (fail_idx, config, sobrestimacion_medida_%) con el comportamiento permisivo
    CASOS = [
        (set(range(57, 60)), "ss_ss", 0.000),
        (set(range(16, 60)), "ss_ss", 0.000),
        ({15}, "ss_ss", 0.059),
        (set(range(14, 17)), "ss_ss", 0.367),
        (set(range(12, 19)), "ss_ss", 1.815),
        (set(range(8, 23)), "ss_ss", 6.198),
        (set(range(0, 31)), "ss_ss", 20.515),
        ({59}, "ss_free", 0.005),
        (set(range(50, 60)), "ss_free", 0.063),
        (set(range(20, 60)), "ss_free", 1.155),
        (set(range(0, 30)), "ss_free", 0.000),
    ]

    @pytest.mark.parametrize("fail_idx,cfg_name,sobrest_pct", CASOS)
    def test_lo_que_pasa_la_guarda_es_exacto(self, fail_idx, cfg_name, sobrest_pct,
                                             monkeypatch):
        cfg = _SS_SS if cfg_name == "ss_ss" else _SS_FREE
        base = local_critical_stress_fsm(**cfg)
        _con_fallos(fail_idx, monkeypatch)
        try:
            r = local_critical_stress_fsm(**cfg)
        except RuntimeError:
            return  # la guarda lo rechazo: es el resultado admisible
        # Si pasa, el valor tiene que ser el del barrido completo.
        assert r.sigma_cr_MPa == base.sigma_cr_MPa, (
            f"la guarda dejo pasar un valor movido "
            f"({(r.sigma_cr_MPa / base.sigma_cr_MPa - 1) * 100:.3f} %)"
        )
        assert sobrest_pct == 0.000, (
            f"caso con sobrestimacion medida {sobrest_pct} % deberia haber sido "
            f"rechazado por la guarda"
        )
