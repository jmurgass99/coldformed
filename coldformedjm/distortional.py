"""coldformedjm.distortional — Pandeo Distorsional para perfiles C y Z.

Implementa y separa inequívocamente:
1. Método AISI S100-16 / S100-22 (Direct Strength Method - DSM):
   - Cálculo analítico del esfuerzo crítico de pandeo distorsional σ_crd (Schafer 2002 / Appendix 2).
   - Resistencia nominal distorsional en compresión Pnd (AISI S100 §E3).
   - Resistencia nominal distorsional en flexión Mnd (AISI S100 §F3).
   - Verificación de límites de aplicabilidad geométrica (AISI S100 Tabla B4.1-1).

2. Método EN 1993-1-3:2006 §5.5.3 (Eurocódigo 3 Parte 1-3):
   - Rigidez elástica de muelle K del rigidizador de borde (pestaña/labio).
   - Esfuerzo crítico de pandeo elástico del rigidizador σ_cr,s = 2·sqrt(K·E·Is) / As.
   - Esbeltez relativa de pandeo distorsional λ_bar_d = sqrt(f_yb / σ_cr,s).
   - Factor de reducción distorsional χ_d (§5.5.3.1 eq 5.12).
   - Espesor reducido t_red y área reducida As,red del rigidizador.
   - Capacidad resistente de diseño Nc,Rd y Mc,Rd según EN 1993-1-3.
   - Verificación de límites geométricos normativos (EN 1993-1-3 Tabla 5.1).

Criterio de integridad: cada resultado declara expresamente la norma aplicada,
el método de cálculo, las hipótesis adoptadas y si la sección satisface los límites
de aplicabilidad normativa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Literal, Optional


# ---------------------------------------------------------------------------
# Estructuras de Entrada y Salida
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SectionGeometryCZ:
    """Geometría canónica de sección C o Z conformada en frío.

    Dimensiones exteriores:
    - h_mm: canto total del alma
    - b_mm: ancho total de las alas
    - lip_mm: longitud total de la pestaña o rigidizador de borde (d o c)
    - t_mm: espesor nominal del acero (descontado galvanizado)
    - shape: 'C' (canal rigidizada) o 'Z' (perfil zeta)
    """
    h_mm: float
    b_mm: float
    lip_mm: float
    t_mm: float
    shape: Literal["C", "Z"] = "C"

    @property
    def h_t(self) -> float:
        return self.h_mm / max(self.t_mm, 1e-6)

    @property
    def b_t(self) -> float:
        return self.b_mm / max(self.t_mm, 1e-6)

    @property
    def lip_t(self) -> float:
        return self.lip_mm / max(self.t_mm, 1e-6)

    @property
    def lip_b(self) -> float:
        return self.lip_mm / max(self.b_mm, 1e-6)

    @property
    def h_b(self) -> float:
        return self.h_mm / max(self.b_mm, 1e-6)

    @property
    def gross_area_mm2(self) -> float:
        """Área bruta aproximada de la chapa plana (sin considerar radios de curvatura)."""
        return (self.h_mm + 2.0 * self.b_mm + 2.0 * self.lip_mm) * self.t_mm

    @property
    def gross_modulus_major_mm3(self) -> float:
        """Módulo de sección elástico bruto aproximado respecto al eje fuerte (z-z / x-x)."""
        h, b, d, t = self.h_mm, self.b_mm, self.lip_mm, self.t_mm
        # Inercia de chapa delgada aproximada
        # Alma: t * h^3 / 12
        # Alas: 2 * (b * t * (h/2)^2)
        # Labios: 2 * (t * d^3 / 12 + d * t * (h/2 - d/2)^2)
        I_web = t * (h ** 3) / 12.0
        I_flanges = 2.0 * (b * t * ((h / 2.0) ** 2))
        I_lips = 2.0 * (t * (d ** 3) / 12.0 + d * t * ((h / 2.0 - d / 2.0) ** 2))
        I_total = I_web + I_flanges + I_lips
        return I_total / (h / 2.0)


@dataclass(frozen=True)
class DistortionalResultAISI:
    """Resultado del cálculo distorsional según AISI S100 (DSM)."""
    standard: str = "AISI S100-16/22"
    method: str = "Direct Strength Method (DSM)"
    sigma_crd_MPa: float = 0.0
    L_crd_mm: float = 0.0
    # Compresión
    Py_kN: float = 0.0
    Pcrd_kN: float = 0.0
    lambda_d_c: float = 0.0
    Pnd_kN: float = 0.0
    phi_c_Pn_kN: float = 0.0    # φc = 0.85
    # Flexión
    My_kNm: float = 0.0
    Mcrd_kNm: float = 0.0
    lambda_d_b: float = 0.0
    Mnd_kNm: float = 0.0
    phi_b_Mn_kNm: float = 0.0  # φb = 0.90
    # Validez
    is_valid_dsm: bool = True
    validity_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "standard": self.standard,
            "method": self.method,
            "sigma_crd_MPa": self.sigma_crd_MPa,
            "L_crd_mm": self.L_crd_mm,
            "Pnd_kN": self.Pnd_kN,
            "phi_c_Pn_kN": self.phi_c_Pn_kN,
            "Mnd_kNm": self.Mnd_kNm,
            "phi_b_Mn_kNm": self.phi_b_Mn_kNm,
            "is_valid_dsm": self.is_valid_dsm,
            "validity_notes": list(self.validity_notes),
        }


@dataclass(frozen=True)
class DistortionalResultEC3:
    """Resultado del cálculo distorsional según EN 1993-1-3 §5.5.3 (EWM)."""
    standard: str = "EN 1993-1-3:2006"
    method: str = "Effective Width Method (EWM §5.5.3 Edge Stiffener)"
    K_spring_N_per_mm2: float = 0.0
    As_eff_mm2: float = 0.0
    Is_eff_mm4: float = 0.0
    sigma_cr_s_MPa: float = 0.0
    lambda_bar_d: float = 0.0
    chi_d: float = 1.0
    t_red_mm: float = 0.0
    As_red_mm2: float = 0.0
    # Capacidades de diseño
    Nc_Rd_kN: float = 0.0        # Compresión resistente de diseño (γM0 = 1.00)
    Mc_Rd_kNm: float = 0.0       # Flexión resistente de diseño (γM0 = 1.00)
    # Validez
    is_valid_ec3: bool = True
    validity_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "standard": self.standard,
            "method": self.method,
            "K_spring_N_per_mm2": self.K_spring_N_per_mm2,
            "sigma_cr_s_MPa": self.sigma_cr_s_MPa,
            "lambda_bar_d": self.lambda_bar_d,
            "chi_d": self.chi_d,
            "t_red_mm": self.t_red_mm,
            "As_red_mm2": self.As_red_mm2,
            "Nc_Rd_kN": self.Nc_Rd_kN,
            "Mc_Rd_kNm": self.Mc_Rd_kNm,
            "is_valid_ec3": self.is_valid_ec3,
            "validity_notes": list(self.validity_notes),
        }


# ---------------------------------------------------------------------------
# Verificaciones de Aplicabilidad Normativa
# ---------------------------------------------------------------------------

def check_aisi_dsm_applicability(sec: SectionGeometryCZ, Fy_MPa: float) -> tuple[bool, list[str]]:
    """Verifica los límites de aplicabilidad geométrica de perfiles C y Z según AISI S100 Tabla B4.1-1."""
    notes: list[str] = []
    is_valid = True

    if sec.h_t > 200.0:
        notes.append(f"h/t = {sec.h_t:.1f} excede el límite DSM de 200 para perfiles C/Z")
        is_valid = False
    if sec.b_t > 60.0:
        notes.append(f"b/t = {sec.b_t:.1f} excede el límite DSM de 60 para alas")
        is_valid = False
    if sec.lip_t > 50.0:
        notes.append(f"lip/t = {sec.lip_t:.1f} excede el límite DSM de 50 para pestañas")
        is_valid = False
    if sec.lip_mm <= 0.0:
        notes.append("El perfil carece de pestaña (lip <= 0); no es aplicable pandeo distorsional de borde")
        is_valid = False
    if not (1.5 <= sec.h_b <= 5.0):
        notes.append(f"Relación h/b = {sec.h_b:.2f} fuera del rango típico precalificado [1.5, 5.0]")
    if not (0.05 <= sec.lip_b <= 0.50):
        notes.append(f"Relación lip/b = {sec.lip_b:.2f} fuera del rango típico [0.05, 0.50]")
    if Fy_MPa > 550.0:
        notes.append(f"Fy = {Fy_MPa:.1f} MPa excede el límite de acero conformado en frío (550 MPa)")
        is_valid = False

    return is_valid, notes


def check_ec3_applicability(sec: SectionGeometryCZ, fyb_MPa: float) -> tuple[bool, list[str]]:
    """Verifica los límites geométricos de perfiles C y Z según EN 1993-1-3 Tabla 5.1."""
    notes: list[str] = []
    is_valid = True

    if sec.b_t > 60.0:
        notes.append(f"b/t = {sec.b_t:.1f} excede el límite normativo EN 1993-1-3 de 60")
        is_valid = False
    if sec.h_t > 500.0:
        notes.append(f"h/t = {sec.h_t:.1f} excede el límite normativo EN 1993-1-3 de 500")
        is_valid = False
    if sec.lip_t > 50.0:
        notes.append(f"c/t = {sec.lip_t:.1f} excede el límite normativo EN 1993-1-3 de 50")
        is_valid = False
    if sec.lip_mm <= 0.0:
        notes.append("Perfil sin rigidizador de borde (c <= 0); aplicar §5.5.2 en vez de §5.5.3")
        is_valid = False
    if not (0.2 <= sec.lip_b <= 0.6):
        notes.append(f"Relación c/b = {sec.lip_b:.2f} fuera de la recomendación EN 1993-1-3 [0.2, 0.6]")
    if fyb_MPa > 550.0:
        notes.append(f"fyb = {fyb_MPa:.1f} MPa excede los aceros normalizados de EN 1993-1-3")
        is_valid = False

    return is_valid, notes


# ---------------------------------------------------------------------------
# Implementación 1: AISI S100-16 / S100-22 (DSM)
# ---------------------------------------------------------------------------

def aisi_distortional_buckling(
    sec: SectionGeometryCZ,
    Fy_MPa: float = 350.0,
    E_MPa: float = 210000.0,
    nu: float = 0.30,
) -> DistortionalResultAISI:
    """Calcula el pandeo distorsional según el Direct Strength Method (AISI S100).

    Aplica las ecuaciones analíticas de Schafer (2002) para perfiles C y Z lipped:
    1. Propiedades de la pestaña y rigidizador de borde aislado.
    2. Rigidez rotacional suministrada por el alma k_phi_w.
    3. Longitud de onda crítica L_crd y tensión crítica de pandeo distorsional σ_crd.
    4. Resistencia a compresión Pnd (§E3) y flexión Mnd (§F3).
    """
    is_valid, notes = check_aisi_dsm_applicability(sec, Fy_MPa)

    h = max(sec.h_mm, 10.0)
    b = max(sec.b_mm, 10.0)
    d = max(sec.lip_mm, 1.0)
    t = max(sec.t_mm, 0.5)

    # 1. Propiedades del conjunto ala-pestaña (flange-lip)
    Af = (b + d) * t
    # Centro de gravedad del ala-pestaña desde el plano medio del alma (x) y ala (y)
    x_bar = (b * t * (b / 2.0) + d * t * b) / Af
    y_bar = (d * t * (d / 2.0)) / Af

    # Inercias del ala-pestaña respecto a su propio centro de gravedad
    Ixf = (t * (d ** 3) / 12.0) + (d * t * ((d / 2.0 - y_bar) ** 2)) + (b * t * (y_bar ** 2))
    Iyf = (t * (b ** 3) / 12.0) + (b * t * ((b / 2.0 - x_bar) ** 2)) + (d * t * ((b - x_bar) ** 2))
    Jf = (1.0 / 3.0) * (b + d) * (t ** 3)
    G = E_MPa / (2.0 * (1.0 + nu))

    # Radio de giro polar respecto al punto de unión alma-ala
    r_of_sq = (Ixf + Iyf) / Af + (x_bar ** 2) + (y_bar ** 2)

    # 2. Rigidez rotacional del alma k_phi_w (Schafer 2002)
    k_phi_w = (E_MPa * (t ** 3)) / (6.0 * (1.0 - nu ** 2) * h)

    # 3. Longitud de onda crítica L_crd
    term_L = (E_MPa * Ixf * (b ** 2)) / max(k_phi_w, 1e-6)
    L_crd = math.pi * (term_L ** 0.25)
    L_crd = max(50.0, min(L_crd, 20.0 * h))

    # Tensión elástica crítica de pandeo distorsional σ_crd
    pi_L_sq = (math.pi / L_crd) ** 2
    k_phi_fe = pi_L_sq * E_MPa * Ixf * (y_bar ** 2) + G * Jf
    k_phi_fg = Af * pi_L_sq * (r_of_sq + y_bar ** 2)

    sigma_crd = (k_phi_fe + k_phi_w) / max(k_phi_fg, 1e-9)
    sigma_crd = max(1.0, sigma_crd)

    # 4. Compresión nominal Pnd (AISI S100 §E3)
    Ag = sec.gross_area_mm2
    Py = Ag * Fy_MPa / 1000.0  # kN
    Pcrd = Ag * sigma_crd / 1000.0  # kN
    lam_d_c = math.sqrt(Py / max(Pcrd, 1e-6))

    if lam_d_c <= 0.561:
        Pnd = Py
    else:
        ratio_c = Pcrd / Py
        Pnd = (1.0 - 0.25 * (ratio_c ** 0.6)) * (ratio_c ** 0.6) * Py

    phi_c = 0.85
    phi_c_Pn = phi_c * Pnd

    # 5. Flexión nominal Mnd (AISI S100 §F3)
    Sf = sec.gross_modulus_major_mm3
    My = Sf * Fy_MPa / 1e6  # kN·m
    Mcrd = Sf * sigma_crd / 1e6  # kN·m
    lam_d_b = math.sqrt(My / max(Mcrd, 1e-6))

    if lam_d_b <= 0.673:
        Mnd = My
    else:
        ratio_b = Mcrd / My
        Mnd = (1.0 - 0.22 * (ratio_b ** 0.5)) * (ratio_b ** 0.5) * My

    phi_b = 0.90
    phi_b_Mn = phi_b * Mnd

    return DistortionalResultAISI(
        standard="AISI S100-16/22",
        method="Direct Strength Method (DSM)",
        sigma_crd_MPa=round(sigma_crd, 2),
        L_crd_mm=round(L_crd, 1),
        Py_kN=round(Py, 2),
        Pcrd_kN=round(Pcrd, 2),
        lambda_d_c=round(lam_d_c, 3),
        Pnd_kN=round(Pnd, 2),
        phi_c_Pn_kN=round(phi_c_Pn, 2),
        My_kNm=round(My, 3),
        Mcrd_kNm=round(Mcrd, 3),
        lambda_d_b=round(lam_d_b, 3),
        Mnd_kNm=round(Mnd, 3),
        phi_b_Mn_kNm=round(phi_b_Mn, 3),
        is_valid_dsm=is_valid,
        validity_notes=notes,
    )


# ---------------------------------------------------------------------------
# Implementación 2: EN 1993-1-3:2006 §5.5.3 (EWM con Muelle Elástico)
# ---------------------------------------------------------------------------

def ec3_distortional_buckling(
    sec: SectionGeometryCZ,
    fyb_MPa: float = 350.0,
    loading: Literal["compression", "bending"] = "compression",
    E_MPa: float = 210000.0,
    nu: float = 0.30,
    gamma_M0: float = 1.00,
) -> DistortionalResultEC3:
    """Calcula el pandeo distorsional del rigidizador de borde según EN 1993-1-3 §5.5.3.

    Procedimiento normativo:
    1. Sección eficaz inicial del rigidizador As (pestaña outstand + franja de ala).
    2. Rigidez elástica de muelle K por unidad de longitud (ec. 5.10 / 5.11).
    3. Tensión crítica elástica de pandeo del rigidizador:
       σ_cr,s = 2 · sqrt(K · E · Is) / As   (ec. 5.15)
    4. Esbeltez relativa:
       λ_bar_d = sqrt(f_yb / σ_cr,s)
    5. Coeficiente de reducción distorsional χ_d (ec. 5.12).
    6. Espesor y área reducida As,red = χ_d · As.
    """
    is_valid, notes = check_ec3_applicability(sec, fyb_MPa)

    h = max(sec.h_mm, 10.0)
    b = max(sec.b_mm, 10.0)
    c = max(sec.lip_mm, 1.0)
    t = max(sec.t_mm, 0.5)

    # 1. Ancho eficaz inicial de la pestaña (outstand element, k_sigma = 0.43)
    epsilon = math.sqrt(235.0 / fyb_MPa)
    lambda_p_c = (c / t) / (28.4 * epsilon * math.sqrt(0.43))
    if lambda_p_c <= 0.74:
        rho_c = 1.0
    else:
        rho_c = (lambda_p_c - 0.188) / (lambda_p_c ** 2)
    rho_c = min(1.0, max(0.0, rho_c))
    c_eff = rho_c * c

    # Franja eficaz de ala adyacente al rigidizador (EN 1993-1-3 §5.5.3.2)
    # Por defecto para compresión uniforme: be2 = 0.5 * beff, flange k_sigma = 4.0
    lambda_p_b = (b / t) / (28.4 * epsilon * math.sqrt(4.0))
    if lambda_p_b <= 0.673:
        rho_b = 1.0
    else:
        rho_b = (lambda_p_b - 0.055 * 4.0) / (lambda_p_b ** 2)
    rho_b = min(1.0, max(0.0, rho_b))
    b_e2 = 0.5 * rho_b * b

    # Área y centro de gravedad del rigidizador eficaz As
    As = t * (c_eff + b_e2)
    # Centro de gravedad del rigidizador medido desde la línea media del ala hacia el labio
    y_s = (c_eff * t * (c_eff / 2.0)) / As
    # Inercia Is respecto al eje neutro paralelo al alma
    Is = (t * (c_eff ** 3) / 12.0) + (c_eff * t * ((c_eff / 2.0 - y_s) ** 2)) + (b_e2 * t * (y_s ** 2))

    # 2. Rigidez elástica de muelle K por unidad de longitud (EN 1993-1-3 ec. 5.10 / 5.11)
    b1 = b - (b_e2 / 2.0)
    D = (E_MPa * (t ** 3)) / (12.0 * (1.0 - nu ** 2))

    if loading == "bending":
        # En flexión, el ala traccionada estabiliza el alma
        delta = (1.0 / (E_MPa * (t ** 3))) * (1.0 - nu ** 2) * (b1 ** 2) * ((2.0 * h / 3.0) + 4.0 * b1)
    else:
        # En compresión uniforme pura
        delta = (4.0 / (E_MPa * (t ** 3))) * (1.0 - nu ** 2) * ((b1 ** 2) * h + (b1 ** 3))

    K = 1.0 / max(delta, 1e-12)

    # 3. Tensión crítica elástica del rigidizador σ_cr,s (ec. 5.15)
    sigma_cr_s = (2.0 * math.sqrt(K * E_MPa * Is)) / max(As, 1e-6)

    # 4. Esbeltez relativa λ_bar_d (ec. 5.13)
    lambda_bar_d = math.sqrt(fyb_MPa / max(sigma_cr_s, 1e-6))

    # 5. Factor de reducción distorsional χ_d (ec. 5.12)
    if lambda_bar_d <= 0.65:
        chi_d = 1.0
    elif lambda_bar_d < 1.38:
        chi_d = 1.47 - 0.723 * lambda_bar_d
    else:
        chi_d = 0.66 / lambda_bar_d
    chi_d = min(1.0, max(0.05, chi_d))

    # Espesor reducido y área reducida
    t_red = chi_d * t
    As_red = chi_d * As

    # 6. Capacidades resistentes de diseño EN 1993-1-3
    # Área eficaz total aproximada: Aeff = As_red (alas) + b_e1*t + h_eff*t
    # Para compresión pura: alma k_sigma=4.0
    lambda_p_h = (h / t) / (28.4 * epsilon * math.sqrt(4.0))
    rho_h = min(1.0, max(0.0, (lambda_p_h - 0.22) / (lambda_p_h ** 2))) if lambda_p_h > 0.673 else 1.0
    h_eff = rho_h * h
    b_e1 = 0.5 * rho_b * b
    A_eff = 2.0 * As_red + 2.0 * (b_e1 * t) + (h_eff * t)

    Nc_Rd = (A_eff * fyb_MPa / gamma_M0) / 1000.0  # kN

    # Flexión (eje fuerte): W_eff aproximado considerando t_red en el ala comprimida
    I_eff = (
        (t * (h ** 3) / 12.0)
        + (b * t_red * ((h / 2.0) ** 2))
        + (b * t * ((h / 2.0) ** 2))
        + (t_red * (c ** 3) / 12.0 + c * t_red * ((h / 2.0 - c / 2.0) ** 2))
        + (t * (c ** 3) / 12.0 + c * t * ((h / 2.0 - c / 2.0) ** 2))
    )
    W_eff = I_eff / (h / 2.0)
    Mc_Rd = (W_eff * fyb_MPa / gamma_M0) / 1e6  # kN·m

    return DistortionalResultEC3(
        standard="EN 1993-1-3:2006",
        method="Effective Width Method (EWM §5.5.3 Edge Stiffener)",
        K_spring_N_per_mm2=round(K, 4),
        As_eff_mm2=round(As, 2),
        Is_eff_mm4=round(Is, 2),
        sigma_cr_s_MPa=round(sigma_cr_s, 2),
        lambda_bar_d=round(lambda_bar_d, 3),
        chi_d=round(chi_d, 3),
        t_red_mm=round(t_red, 3),
        As_red_mm2=round(As_red, 2),
        Nc_Rd_kN=round(Nc_Rd, 2),
        Mc_Rd_kNm=round(Mc_Rd, 3),
        is_valid_ec3=is_valid,
        validity_notes=notes,
    )


__all__ = [
    "SectionGeometryCZ",
    "DistortionalResultAISI",
    "DistortionalResultEC3",
    "check_aisi_dsm_applicability",
    "check_ec3_applicability",
    "aisi_distortional_buckling",
    "ec3_distortional_buckling",
]
