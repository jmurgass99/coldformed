# -*- coding: utf-8 -*-
"""Golden tests EC3-1-3 adicionales del factor de reduccion de ancho eficaz rho
(Winter) para el ALMA de perfiles conformados en frio, anclados a fichas del
master DISTINTAS de W00777 (que ya cubre test_winter_effective_width.py).

Formula bajo prueba (EN 1993-1-5 §4.4, partes internas comprimidas — citada en
las tres fichas de esta campaña como el metodo de ancho eficaz aplicable a
elementos planos de perfiles conformados en frio):

    epsilon  = sqrt(235 / fy)
    lambda_p = (b_bar / t) / (28.4 * epsilon * sqrt(k_sigma))
    rho      = (lambda_p - 0.055 * (3 + psi)) / lambda_p**2   <= 1.0  (si lambda_p > umbral)
    rho      = 1.0                                             (si lambda_p <= umbral)
    umbral   = 0.5 + sqrt(0.085 - 0.055*psi)

Cita de clausula: EN 1993-1-3:2006 §5.5.2 "Plane elements without stiffeners"
remite el ancho eficaz de elementos planos sin rigidizar a EN 1993-1-5 §4.4 —
asi lo tratan las tres fichas ancladas aqui (W01482, W01486, W01527), que citan
"EC3-1-3" / "EC3 Parte 1-3" como marco y desarrollan literalmente la formula de
EN 1993-1-5 §4.4. NOTA: el numero "§5.5.2" es la numeracion estandar de
EN 1993-1-3:2006 para esa remision; ninguna ficha de este corpus transcribe el
texto de esa clausula concreta (solo grep-eado "EN 1993-1-5 §4.4" aparece
verificado literalmente en los ficheros), por lo que se documenta como
clausula estandar del codigo, no como cita verificada palabra-por-palabra del
corpus. La formula en si (rho, lambda_p, umbral) SI esta verificada linea a
linea contra el texto de las tres fichas.

REGLA DE ORO de esta campana: no fiarse de los numeros impresos en las fichas.
Cada golden de este fichero fue recalculado a mano (formula transcrita, sin
reimportar la funcion bajo prueba) antes de anclarlo — ver el bloque de
verificacion en cada test. Los tres casos cuadran con los valores impresos
dentro de la tolerancia de redondeo de la ficha (las fichas redondean
lambda_p/k_sigma a 2 decimales antes de evaluar rho, lo que introduce un
arrastre de ~0.001-0.003 en rho frente al valor con precision completa).
"""
from __future__ import annotations

import math

import pytest

from coldformed.class4_evaluator import (
    effective_width_factor_rho,
    plate_relative_slenderness,
)


# ---------------------------------------------------------------------------
# WorkID W01486 — "Exercise 16 resolution": vigueta C200.74.2 (S350GD),
# alma bajo gradiente de tensiones psi=-0.74 (NO psi=-1 ni psi=+1: caso no
# degenerado, el mas discriminante de los tres — un psi equivocado (+1 o el
# termino de voladizo 0.188) se aleja claramente de 0.85, ver test de abajo).
# Clausula: EN 1993-1-3 §5.5.2 -> EN 1993-1-5 §4.4 (alma, elemento interno).
# ---------------------------------------------------------------------------
W01486_FY = 350.0        # S350GD
W01486_HP = 198.0        # mm, ancho plano del alma (h_p, esquinas despreciadas)
W01486_T = 1.96          # mm, espesor neto (t_cor, descontado galvanizado)
W01486_PSI = -0.74
# k_sigma de la ficha: k_sigma = 7.81 - 6.29*psi + 9.78*psi**2 (EN1993-1-5 Tabla 4.1,
# formula para elemento interno bajo gradiente, 0 > psi > -1). Verificado a mano:
W01486_KSIGMA_FICHA = 17.82
W01486_LAMBDA_P_FICHA = 1.03
W01486_RHO_FICHA = 0.85


