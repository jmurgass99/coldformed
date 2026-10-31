"""Coste y huella de carbono de un pedido de correas por país.

Pedido de 240 correas C de 6 m a 5,50 kg/m, galvanizadas. `cost_estimate` aplica la
tarifa USD/t del país, el recargo por conformado del tipo de perfil y el 5 % del
galvanizado; `co2_estimate` usa un coeficiente t CO₂/t por país. Las tarifas son
estimativas (Q2-2025) y están en el propio módulo: sustitúyelas por tus cotizaciones.

Ejecutar:  python examples/purlin_order_cost_and_co2_by_country.py
"""
from coldformed.cost_estimator import CostInput, co2_estimate, cost_estimate


def main() -> None:
    print(f"{'país':<8} {'USD/t ef.':>10} {'peso [kg]':>10} {'total USD':>10} {'t CO₂':>7}")
    for country in ("CL", "CO", "US", "EU", "AU", "SG"):
        r = cost_estimate(CostInput(profile_type="C", weight_per_m_kg=5.50, length_m=6.0, country=country,
                                    quantity=240, galvanized=True))
        print(f"{country:<8} {r['usd_per_ton_effective']:10.0f} {r['total_weight_kg']:10.0f} {r['total_USD']:10.0f} "
              f"{co2_estimate(r['total_weight_kg'], country):7.2f}")
    r_sigma = cost_estimate(CostInput(profile_type="Sigma", weight_per_m_kg=6.18, length_m=6.0, country="EU", quantity=240))
    print(f"\nMismo pedido en perfil Σ (EU): {r_sigma['total_USD']:.0f} USD ({r_sigma['USD_per_kg']:.3f} USD/kg)")


if __name__ == "__main__":
    main()
