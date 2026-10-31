"""De la resistencia nominal a la de diseño: φ de AISI/AS frente a γ_M de EN 1993-1-3.

Para una misma resistencia nominal M_n = 18,2 kN·m y P_n = 95 kN se muestra qué
devuelve cada código: US, CO y AU multiplican por φ (0,90 en flexión, 0,85 en
compresión); EU y SG dividen por γ_M1 = 1,00. Un código no soportado lanza ValueError.

Ejecutar:  python examples/resistance_factors_by_code_dsm_vs_ewm.py
"""
from coldformed.codes_multi import code_description, design_resistance_compression, design_resistance_flexure

MN, PN = 18.2, 95.0


def main() -> None:
    print(f"M_n = {MN} kN·m, P_n = {PN} kN\n")
    print(f"{'código':<7} {'M_d [kN·m]':>10} {'P_d [kN]':>9}  norma")
    for code in ("US", "CO", "AU", "EU", "SG"):
        print(f"{code:<7} {design_resistance_flexure(code, MN):10.2f} {design_resistance_compression(code, PN):9.2f}  "
              f"{code_description(code)}")
    try:
        design_resistance_flexure("BR", MN)
    except ValueError as exc:
        print(f"\nCódigo no soportado: ValueError: {exc}")


if __name__ == "__main__":
    main()
