"""Iteración de propiedades eficaces: el modelo global se resuelve con sección bruta y la real es menor.

Un alma de 250 mm y 1,5 mm en compresión recibe del modelo de barras una tensión de
120 MPa con la sección bruta. Al reducir el ancho eficaz, la tensión sube (menos área
para la misma carga) y hay que volver a reducir. `iterate_effective` repite el bucle
σ → b_eff → nuevo ratio → σ' hasta que el ratio b_eff/b converge. Aquí el modelo se
sustituye por una función que devuelve σ = σ₀ / ratio (la carga se reparte en el área
eficaz); en producción esa función reasigna los modificadores de propiedad en SAP2000
o ETABS y vuelve a correr el análisis.

Ejecutar:  python examples/effective_properties_iteration_with_fem_demand.py
"""
from coldformed.effective_iter import EffectiveIterInput, iterate_effective

SIGMA_GROSS = 120.0


def demand_from_model(ratio: float) -> float:
    """Tensión actuante que devolvería el modelo con el área eficaz actual."""
    return SIGMA_GROSS / max(ratio, 0.2)


def main() -> None:
    for tol in (0.05, 0.01, 0.001):
        res = iterate_effective(EffectiveIterInput(b_gross=250.0, t=1.5, sigma_demand_provider=demand_from_model,
                                                   sigma_y=350.0, tol=tol, max_iter=30))
        hist = ", ".join(f"{r:.3f}" for r in res.history)
        print(f"tol = {tol:<6} iteraciones = {res.iterations:2d}  convergió = {res.converged}  "
              f"b_eff/b final = {res.final_ratio:.3f}")
        print(f"         historia del ratio: {hist}")
    print("\nCon la sección bruta el alma parecía eficaz al 100 %; converge a un ratio bastante menor "
          "porque cada reducción eleva la tensión y vuelve a reducir.")


if __name__ == "__main__":
    main()
