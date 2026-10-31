# -*- coding: utf-8 -*-
"""Golden tests del factor de reduccion de ancho eficaz rho (Winter) — EN 1993-1-5 §4.4.

Ancla la formula de Winter para PARTES INTERNAS comprimidas

    epsilon = sqrt(235 / fy)
    lambda_p = (b_bar / t) / (28.4 * epsilon * sqrt(k_sigma))
    rho      = (lambda_p - 0.055 * (3 + psi)) / lambda_p**2   <= 1.0

a un caso resuelto a mano del material del master:

WorkID **W00777** — "Solucion Problema 9 — Determinacion de M_C,Rd en viga armada
de Clase 4" (S355, viga armada soldada; alma INTERNA de Clase 4 en flexion pura).
Clausula citada: **EN 1993-1-5 §4.4** (ancho eficaz, factor rho; Tabla 4.1 partes
internas, k_sigma=23.9 para psi=-1).

El alma del cajon/I soldado es un elemento INTERNO (apoyado-apoyado), por lo que la
formula de partes internas (con el termino 0.055*(3+psi)) es la idealizacion correcta
— a diferencia de un ala en voladizo (outstand), que usaria 0.188.

Caso W00777 (alma en flexion pura):
    fy      = 355 MPa            -> epsilon = 0.81
    b_bar   = 1488 mm            (parte plana del alma comprimida idealizada)
    t       = 10 mm
    k_sigma = 23.9               (Tabla 4.1, psi = -1, flexion pura)
    psi     = -1
  => lambda_p = (1488/10) / (28.4 * 0.81 * sqrt(23.9)) = 1.32   [ficha: 1.32]
  => rho      = (1.32 - 0.055*(3-1)) / 1.32**2          = 0.69   [ficha: 0.69]

El golden NO es tautologico: las ENTRADAS (geometria b_bar=1488, t=10, fy=355,
k_sigma=23.9, psi=-1) son independientes del codigo, y los valores ESPERADOS
(epsilon=0.81, lambda_p=1.32, rho=0.69) provienen del calculo manual de la ficha,
no de re-ejecutar la funcion bajo prueba.
"""
from __future__ import annotations

import math

import pytest

from coldformed.class4_evaluator import (
    effective_width_factor_rho,
    plate_relative_slenderness,
)

# --- Datos anclados a W00777 (alma de viga armada Clase 4, flexion pura) ----------
W00777_FY = 355.0
W00777_B_BAR = 1488.0
W00777_T = 10.0
W00777_KSIGMA = 23.9
W00777_PSI = -1.0
# Valores esperados resueltos a mano en la ficha W00777 (EN 1993-1-5 §4.4):
W00777_EPSILON = 0.81
W00777_LAMBDA_P = 1.32
W00777_RHO = 0.69


class TestGoldenW00777Winter:
    """Golden: factor rho de Winter anclado a W00777 (EN 1993-1-5 §4.4, psi=-1)."""

    def test_epsilon_S355(self):
        # epsilon = sqrt(235/355) = 0.8136 -> redondea a 0.81 en la ficha.
        eps = math.sqrt(235.0 / W00777_FY)
        assert eps == pytest.approx(W00777_EPSILON, abs=0.005)

    def test_lambda_p_alma_interna(self):
        lam = plate_relative_slenderness(
            b_bar=W00777_B_BAR, t=W00777_T, fy=W00777_FY, k_sigma=W00777_KSIGMA
        )
        # ficha W00777: lambda_p = 1.32
        assert lam == pytest.approx(W00777_LAMBDA_P, abs=0.005)

    def test_rho_winter_psi_menos_uno(self):
        lam = plate_relative_slenderness(
            b_bar=W00777_B_BAR, t=W00777_T, fy=W00777_FY, k_sigma=W00777_KSIGMA
        )
        rho = effective_width_factor_rho(lambda_p=lam, psi=W00777_PSI)
        # ficha W00777: rho = 0.69  (NO 0.63: el termino es 0.055*(3+psi)=0.11 con psi=-1).
        # La ficha redondea lambda_p a 1.32 antes de evaluar rho: (1.32-0.11)/1.32^2=0.6944;
        # con lambda_p exacto (1.3172) sale 0.6958. Ambos redondean a 0.69 -> tol abs=0.01.
        assert rho == pytest.approx(W00777_RHO, abs=0.01)

    def test_rho_es_sensible_a_psi(self):
        # Honestidad anti-tautologica: con el psi equivocado (+1) la formula da 0.63,
        # claramente distinto del 0.69 de la ficha. El termino (3+psi) IMPORTA.
        lam = plate_relative_slenderness(
            b_bar=W00777_B_BAR, t=W00777_T, fy=W00777_FY, k_sigma=W00777_KSIGMA
        )
        rho_correcto = effective_width_factor_rho(lambda_p=lam, psi=-1.0)
        rho_psi_mas1 = effective_width_factor_rho(lambda_p=lam, psi=1.0)
        assert rho_correcto == pytest.approx(0.69, abs=0.01)   # ficha W00777
        assert rho_psi_mas1 == pytest.approx(0.63, abs=0.01)   # psi=+1 equivocado
        assert rho_correcto > rho_psi_mas1


class TestWinterFactorPropiedades:
    """Propiedades generales de la formula de Winter (EN 1993-1-5 §4.4)."""

    def test_placa_compacta_rho_uno(self):
        # lambda_p pequeno (placa robusta) -> rho se satura a 1.0 (sin reduccion).
        rho = effective_width_factor_rho(lambda_p=0.5, psi=1.0)
        assert rho == pytest.approx(1.0)

    def test_placa_esbelta_rho_menor_uno(self):
        rho = effective_width_factor_rho(lambda_p=2.0, psi=1.0)
        assert 0.0 < rho < 1.0

    def test_rho_acotado_a_uno(self):
        # Nunca supera 1.0 aunque la formula cruda lo permitiera cerca del limite.
        for lam in (0.673, 0.7, 0.9, 1.5, 3.0):
            rho = effective_width_factor_rho(lambda_p=lam, psi=0.0)
            assert rho <= 1.0

    def test_mas_esbelto_menos_eficaz(self):
        # Monotonia: a mayor lambda_p, menor rho (en el rango reductor).
        r1 = effective_width_factor_rho(lambda_p=1.0, psi=1.0)
        r2 = effective_width_factor_rho(lambda_p=2.0, psi=1.0)
        assert r1 > r2

    def test_lambda_p_escala_con_b_sobre_t(self):
        # lambda_p ~ (b/t): duplicar b duplica lambda_p (mismo material y k_sigma).
        lam1 = plate_relative_slenderness(b_bar=744.0, t=10.0, fy=355.0, k_sigma=23.9)
        lam2 = plate_relative_slenderness(b_bar=1488.0, t=10.0, fy=355.0, k_sigma=23.9)
        assert lam2 / lam1 == pytest.approx(2.0, rel=1e-9)
