"""Metamodelo de pandeo de placa (extra `ml`): entrenar, medir en holdout y predecir un lote.

`PlateBucklingSurrogate` entrena un GradientBoosting sobre log(σ_cr) con 2 000 muestras
generadas por la solución de Bryan, mide R² y MAE en un holdout reproducible y predice
en una sola llamada un lote de geometrías. Se compara la predicción con el cálculo
directo para 6 placas. Útil en barridos de miles de geometrías; para una placa suelta
la fórmula cerrada es más rápida y exacta. Requiere `pip install "coldformed[ml]"`.

Ejecutar:  python examples/surrogate_batch_prediction_vs_fsm.py
"""
import numpy as np

from coldformed.fsm import PlateBucklingInput, plate_critical_stress
from coldformed.surrogates import PlateBucklingSurrogate

BATCH = [
    (100.0, 1.0, 4.0), (150.0, 2.0, 4.0), (200.0, 2.0, 0.425),
    (250.0, 3.0, 4.0), (80.0, 1.5, 6.97), (300.0, 2.5, 5.42),
]


def main() -> None:
    surr = PlateBucklingSurrogate.train(n_samples=2000, seed=0)
    m = surr.metrics
    print(f"Holdout: R² = {m.r2:.4f}, MAE = {m.mae:.2f} MPa (n_train = {m.n_train}, n_test = {m.n_test})\n")

    X = np.array([[b, t, 210_000.0, 0.30, k] for b, t, k in BATCH])
    pred = np.atleast_1d(surr.predict(X))
    print(f"{'b':>5} {'t':>4} {'k':>6} {'σ_cr Bryan':>11} {'σ_cr surrogate':>15} {'error':>7}")
    for (b, t, k), p in zip(BATCH, pred):
        ref = plate_critical_stress(PlateBucklingInput(b, t, k_override=k)).sigma_cr_MPa
        print(f"{b:5.0f} {t:4.1f} {k:6.3f} {ref:11.2f} {p:15.2f} {p / ref - 1:+7.1%}")


if __name__ == "__main__":
    main()
