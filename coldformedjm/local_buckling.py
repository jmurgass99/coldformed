# -*- coding: utf-8 -*-
"""Esfuerzo critico de pandeo local de placa (Loadpath).

ENGINE DE PRODUCCION: solucion analitica de Bryan/Timoshenko
    sigma_cr = k · pi^2 · D / (b^2 · t),   D = E·t^3 / (12·(1-nu^2))
con el factor k segun la condicion de borde (``PLATE_K`` en :mod:`coldformedjm.fsm`):
``ss_ss`` (alma interna) k=4.0, ``ss_free`` (ala en voladizo) k=0.425.

ENGINE FSM JIT (recalibrado, Fase 9): :func:`local_critical_stress_fsm` ensambla
    n franjas del kernel Numba (`fsm_jit`, ahora con la rigidez geometrica Kg = sigma*t*
    (pi/L)^2 * B correcta y el acople ke con la C real, dependiente de nu) y resuelve
    el problema de autovalores generalizado. **Verificado**: converge a la solucion
    de Bryan (k=4.000 SS-SS, k=0.426 SS-libre). Sirve para secciones generales; la
    solucion analitica se mantiene como engine rapido por defecto del validador.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np

from .fsm import PlateBucklingInput, plate_critical_stress, solve_buckling_eigenvalue
from .fsm_jit import fsm_local_stiffness_matrices_jit

# DOF fijos (w=0) por condicion de borde longitudinal, sobre el ensamblado de
# n franjas (2*(n+1) GDL, [w, theta] por nodo). El nodo 0 es un borde, el 2n el otro.
_SIGMA_REF = 1.0  # MPa de referencia; sigma_cr = lambda_min * sigma_ref


@dataclass(frozen=True)
class LocalBucklingResult:
    """Resultado del pandeo local de una placa."""
    sigma_cr_MPa: float
    k: float
    slenderness: float       # b / t
    boundary: str
    method: str = "Bryan/Timoshenko (analitica)"


def local_critical_stress(
    width_mm,
    thickness_mm,
    E_MPa=210000.0,
    nu=0.30,
    boundary="ss_ss",
    k_override=None,
):
    """sigma_cr de pandeo local de una placa en compresion uniforme (Bryan).

    Args:
        width_mm: ancho b de la placa (dimension no apoyada / outstand).
        thickness_mm: espesor t.
        E_MPa, nu: propiedades del material.
        boundary: condicion de borde longitudinal (clave de ``PLATE_K``):
            "ss_ss" alma interna (k=4.0), "ss_free" ala en voladizo (k=0.425).
        k_override: fuerza un k arbitrario (ignora ``boundary``).

    Returns:
        LocalBucklingResult con sigma_cr, k, esbeltez b/t.
    """
    res = plate_critical_stress(PlateBucklingInput(
        width_mm=width_mm, thickness_mm=thickness_mm,
        E_MPa=E_MPa, nu=nu, boundary=boundary, k_override=k_override,
    ))
    return LocalBucklingResult(
        sigma_cr_MPa=res.sigma_cr_MPa,
        k=res.k,
        slenderness=width_mm / thickness_mm,
        boundary=boundary,
    )


def assemble_strip_matrices_jit(width_mm, thickness_mm, length_mm,
                                E_MPa=210000.0, nu=0.30, sigma_ref_MPa=1.0):
    """Expone las matrices 4x4 [ke]/[kg] (calibradas) de una franja FSM via el kernel JIT.

    Returns:
        (ke, kg): matrices numpy 4x4 (DOFs [w_i, theta_i, w_j, theta_j]). El
        autovalor minimo del ensamblado da sigma_cr (ver local_critical_stress_fsm).
    """
    return fsm_local_stiffness_matrices_jit(
        width_mm, thickness_mm, length_mm, E_MPa, nu, sigma_ref_MPa
    )


def _fixed_dofs(boundary, n_strips):
    """GDL de traslacion w a fijar segun la condicion de borde longitudinal."""
    if boundary == "ss_free":
        return (0,)                      # solo el borde apoyado; el otro queda libre
    return (0, 2 * n_strips)             # ss_ss: ambos bordes longitudinales apoyados


def local_critical_stress_fsm(
    width_mm,
    thickness_mm,
    E_MPa=210000.0,
    nu=0.30,
    boundary="ss_ss",
    n_strips=8,
    n_lengths=60,
    ratio_min=0.5,
    ratio_max=None,
):
    """sigma_cr de pandeo local por FSM (kernel Numba) — engine general recalibrado.

    Ensambla ``n_strips`` franjas del kernel JIT a lo ancho de la placa, aplica la
    condicion de borde (``ss_ss`` fija w en ambos bordes, ``ss_free`` en uno) y
    resuelve ``Ke phi = lambda Kg phi`` barriendo la semilongitud de onda L; devuelve
    el sigma_cr minimo (signature curve). Converge a Bryan (k=4.0 SS-SS, 0.425 SS-libre).

    Args:
        width_mm, thickness_mm, E_MPa, nu: placa y material.
        boundary: "ss_ss" (alma interna) o "ss_free" (ala en voladizo).
        n_strips: numero de franjas (8 da <0.1% de error).
        n_lengths, ratio_min, ratio_max: barrido de L/b (ss_free necesita L/b grande;
            por defecto 40 para la asintota del voladizo, 2.5 para ss_ss).

    Returns:
        LocalBucklingResult con sigma_cr, k_effectivo y esbeltez b/t.
    """
    if ratio_max is None:
        ratio_max = 40.0 if boundary == "ss_free" else 2.5
    fixed = _fixed_dofs(boundary, n_strips)
    strip_b = width_mm / n_strips
    ndof = 2 * (n_strips + 1)
    keep = [i for i in range(ndof) if i not in fixed]
    idx = np.ix_(keep, keep)

    best = float("inf")
    for r in np.linspace(ratio_min, ratio_max, n_lengths):
        L = r * width_mm
        KE = np.zeros((ndof, ndof))
        KG = np.zeros((ndof, ndof))
        for s in range(n_strips):
            ke, kg = fsm_local_stiffness_matrices_jit(
                strip_b, thickness_mm, L, E_MPa, nu, _SIGMA_REF
            )
            base = 2 * s
            KE[base:base + 4, base:base + 4] += ke
            KG[base:base + 4, base:base + 4] += kg
        try:
            lam, _mode = solve_buckling_eigenvalue(KE[idx], KG[idx])
        except RuntimeError:
            continue
        if 0.0 < lam < best:
            best = lam  # sigma_cr = lam * sigma_ref, sigma_ref = 1.0

    if best == float("inf"):
        raise RuntimeError("FSM no encontro un modo de pandeo positivo")

    D = E_MPa * thickness_mm ** 3 / (12.0 * (1.0 - nu ** 2))
    k_eff = best / (pi ** 2 * D / (width_mm ** 2 * thickness_mm))
    return LocalBucklingResult(
        sigma_cr_MPa=best,
        k=k_eff,
        slenderness=width_mm / thickness_mm,
        boundary=boundary,
        method="FSM-JIT (Numba, m=1)",
    )


__all__ = [
    "LocalBucklingResult",
    "local_critical_stress",
    "local_critical_stress_fsm",
    "assemble_strip_matrices_jit",
]
