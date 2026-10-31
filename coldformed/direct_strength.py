"""
Direct Strength Method (DSM) — AISI S100 / AS/NZS 4600, Schafer 2008.

Calcula resistencias nominales de flexión Mn y compresión Pn a partir
de los esfuerzos críticos de pandeo local (Mcrl/Pcrl), distorsional
(Mcrd/Pcrd) y global (Mcre/Pcre). Estos suelen venir de un análisis
FSM (ver `fsm.py`) o CUFSM.

Para flexión:
    My = Sf · Fy  (momento de fluencia)
    λ_l = √(My/Mcrl)
    Mnl = My                                    si λ_l ≤ 0.776
    Mnl = (1 - 0.15·(Mcrl/My)^0.4)·(Mcrl/My)^0.4·My  si λ_l > 0.776

    λ_d = √(My/Mcrd)
    Mnd = My                                    si λ_d ≤ 0.673
    Mnd = (1 - 0.22·(Mcrd/My)^0.5)·(Mcrd/My)^0.5·My  si λ_d > 0.673

    λ_e = √(My/Mcre)
    Mne = My                                    si Mcre ≥ 2.78·My (Lat.-torsional limit)
    ... (caso medio)
    Mne = (10/9)·My·(1 - 10·My/(36·Mcre))    si 0.56·My ≤ Mcre < 2.78·My
    Mne = Mcre                                  si Mcre < 0.56·My
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class DSMFlexureInput:
    Mcrl_kNm: float         # local buckling moment
    Mcrd_kNm: float         # distortional buckling moment
    Mcre_kNm: float         # global (lateral-torsional) buckling moment
    Sf_mm3: float           # módulo elástico de la sección
    Fy_MPa: float = 350.0


@dataclass(frozen=True)
class DSMFlexureResult:
    My_kNm: float
    Mnl_kNm: float
    Mnd_kNm: float
    Mne_kNm: float
    Mn_kNm: float           # mínimo gobernante
    governing_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "My_kNm": self.My_kNm,
            "Mnl_kNm": self.Mnl_kNm,
            "Mnd_kNm": self.Mnd_kNm,
            "Mne_kNm": self.Mne_kNm,
            "Mn_kNm": self.Mn_kNm,
            "governing_mode": self.governing_mode,
        }


def dsm_flexure(inp: DSMFlexureInput) -> DSMFlexureResult:
    if min(inp.Mcrl_kNm, inp.Mcrd_kNm, inp.Mcre_kNm) <= 0.0 or not all(
        math.isfinite(x) for x in (inp.Mcrl_kNm, inp.Mcrd_kNm, inp.Mcre_kNm)
    ):
        raise ValueError(
            f"Momentos críticos de pandeo deben ser estrictamente positivos y finitos: "
            f"Mcrl={inp.Mcrl_kNm}, Mcrd={inp.Mcrd_kNm}, Mcre={inp.Mcre_kNm}"
        )
    My = inp.Sf_mm3 * inp.Fy_MPa / 1e6  # kN·m
    # Mne (global)
    if inp.Mcre_kNm >= 2.78 * My:
        Mne = My
    elif inp.Mcre_kNm >= 0.56 * My:
        Mne = (10.0 / 9.0) * My * (1 - 10 * My / (36 * inp.Mcre_kNm))
    else:
        Mne = inp.Mcre_kNm

    # Mnl (local) — depende de Mne
    lam_l = sqrt(Mne / max(inp.Mcrl_kNm, 1e-9))
    if lam_l <= 0.776:
        Mnl = Mne
    else:
        ratio = inp.Mcrl_kNm / Mne
        Mnl = (1 - 0.15 * ratio ** 0.4) * ratio ** 0.4 * Mne

    # Mnd (distortional)
    lam_d = sqrt(My / max(inp.Mcrd_kNm, 1e-9))
    if lam_d <= 0.673:
        Mnd = My
    else:
        ratio_d = inp.Mcrd_kNm / My
        Mnd = (1 - 0.22 * ratio_d ** 0.5) * ratio_d ** 0.5 * My

    Mn = min(Mnl, Mnd, Mne)
    if Mn == Mnl:
        gov = "local"
    elif Mn == Mnd:
        gov = "distortional"
    else:
        gov = "global"

    return DSMFlexureResult(
        My_kNm=My, Mnl_kNm=Mnl, Mnd_kNm=Mnd, Mne_kNm=Mne,
        Mn_kNm=Mn, governing_mode=gov,
    )


@dataclass(frozen=True)
class DSMCompressionInput:
    Pcrl_kN: float
    Pcrd_kN: float
    Pcre_kN: float          # Euler
    A_mm2: float
    Fy_MPa: float = 350.0


def dsm_compression(inp: DSMCompressionInput) -> dict[str, Any]:
    if min(inp.Pcrl_kN, inp.Pcrd_kN, inp.Pcre_kN) <= 0.0 or not all(
        math.isfinite(x) for x in (inp.Pcrl_kN, inp.Pcrd_kN, inp.Pcre_kN)
    ):
        raise ValueError(
            f"Cargas críticas de pandeo deben ser estrictamente positivas y finitas: "
            f"Pcrl={inp.Pcrl_kN}, Pcrd={inp.Pcrd_kN}, Pcre={inp.Pcre_kN}"
        )
    Py = inp.A_mm2 * inp.Fy_MPa / 1000.0  # kN
    # Pne (global)
    lam_c = sqrt(Py / max(inp.Pcre_kN, 1e-9))
    if lam_c <= 1.5:
        Pne = (0.658 ** (lam_c ** 2)) * Py
    else:
        Pne = (0.877 / (lam_c ** 2)) * Py

    # Pnl
    lam_l = sqrt(Pne / max(inp.Pcrl_kN, 1e-9))
    if lam_l <= 0.776:
        Pnl = Pne
    else:
        r = inp.Pcrl_kN / Pne
        Pnl = (1 - 0.15 * r ** 0.4) * r ** 0.4 * Pne

    # Pnd
    lam_d = sqrt(Py / max(inp.Pcrd_kN, 1e-9))
    if lam_d <= 0.561:
        Pnd = Py
    else:
        r = inp.Pcrd_kN / Py
        Pnd = (1 - 0.25 * r ** 0.6) * r ** 0.6 * Py

    Pn = min(Pnl, Pnd, Pne)
    gov = "local" if Pn == Pnl else "distortional" if Pn == Pnd else "global"
    return {
        "Py_kN": Py, "Pne_kN": Pne, "Pnl_kN": Pnl, "Pnd_kN": Pnd,
        "Pn_kN": Pn, "governing_mode": gov,
    }


__all__ = [
    "DSMFlexureInput", "DSMFlexureResult", "dsm_flexure",
    "DSMCompressionInput", "dsm_compression",
]
