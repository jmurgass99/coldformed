"""Tests para coldformed.surrogates — metamodelo sustituto del FSM.

Todos los tests son deterministas (semilla fija) y usan un dataset pequeño
para que la ejecución sea rápida.
"""
import numpy as np
import pytest

from coldformed.fsm import PlateBucklingInput, plate_critical_stress
from coldformed.surrogates import (
    FEATURE_NAMES,
    PlateBucklingSurrogate,
    SurrogateMetrics,
    build_dataset,
    train_surrogate,
)

SEED = 0
# n_samples pequeño para test rápido. A 400 muestras el R2 en el holdout de
# σ_cr (espacio lineal) se estabiliza por encima de 0.9; con holdouts más
# pequeños una sola geometría de σ_cr muy alta domina el ratio de varianza.
N_SAMPLES = 400


class TestBuildDataset:
    def test_shapes_correctas(self):
        X, y = build_dataset(n_samples=N_SAMPLES, seed=SEED)
        assert X.shape == (N_SAMPLES, len(FEATURE_NAMES))
        assert y.shape == (N_SAMPLES,)

    def test_sin_nan_ni_inf(self):
        X, y = build_dataset(n_samples=N_SAMPLES, seed=SEED)
        assert np.all(np.isfinite(X))
        assert np.all(np.isfinite(y))

    def test_target_positivo(self):
        _, y = build_dataset(n_samples=N_SAMPLES, seed=SEED)
        assert np.all(y > 0.0)

    def test_reproducible(self):
        X1, y1 = build_dataset(n_samples=N_SAMPLES, seed=SEED)
        X2, y2 = build_dataset(n_samples=N_SAMPLES, seed=SEED)
        assert np.array_equal(X1, X2)
        assert np.array_equal(y1, y2)

    def test_n_samples_invalido(self):
        with pytest.raises(ValueError):
            build_dataset(n_samples=0, seed=SEED)


class TestTrainSurrogate:
    def test_r2_supera_umbral(self):
        result = train_surrogate(n_samples=N_SAMPLES, seed=SEED, test_size=0.25)
        # El FSM es suave; un GBR sobre log(target) lo ajusta muy bien.
        assert result.metrics.r2 > 0.9

    def test_metricas_tipo_y_signo(self):
        result = train_surrogate(n_samples=N_SAMPLES, seed=SEED, test_size=0.25)
        assert isinstance(result.metrics, SurrogateMetrics)
        assert result.metrics.mae >= 0.0
        assert result.metrics.n_train + result.metrics.n_test == N_SAMPLES

    def test_test_size_invalido(self):
        with pytest.raises(ValueError):
            train_surrogate(n_samples=N_SAMPLES, seed=SEED, test_size=1.5)


class TestPlateBucklingSurrogate:
    @pytest.fixture(scope="class")
    def surrogate(self):
        return PlateBucklingSurrogate.train(n_samples=N_SAMPLES, seed=SEED)

    def test_predict_caso_conocido_dict(self, surrogate):
        # Punto interior al rango de entrenamiento.
        feats = {
            "width_mm": 150.0,
            "thickness_mm": 2.0,
            "E_MPa": 210_000.0,
            "nu": 0.30,
            "k": 4.0,
        }
        pred = surrogate.predict(feats)
        assert isinstance(pred, float)
        assert np.isfinite(pred)
        assert pred > 0.0

        # Comparación contra el FSM (ground truth) con tolerancia laxa.
        truth = plate_critical_stress(PlateBucklingInput(
            width_mm=150.0, thickness_mm=2.0, E_MPa=210_000.0,
            nu=0.30, boundary="ss_ss",
        )).sigma_cr_MPa
        rel_err = abs(pred - truth) / truth
        assert rel_err < 0.25

    def test_predict_acepta_plate_input(self, surrogate):
        data = PlateBucklingInput(
            width_mm=150.0, thickness_mm=2.0, boundary="ss_ss",
        )
        pred = surrogate.predict(data)
        truth = plate_critical_stress(data).sigma_cr_MPa
        assert abs(pred - truth) / truth < 0.25

    def test_predict_array_1d(self, surrogate):
        pred = surrogate.predict([150.0, 2.0, 210_000.0, 0.30, 4.0])
        assert isinstance(pred, float)
        assert pred > 0.0

    def test_predict_lote_2d(self, surrogate):
        batch = np.array([
            [150.0, 2.0, 210_000.0, 0.30, 4.0],
            [100.0, 3.0, 210_000.0, 0.30, 6.97],
            [250.0, 1.5, 210_000.0, 0.30, 0.425],
        ])
        preds = surrogate.predict(batch)
        assert isinstance(preds, np.ndarray)
        assert preds.shape == (3,)
        assert np.all(np.isfinite(preds))
        assert np.all(preds > 0.0)

    def test_metrics_property(self, surrogate):
        assert isinstance(surrogate.metrics, SurrogateMetrics)
        assert surrogate.metrics.r2 > 0.9

    def test_dict_incompleto_lanza(self, surrogate):
        with pytest.raises(KeyError):
            surrogate.predict({"width_mm": 150.0})


def test_inferencia_en_lote_consistente_con_fsm():
    """El surrogate predice un lote coherente con el FSM (sin assert de timing)."""
    surrogate = PlateBucklingSurrogate.train(n_samples=N_SAMPLES, seed=SEED)
    inputs = [
        PlateBucklingInput(width_mm=120.0, thickness_mm=2.5, boundary="ss_ss"),
        PlateBucklingInput(width_mm=200.0, thickness_mm=2.0, boundary="cc"),
        PlateBucklingInput(width_mm=80.0, thickness_mm=1.5, boundary="cs"),
    ]
    X = np.array([
        [d.width_mm, d.thickness_mm, d.E_MPa, d.nu,
         plate_critical_stress(d).k]
        for d in inputs
    ])
    preds = surrogate.predict(X)
    truths = np.array([plate_critical_stress(d).sigma_cr_MPa for d in inputs])
    assert preds.shape == truths.shape
    # Coherencia global: error relativo medio razonable en puntos interiores.
    rel = np.abs(preds - truths) / truths
    assert np.median(rel) < 0.25