class TestGoldenW01486AlmaGradiente:
    """Golden: rho de Winter con psi=-0.74 (gradiente), anclado a W01486."""

    def test_ksigma_formula_gradiente_tensiones(self):
        # Verificacion independiente de la entrada k_sigma=17.82 con la formula
        # de interpolacion de EN 1993-1-5 Tabla 4.1 (0 > psi > -1), transcrita a
        # mano de la ficha (no es funcion de produccion: plate_relative_slenderness
        # recibe k_sigma como parametro y no lo calcula internamente).
        k_sigma = 7.81 - 6.29 * W01486_PSI + 9.78 * W01486_PSI ** 2
        assert k_sigma == pytest.approx(W01486_KSIGMA_FICHA, abs=0.01)

    def test_lambda_p_alma_gradiente(self):
        lam = plate_relative_slenderness(
            b_bar=W01486_HP, t=W01486_T, fy=W01486_FY, k_sigma=W01486_KSIGMA_FICHA
        )
        # calculo manual: eps=sqrt(235/350)=0.8194; lam=(198/1.96)/(28.4*0.8194*sqrt(17.82))=1.0283
        assert lam == pytest.approx(W01486_LAMBDA_P_FICHA, abs=0.005)

    def test_rho_gradiente_psi_menos_0_74(self):
        lam = plate_relative_slenderness(
            b_bar=W01486_HP, t=W01486_T, fy=W01486_FY, k_sigma=W01486_KSIGMA_FICHA
        )
        rho = effective_width_factor_rho(lambda_p=lam, psi=W01486_PSI)
        # calculo manual: umbral=0.5+sqrt(0.085+0.055*0.74)=0.8545 < lam=1.0283
        # rho=(1.0283-0.055*(3-0.74))/1.0283**2 = 0.8549
        assert rho == pytest.approx(W01486_RHO_FICHA, abs=0.01)

    def test_rho_es_sensible_a_psi_no_degenerado(self):
        # Honestidad anti-tautologica: psi=-0.74 es un caso NO trivial (ni -1 ni
        # +1). Con psi equivocado (+1, compresion uniforme) o con el termino de
        # voladizo aproximado (0.188 en vez de 0.055*(3+psi)), rho se aleja
        # claramente de 0.85 -> el test no pasaria "por casualidad".
        lam = plate_relative_slenderness(
            b_bar=W01486_HP, t=W01486_T, fy=W01486_FY, k_sigma=W01486_KSIGMA_FICHA
        )
        rho_correcto = effective_width_factor_rho(lambda_p=lam, psi=W01486_PSI)
        rho_psi_mas1 = effective_width_factor_rho(lambda_p=lam, psi=1.0)
        # formula de voladizo (EN 1993-1-5 Tabla 4.2) evaluada a mano: EQUIVOCADA
        # para el alma (elemento interno), se calcula solo para mostrar que el
        # termino 0.188 tampoco reproduce 0.85 por casualidad.
        rho_outstand_equivocado = (lam - 0.188) / lam ** 2
        assert rho_correcto == pytest.approx(0.85, abs=0.01)              # ficha W01486
        assert rho_psi_mas1 == pytest.approx(0.764, abs=0.005)            # psi=+1 equivocado
        assert rho_outstand_equivocado == pytest.approx(0.795, abs=0.005)  # formula equivocada (voladizo)
        assert rho_correcto > rho_psi_mas1
        assert rho_correcto > rho_outstand_equivocado


# ---------------------------------------------------------------------------
# WorkID W01527 — "Solucion Problema 3 Seccion ligera": vigueta CF200.2 (S460),
# alma en flexion pura (psi=-1), acero de mayor limite elastico que W00777/
# W01486 (S460 vs S355/S350) -> confirmacion independiente con otro fy y otra
# relacion b/t. k_sigma=23.88 coincide con la formula de la Tabla 4.1 evaluada
# en psi=-1 EXACTA: 7.81+6.29+9.78=23.88 (no es solo lectura de tabla redondeada).
# Clausula: EN 1993-1-3 §5.5.2 -> EN 1993-1-5 §4.4.
# ---------------------------------------------------------------------------
W01527_FY = 460.0         # S460
W01527_B = 198.0           # mm, ancho plano del alma (b=h_p, esquinas despreciadas)
W01527_T = 2.0             # mm
W01527_PSI = -1.0
W01527_KSIGMA = 23.88
W01527_LAMBDA_P_FICHA = 1.00
W01527_RHO_FICHA = 0.89


