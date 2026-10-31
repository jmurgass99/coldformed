"""
class4_evaluator.py - Effective width calculations for Class 4 sections.

Factor de reduccion de ancho eficaz rho (Winter) segun EN 1993-1-5 §4.4 para
PARTES INTERNAS comprimidas:

    epsilon  = sqrt(235 / fy)
    lambda_p = (b_bar / t) / (28.4 * epsilon * sqrt(k_sigma))
    rho      = (lambda_p - 0.055 * (3 + psi)) / lambda_p**2   <= 1.0

Anclado a WorkID W00777 (viga armada Clase 4, alma interna en flexion pura,
psi=-1, k_sigma=23.9): rho = 0.69. Ver tests/test_winter_effective_width.py.
"""
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


class Class4Section:
    def __init__(self, b: float, h: float, t: float, f_y: float = 355.0):
        """
        Simplified rectangular hollow section or I-section parameters.
        :param b: Flange width in mm
        :param h: Web height in mm
        :param t: Thickness in mm
        :param f_y: Yield strength in MPa
        """
        self.b = b
        self.h = h
        self.t = t
        self.f_y = f_y
        self.E = 210000.0 # MPa
        
    def calculate_epsilon(self) -> float:
        return math.sqrt(235.0 / self.f_y)
        
    def check_class(self) -> int:
        """
        Check if section is Class 4 based on web under pure bending.
        c/t limit for Class 3 web is 124*epsilon.
        """
        eps = self.calculate_epsilon()
        c_t_ratio = self.h / self.t
        if c_t_ratio > 124 * eps:
            return 4
        # Flange under compression limit for Class 3 is 42*epsilon (outstand) or 33*eps (internal)
        # Assuming internal for simplicity
        c_t_flange = self.b / self.t
        if c_t_flange > 42 * eps:
            return 4
            
        return 3 # or better

    def calculate_effective_modulus(self) -> float:
        """
        Iterative-like calculation of effective section modulus W_eff for a Class 4 section.
        """
        if self.check_class() < 4:
            # Gross modulus
            I_y = (self.b * self.h**3) / 12.0 - ((self.b - self.t) * (self.h - 2*self.t)**3) / 12.0
            return (I_y / (self.h / 2.0)) / 1000.0 # cm3
            
        # For class 4, we reduce the web and flange widths via the Winter factor
        # rho (EN 1993-1-5 §4.4). Each element carries its own psi and k_sigma:
        #   - flange in uniform compression: psi = +1, k_sigma = 4.0
        #   - web in pure bending:           psi = -1, k_sigma = 23.9
        # NOTE: el termino 0.055*(3+psi) depende de psi; usar psi=+1 para el alma
        # (flexion pura, psi=-1) subestimaba rho_w. Anclado a W00777 (rho_w=0.69).
        lambda_p_f = plate_relative_slenderness(self.b, self.t, self.f_y, k_sigma=4.0)
        rho_f = effective_width_factor_rho(lambda_p_f, psi=1.0)
        b_eff = rho_f * self.b

        # Web reduction (rho_w) under pure bending (psi = -1).
        lambda_p_w = plate_relative_slenderness(self.h, self.t, self.f_y, k_sigma=23.9)
        rho_w = effective_width_factor_rho(lambda_p_w, psi=-1.0)
        h_eff = rho_w * self.h
        
        # Approximate effective inertia
        I_y_eff = (b_eff * h_eff**3) / 12.0 - ((b_eff - self.t) * (h_eff - 2*self.t)**3) / 12.0
        W_eff = (I_y_eff / (self.h / 2.0)) / 1000.0 # cm3
        
        return round(W_eff, 2)
