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
    """Resultado del pandeo local de una placa.

    Los tres ultimos campos son el diagnostico del barrido de longitudes del
    engine FSM. Valen ``None`` — no ``0`` — cuando el engine no hace barrido
    (solucion analitica de Bryan): la ausencia de barrido se propaga como
    ausencia; decir "0 intentadas / 0 convergidas" seria afirmar un fallo total
    que no ha ocurrido.
    """
    sigma_cr_MPa: float
    k: float
    slenderness: float       # b / t
    boundary: str
    method: str = "Bryan/Timoshenko (analitica)"
    # --- diagnostico del barrido FSM (None = este engine no barre longitudes)
    n_lengths_attempted: int | None = None
    n_lengths_converged: int | None = None
    failed_ratios: tuple[float, ...] | None = None   # L/b que no convergieron


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
        LocalBucklingResult con sigma_cr, k_effectivo, esbeltez b/t y el
        diagnostico del barrido (``n_lengths_attempted``, ``n_lengths_converged``,
        ``failed_ratios``).

    Raises:
        RuntimeError: si NINGUNA longitud converge, o si el minimo retenido no
            queda resuelto en la rejilla (ver "Guarda" abajo). En ambos casos el
            resultado es NO CALCULADO, no un numero degradado.

    Guarda de fallo PARCIAL — por que NO hay umbral sobre la fraccion perdida:
        ``sigma_cr`` es el MINIMO sobre las longitudes, luego saltarse una
        longitud solo puede SUBIR el resultado: el error es siempre
        sobrestimacion de la capacidad, nunca conservador.

        Medido (b=200 mm, t=6 mm, forzando fallos del eigensolver), la fraccion
        perdida NO predice el error — lo que lo predice es DONDE se pierde:

            44/60 perdidas lejos del minimo (ss_ss)   ->  0.000 %
            30/60 perdidas lejos del minimo (ss_free) ->  0.000 %
             7/60 perdidas sobre el minimo (ss_ss)    ->  1.815 %
            31/60 perdidas sobre el minimo (ss_ss)    -> 20.515 %

        Dos perdidas de tamano comparable (44 y 31) dan 0.000 % y 20.515 %.
        Cualquier umbral del tipo "rechaza si se pierde mas del X %" es a la vez
        demasiado laxo (deja pasar el 1.815 % con solo 7/60 perdidas) y
        demasiado estricto (un umbral del 50 % rechazaria el caso ss_free de
        30/60 perdidas, cuyo error medido es 0.000 %). Por eso el criterio es
        LOCAL, no global:

        **El minimo retenido tiene que estar resuelto en la rejilla**: las dos
        longitudes inmediatamente vecinas del argmin (la unica que exista, si el
        argmin cae en un extremo del barrido) tienen que haber convergido. Con
        ambas presentes el minimo real queda acotado dentro de +/- un paso de
        rejilla y el error es el propio error de discretizacion que el metodo ya
        acepta. Si falta una vecina, el intervalo se ensancha y el error crece de
        forma monotona y sin cota conocida con el ancho del hueco. Medido sobre
        la rama de r bajo (ss_ss, argmin en idx 15): 0.059 % / 0.367 % / 0.953 %
        al alejarse 1, 2 y 3 pasos; y 1.815 % / 6.198 % / 20.515 % para huecos
        contiguos de 7 / 15 / 31 longitudes centrados en el minimo. (No se
        afirma ninguna ley de potencias: el minimo real no cae sobre un nodo de
        la rejilla y las dos ramas crecen a ritmos distintos.)

        La guarda es deliberadamente UNILATERAL: prefiere rechazar de mas antes
        que aprobar de menos. Rechaza dos casos cuyo error medido es
        despreciable — perder la asintota de ss_free (0.005 %) y perder
        idx 16..59 en ss_ss (0.000 %) — porque en ambos la curva todavia venia
        BAJANDO al llegar al borde de lo conocido: que el valor salga bien es
        suerte, no demostracion. El precio de la direccion permisiva es el
        20.515 % de arriba, y es silencioso.

        Suficiencia: que ninguna perdida LEJANA pueda esconder un minimo mas bajo
        descansa en la unimodalidad de la signature curve, MEDIDA aqui (ss_ss:
        1 cambio de signo de la pendiente; ss_free: 0) y garantizada por
        construccion, porque la funcion ensambla franjas de una sola placa. Aun
        asi toda perdida queda registrada en ``failed_ratios``: con perdidas
        presentes ``sigma_cr`` es una COTA SUPERIOR sobre el subdominio perdido.

        Barridos degenerados (``n_lengths`` < 3) no se tratan aparte: la regla
        "toda vecina que exista tiene que haber convergido" se reduce sola. La
        guarda certifica que NINGUNA PERDIDA degrada el barrido; NO certifica que
        la densidad ni el RANGO elegidos por el llamante resuelvan la curva. En
        particular, como un argmin en el extremo del barrido pasa con solo su
        vecina interior, un ``ratio_min``/``ratio_max`` que no encierre el minimo
        real devuelve un numero equivocado sin diagnostico: es un defecto
        preexistente distinto del fallo parcial, y esta guarda no lo cubre.
    """
    if ratio_max is None:
        ratio_max = 40.0 if boundary == "ss_free" else 2.5
    fixed = _fixed_dofs(boundary, n_strips)
    strip_b = width_mm / n_strips
    ndof = 2 * (n_strips + 1)
    keep = [i for i in range(ndof) if i not in fixed]
    idx = np.ix_(keep, keep)

    ratios = np.linspace(ratio_min, ratio_max, n_lengths)
    lambdas: list[float | None] = []   # None = longitud perdida
    failed_ratios: list[float] = []
    for r in ratios:
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
            lam = None
        # Convergir y devolver lambda <= 0 tambien es una longitud perdida:
        # no es un salto mudo, se contabiliza igual que el fallo del solver.
        if lam is None or not (lam > 0.0):
            lambdas.append(None)
            failed_ratios.append(float(r))
            continue
        lambdas.append(float(lam))

    n_converged = n_lengths - len(failed_ratios)
    if n_converged == 0:
        raise RuntimeError("FSM no encontro un modo de pandeo positivo")

    i_best = -1
    best = float("inf")
    for i, lam in enumerate(lambdas):
        if lam is not None and lam < best:
            best = lam       # sigma_cr = lam * sigma_ref, sigma_ref = 1.0
            i_best = i

    # Integridad de rejilla alrededor del minimo retenido (ver docstring).
    lost_neighbours = [
        j for j in (i_best - 1, i_best + 1)
        if 0 <= j < n_lengths and lambdas[j] is None
    ]
    if lost_neighbours:
        vecinas = ", ".join(f"L/b={ratios[j]:.4f}" for j in lost_neighbours)
        raise RuntimeError(
            f"FSM: el minimo del barrido no esta resuelto — la longitud vecina "
            f"del minimo no convergio ({vecinas}); convergieron "
            f"{n_converged}/{n_lengths} longitudes. Saltarse longitudes solo "
            f"puede SUBIR sigma_cr, luego el valor seria una COTA SUPERIOR y no "
            f"un valor: NO CALCULADO."
        )

    D = E_MPa * thickness_mm ** 3 / (12.0 * (1.0 - nu ** 2))
    k_eff = best / (pi ** 2 * D / (width_mm ** 2 * thickness_mm))
    return LocalBucklingResult(
        sigma_cr_MPa=best,
        k=k_eff,
        slenderness=width_mm / thickness_mm,
        boundary=boundary,
        method="FSM-JIT (Numba, m=1)",
        n_lengths_attempted=n_lengths,
        n_lengths_converged=n_converged,
        failed_ratios=tuple(failed_ratios),
    )


__all__ = [
    "LocalBucklingResult",
    "local_critical_stress",
    "local_critical_stress_fsm",
    "assemble_strip_matrices_jit",
]