class TestGoldenW01527AlmaS460:
    """Golden: rho de Winter en S460 (flexion pura), anclado a W01527."""

    def test_ksigma_flexion_pura_formula_exacta(self):
        # k_sigma = 7.81 - 6.29*(-1) + 9.78*(-1)**2 = 23.88 (EXACTO, no redondeo).
        k_sigma = 7.81 - 6.29 * W01527_PSI + 9.78 * W01527_PSI ** 2
        assert k_sigma == pytest.approx(W01527_KSIGMA, abs=0.001)

    def test_lambda_p_alma_S460(self):
        lam = plate_relative_slenderness(
            b_bar=W01527_B, t=W01527_T, fy=W01527_FY, k_sigma=W01527_KSIGMA
        )
        # calculo manual: eps=sqrt(235/460)=0.7148; lam=(198/2)/(28.4*0.7148*sqrt(23.88))=0.9980
        assert lam == pytest.approx(W01527_LAMBDA_P_FICHA, abs=0.005)

    def test_rho_S460_flexion_pura(self):
        lam = plate_relative_slenderness(
            b_bar=W01527_B, t=W01527_T, fy=W01527_FY, k_sigma=W01527_KSIGMA
        )
        rho = effective_width_factor_rho(lambda_p=lam, psi=W01527_PSI)
        # calculo manual: umbral=0.8742 < lam=0.9980
        # rho=(0.9980-0.055*2)/0.9980**2 = 0.8915
        assert rho == pytest.approx(W01527_RHO_FICHA, abs=0.01)


# ---------------------------------------------------------------------------
# WorkID W01482 — "Exercise 14 resolution": correa Z 350.3 (S350GD), alma en
# flexion pura (psi=-1). NOTA DE ALCANCE: la ficha usa el ancho TOTAL h=350mm
# como b_bar del alma (no descuenta esquinas), a diferencia de W01486 (h_p=198
# vs h_nominal=200) y W01527 (b=198 vs h_nominal=200) que SI descuentan ~2mm
# por esquinas redondeadas. La ficha W01482 no reporta el radio de acuerdo r,
# asi que no se puede confirmar si b_bar=350 es una simplificacion valida
# (r<5t) o una inconsistencia de la ficha frente a sus hermanas. Por eso este
# golden se ancla como afirmacion de NIVEL DE PLACA ("dado b_bar=350mm,
# t=3mm, k_sigma=23.9, psi=-1 -> rho"), NO como hecho de seccion completa del
# perfil Z 350.3 (ver hallazgo en el informe final, seccion "erratas/dudas").
# Clausula: EN 1993-1-3 §5.5.2 -> EN 1993-1-5 §4.4.
# ---------------------------------------------------------------------------
W01482_FY = 350.0          # S350GD
W01482_B_BAR = 350.0        # mm, altura total h usada como b_bar en la ficha (ver nota de alcance)
W01482_T = 3.0              # mm
W01482_PSI = -1.0
W01482_KSIGMA = 23.9
W01482_LAMBDA_P_FICHA = 1.03
W01482_RHO_FICHA = 0.867


class TestGoldenW01482PlacaZ350AlmaFlexionPura:
    """Golden a nivel de PLACA (no de seccion), anclado a W01482. Ver nota de alcance arriba."""

    def test_lambda_p_placa_alma_Z350(self):
        lam = plate_relative_slenderness(
            b_bar=W01482_B_BAR, t=W01482_T, fy=W01482_FY, k_sigma=W01482_KSIGMA
        )
        # calculo manual: eps=sqrt(235/350)=0.8194; lam=(350/3)/(28.4*0.8194*sqrt(23.9))=1.0255
        assert lam == pytest.approx(W01482_LAMBDA_P_FICHA, abs=0.005)

    def test_rho_placa_alma_Z350(self):
        lam = plate_relative_slenderness(
            b_bar=W01482_B_BAR, t=W01482_T, fy=W01482_FY, k_sigma=W01482_KSIGMA
        )
        rho = effective_width_factor_rho(lambda_p=lam, psi=W01482_PSI)
        # calculo manual: umbral=0.8742 < lam=1.0255
        # rho=(1.0255-0.11)/1.0255**2 = 0.8705 (ficha redondea lambda_p a 1.03
        # antes de evaluar rho: (1.03-0.11)/1.03**2=0.8672; ambos redondean a 0.867/0.870)
        assert rho == pytest.approx(W01482_RHO_FICHA, abs=0.01)
