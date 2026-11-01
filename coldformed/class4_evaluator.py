"""
class4_evaluator.py - Effective width calculations for Class 4 sections.

Factor de reduccion de ancho eficaz rho (Winter) segun EN 1993-1-5 §4.4 para
PARTES INTERNAS comprimidas y elementos en voladizo (outstand):

    epsilon  = sqrt(235 / fy)
    lambda_p = (b_bar / t) / (28.4 * epsilon * sqrt(k_sigma))
    rho      = (lambda_p - 0.055 * (3 + psi)) / lambda_p**2   <= 1.0   (internas)
    rho      = (lambda_p - 0.188) / lambda_p**2               <= 1.0   (outstand)

Anclado a WorkID W00777 (viga armada Clase 4, alma interna en flexion pura,
psi=-1, k_sigma=23.9): rho = 0.69. Ver tests/test_winter_effective_width.py.
"""
from __future__ import annotations

import math


def plate_relative_slenderness(b_bar: float, t: float, fy: float,
                               k_sigma: float) -> float:
    """Esbeltez relativa de placa lambda_p (EN 1993-1-5 §4.4, ec. 4.3).

    ``lambda_p = (b_bar / t) / (28.4 * epsilon * sqrt(k_sigma))`` con
    ``epsilon = sqrt(235 / fy)``. Equivale a ``sqrt(fy / sigma_cr)`` ya que el
    coeficiente 28.4 absorbe ``pi**2 * E / (12 * (1 - nu**2))`` para E=210000, nu=0.3.

    Args:
        b_bar: ancho de la parte plana comprimida del elemento [mm].
        t: espesor [mm].
        fy: limite elastico [MPa].
        k_sigma: coeficiente de pandeo de placa segun psi y condicion de borde
            (Tabla 4.1 partes internas / Tabla 4.2 voladizos de EN 1993-1-5).

    Returns:
        lambda_p (adimensional).
    """
    epsilon = math.sqrt(235.0 / fy)
    return (b_bar / t) / (28.4 * epsilon * math.sqrt(k_sigma))


def effective_width_factor_rho(lambda_p: float, psi: float) -> float:
    """Factor de reduccion de ancho eficaz rho de Winter — partes internas.

    EN 1993-1-5 §4.4, ec. (4.2):
        rho = 1.0                                  si lambda_p <= 0.5 + sqrt(0.085 - 0.055*psi)
        rho = (lambda_p - 0.055*(3 + psi)) / lambda_p**2   <= 1.0   en caso contrario

    Args:
        lambda_p: esbeltez relativa de placa (ver :func:`plate_relative_slenderness`).
        psi: relacion de tensiones en los bordes del elemento (1.0 compresion
            uniforme, -1.0 flexion pura). Afecta tanto al umbral como al termino
            ``0.055*(3 + psi)`` — por eso un psi equivocado falsea rho.

    Returns:
        rho en (0, 1].
    """
    threshold = 0.5 + math.sqrt(max(0.085 - 0.055 * psi, 0.0))
    if lambda_p <= threshold:
        return 1.0
    rho = (lambda_p - 0.055 * (3.0 + psi)) / (lambda_p ** 2)
    return min(1.0, max(0.0, rho))


def effective_width_factor_rho_outstand(lambda_p: float) -> float:
    """Factor de reduccion de ancho eficaz rho de Winter — elementos en voladizo (outstand).

    EN 1993-1-5 §4.4, ec. (4.3):
        rho = 1.0                              si lambda_p <= 0.748
        rho = (lambda_p - 0.188) / lambda_p^2  en caso contrario (<= 1.0)
    """
    if lambda_p <= 0.748:
        return 1.0
    rho = (lambda_p - 0.188) / (lambda_p ** 2)
    return min(1.0, max(0.0, rho))


class Class4Section:
    def __init__(
        self,
        b: float,
        h: float,
        t: float,
        f_y: float = 355.0,
        t_f: float | None = None,
        t_w: float | None = None,
        outstand_flange: bool = False,
    ):
        """
        Rectangular hollow section or welded I-section parameters.
        :param b: Flange width in mm
        :param h: Web height in mm
        :param t: Default thickness in mm (used when t_f or t_w are not specified)
        :param f_y: Yield strength in MPa
        :param t_f: Optional flange thickness in mm (defaults to t)
        :param t_w: Optional web thickness in mm (defaults to t)
        :param outstand_flange: If True, treats compression flange as outstand (EN 1993-1-5 Table 4.2)
        """
        self.b = b
        self.h = h
        self.t = t
        self.t_f = float(t if t_f is None else t_f)
        self.t_w = float(t if t_w is None else t_w)
        self.f_y = f_y
        self.outstand_flange = bool(outstand_flange)
        self.E = 210000.0  # MPa

    def calculate_epsilon(self) -> float:
        return math.sqrt(235.0 / self.f_y)

    def check_class(self) -> int:
        """
        Check if section is Class 4 based on web under pure bending and flange under compression.
        c/t limit for Class 3 web is 124*epsilon; for flange is 42*epsilon (internal) or 14*epsilon (outstand).
        """
        eps = self.calculate_epsilon()
        c_t_ratio = self.h / self.t_w
        if c_t_ratio > 124.0 * eps:
            return 4
        c_t_flange = self.b / self.t_f
        flange_limit = 14.0 * eps if self.outstand_flange else 42.0 * eps
        if c_t_flange > flange_limit:
            return 4
        return 3

    def calculate_effective_modulus(self) -> float:
        """
        Calculation of effective section modulus W_eff for a Class 4 section [cm³].
        Supports independent flange (t_f) and web (t_w) thicknesses.
        """
        if self.check_class() < 4:
            I_y = (self.b * self.h ** 3) / 12.0 - ((self.b - self.t_w) * (self.h - 2.0 * self.t_f) ** 3) / 12.0
            return (I_y / (self.h / 2.0)) / 1000.0  # cm3

        if self.outstand_flange:
            lambda_p_f = plate_relative_slenderness(self.b, self.t_f, self.f_y, k_sigma=0.43)
            rho_f = effective_width_factor_rho_outstand(lambda_p_f)
        else:
            lambda_p_f = plate_relative_slenderness(self.b, self.t_f, self.f_y, k_sigma=4.0)
            rho_f = effective_width_factor_rho(lambda_p_f, psi=1.0)
        b_eff = rho_f * self.b

        lambda_p_w = plate_relative_slenderness(self.h, self.t_w, self.f_y, k_sigma=23.9)
        rho_w = effective_width_factor_rho(lambda_p_w, psi=-1.0)
        h_eff = rho_w * self.h

        I_y_eff = (b_eff * h_eff ** 3) / 12.0 - ((b_eff - self.t_w) * (h_eff - 2.0 * self.t_f) ** 3) / 12.0
        W_eff = (I_y_eff / (self.h / 2.0)) / 1000.0  # cm3

        return round(W_eff, 2)
