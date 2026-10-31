# -*- coding: utf-8 -*-
"""
Loadpath Core - FSM Elastic Strip Engine Acelerado con Numba JIT.

Matrices de rigidez de una franja finita (plate bending strip) para pandeo local
elastico, con modo longitudinal sinusoidal sin(pi*y/L) (m=1) y forma transversal
Hermite cubica (4 GDL: w_i, theta_i, w_j, theta_j).

Formulacion CUFSM (Cheung) calibrada y verificada (converge a la solucion clasica
de Bryan: k=4.0 para placa SS-SS, k=0.425 para ala en voladizo SS-libre):

    Ke = D * ( A + p^4*B - nu*p^2*(C + C^T) + 2*(1-nu)*p^2*E )
    Kg = sigma_x * t * p^2 * B

con  p = pi/L,  D = E*t^3 / (12*(1-nu^2))  y las matrices de Hermite sobre [0,b]:
    A = int N'' N''  (curvatura transversal)
    B = int N  N     (consistente; tambien define Kg geometrica)
    E = int N'  N'    (torsion/twist)
    C = int N'' N     (acople flexion transversal-longitudinal, no simetrica)

Nota: el factor longitudinal comun (a/2 = L/2) de ambas matrices se OMITE porque se
cancela en el autovalor de pandeo sigma_cr = lambda * sigma_ref.
"""
from __future__ import annotations
import numpy as np
from numba import jit


@jit(nopython=True, cache=True)
def fsm_local_stiffness_matrices_jit(
    width: float,
    thickness: float,
    length: float,
    E: float,
    nu: float,
    sigma_x: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Calcula las matrices elastica [ke] y geometrica [kg] (4x4) de una franja.

    Args:
        width: ancho b de la franja (mm).
        thickness: espesor t (mm).
        length: semilongitud de onda L del modo longitudinal (mm).
        E: modulo de elasticidad (MPa).
        nu: relacion de Poisson.
        sigma_x: esfuerzo de compresion longitudinal de referencia (MPa).

    Returns:
        (ke, kg): tupla de matrices numpy 4x4 (Float64). El autovalor minimo de
        ``Ke phi = lambda Kg phi`` (con sigma_x de referencia) da sigma_cr.
    """
    b = width
    t = thickness
    L = length
    D = (E * t ** 3) / (12.0 * (1.0 - nu ** 2))
    p = np.pi / L
    p2 = p * p
    p4 = p2 * p2

    # A = int N'' N'' dx  (curvatura transversal). [12, 6b, ...] / b^3
    A = np.array([
        [12.0,     6.0 * b,    -12.0,     6.0 * b],
        [6.0 * b,  4.0 * b * b, -6.0 * b, 2.0 * b * b],
        [-12.0,   -6.0 * b,     12.0,    -6.0 * b],
        [6.0 * b,  2.0 * b * b, -6.0 * b, 4.0 * b * b],
    ]) / (b ** 3)

    # B = int N N dx  (consistente). (b/420) * [156, 22b, ...]
    B = np.array([
        [156.0,     22.0 * b,     54.0,     -13.0 * b],
        [22.0 * b,  4.0 * b * b,  13.0 * b, -3.0 * b * b],
        [54.0,      13.0 * b,     156.0,    -22.0 * b],
        [-13.0 * b, -3.0 * b * b, -22.0 * b, 4.0 * b * b],
    ]) * (b / 420.0)

    # E = int N' N' dx  (twist). [36, 3b, ...] / (30b)
    Em = np.array([
        [36.0,     3.0 * b,     -36.0,     3.0 * b],
        [3.0 * b,  4.0 * b * b, -3.0 * b, -1.0 * b * b],
        [-36.0,   -3.0 * b,      36.0,    -3.0 * b],
        [3.0 * b, -1.0 * b * b, -3.0 * b,  4.0 * b * b],
    ]) / (30.0 * b)

    # C = int N'' N dx  (acople, NO simetrica).
    C = np.array([
        [-6.0 / (5.0 * b), -0.1,            6.0 / (5.0 * b), -0.1],
        [-1.1,             -2.0 * b / 15.0, 0.1,              b / 30.0],
        [6.0 / (5.0 * b),   0.1,           -6.0 / (5.0 * b),  0.1],
        [-0.1,              b / 30.0,       1.1,             -2.0 * b / 15.0],
    ])

    ke = D * (A + p4 * B - nu * p2 * (C + C.T) + 2.0 * (1.0 - nu) * p2 * Em)
    kg = sigma_x * t * p2 * B
    return ke, kg
