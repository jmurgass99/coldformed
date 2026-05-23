"""
class4_evaluator.py - Effective width calculations for Class 4 sections.
"""
import math

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
            
        # For class 4, we reduce the web and flange widths
        # Simplified winter formula approach
        eps = self.calculate_epsilon()
        
        # Flange reduction (rho_f)
        lambda_p_f = (self.b / self.t) / (28.4 * eps * math.sqrt(4.0)) # approx k_sigma = 4.0
        rho_f = 1.0
        if lambda_p_f > 0.673:
            rho_f = (lambda_p_f - 0.055 * (3.0 + 1)) / (lambda_p_f**2)
            rho_f = min(1.0, max(0.0, rho_f))
            
        b_eff = rho_f * self.b
        
        # Web reduction (rho_w) under pure bending
        lambda_p_w = (self.h / self.t) / (28.4 * eps * math.sqrt(23.9)) # approx k_sigma = 23.9
        rho_w = 1.0
        if lambda_p_w > 0.673:
            rho_w = (lambda_p_w - 0.055 * (3.0 + 1)) / (lambda_p_w**2)
            rho_w = min(1.0, max(0.0, rho_w))
            
        h_eff = rho_w * self.h
        
        # Approximate effective inertia
        I_y_eff = (b_eff * h_eff**3) / 12.0 - ((b_eff - self.t) * (h_eff - 2*self.t)**3) / 12.0
        W_eff = (I_y_eff / (self.h / 2.0)) / 1000.0 # cm3
        
        return round(W_eff, 2)
