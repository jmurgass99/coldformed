"""
Metamodelo sustituto (AI surrogate) para el esfuerzo crítico de pandeo
elástico de placas.

Este módulo entrena un regresor de scikit-learn que aprende a reproducir el
mapa físico calculado por el FSM (:func:`coldformedjm.fsm.plate_critical_stress`)
a partir de las dimensiones y propiedades de la placa. Una vez entrenado, el
surrogate evalúa σ_cr de forma vectorizada (lote completo en una sola llamada),
mucho más rápido que invocar el FSM punto a punto cuando hay que barrer
miles de geometrías (optimización, análisis de sensibilidad, etc.).

El FSM subyacente es la solución cerrada de Bryan/Timoshenko:

    σ_cr = k · π² · E / (12·(1 - ν²)) · (t / b)²

que es suave y monótona; por ello un ``GradientBoostingRegressor`` la ajusta
con altísima fidelidad. El target abarca varios órdenes de magnitud (por el
factor (t/b)²), así que se entrena sobre log(σ_cr) mediante
``TransformedTargetRegressor`` para mantener bajo el error relativo en todo
el rango.

Features usadas (en este orden):
    0. width_mm      — ancho de la placa b [mm]
    1. thickness_mm  — espesor t [mm]
    2. E_MPa         — módulo de Young [MPa]
    3. nu            — coeficiente de Poisson [-]
    4. k             — coeficiente de pandeo de placa [-]

El coeficiente de pandeo ``k`` (que depende de la condición de borde
``boundary``) se incluye como feature numérica directa: la condición de borde
sólo entra en la física a través de este escalar, de modo que no hace falta
codificación one-hot.

Target:
    y = σ_cr [MPa]  (esfuerzo crítico de pandeo elástico)

Nota: el término "microsegundos" no aplica aquí; el FSM devuelve y el
surrogate predice un esfuerzo en MPa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from coldformedjm.fsm import PLATE_K, PlateBucklingInput, plate_critical_stress

try:
    from sklearn.compose import TransformedTargetRegressor
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:  # pragma: no cover - sólo si falta sklearn
    raise ImportError(
        "El módulo de surrogates requiere scikit-learn. "
        "Instálalo con: pip install scikit-learn"
    ) from exc


# Orden canónico de las features en la matriz X.
FEATURE_NAMES: tuple[str, ...] = (
    "width_mm",
    "thickness_mm",
    "E_MPa",
    "nu",
    "k",
)

# Rangos de muestreo razonables para perfiles conformados en frío.
# (mínimo, máximo) en unidades coherentes con PlateBucklingInput.
SAMPLING_RANGES: dict[str, tuple[float, float]] = {
    "width_mm": (20.0, 400.0),       # anchos de almas/alas típicos
    "thickness_mm": (0.5, 6.0),      # calibres de chapa fina
    "E_MPa": (200_000.0, 215_000.0), # acero estructural (banda estrecha)
    "nu": (0.25, 0.35),              # Poisson del acero
}


def _features_from_input(data: PlateBucklingInput) -> list[float]:
    """Extrae el vector de features (en :data:`FEATURE_NAMES`) de un input FSM."""
    k = data.k_override if data.k_override is not None else PLATE_K[data.boundary]
    return [data.width_mm, data.thickness_mm, data.E_MPa, data.nu, float(k)]


def build_dataset(n_samples: int = 400, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Genera un dataset (X, y) muestreando inputs físicos y evaluando el FSM.

    Se muestrean aleatoriamente, de forma uniforme e independiente, los
    parámetros de :class:`~coldformedjm.fsm.PlateBucklingInput` dentro de los
    rangos documentados en :data:`SAMPLING_RANGES`. La condición de borde se
    elige uniformemente entre las claves de
    :data:`~coldformedjm.fsm.PLATE_K`; el coeficiente ``k`` resultante se usa
    como feature. Para cada muestra se llama a
    :func:`~coldformedjm.fsm.plate_critical_stress` (ground truth) y se toma
    ``sigma_cr_MPa`` como target.

    Args:
        n_samples: número de muestras a generar (filas de X / y).
        seed: semilla para ``np.random.default_rng`` (reproducibilidad).

    Returns:
        (X, y): X de forma ``(n_samples, len(FEATURE_NAMES))`` con las features
        en el orden de :data:`FEATURE_NAMES`; y de forma ``(n_samples,)`` con
        el esfuerzo crítico σ_cr en MPa.
    """
    if n_samples <= 0:
        raise ValueError("n_samples debe ser > 0")

    rng = np.random.default_rng(seed)
    boundaries = sorted(PLATE_K)

    widths = rng.uniform(*SAMPLING_RANGES["width_mm"], size=n_samples)
    thicknesses = rng.uniform(*SAMPLING_RANGES["thickness_mm"], size=n_samples)
    E_vals = rng.uniform(*SAMPLING_RANGES["E_MPa"], size=n_samples)
    nu_vals = rng.uniform(*SAMPLING_RANGES["nu"], size=n_samples)
    boundary_idx = rng.integers(0, len(boundaries), size=n_samples)

    X = np.empty((n_samples, len(FEATURE_NAMES)), dtype=float)
    y = np.empty(n_samples, dtype=float)

    for i in range(n_samples):
        data = PlateBucklingInput(
            width_mm=float(widths[i]),
            thickness_mm=float(thicknesses[i]),
            E_MPa=float(E_vals[i]),
            nu=float(nu_vals[i]),
            boundary=boundaries[int(boundary_idx[i])],
        )
        res = plate_critical_stress(data)
        X[i, :] = _features_from_input(data)
        y[i] = res.sigma_cr_MPa

    return X, y


@dataclass(frozen=True)
class SurrogateMetrics:
    """Métricas de desempeño del surrogate en el conjunto de holdout."""

    r2: float
    mae: float
    n_train: int
    n_test: int

    def to_dict(self) -> dict[str, float]:
        return {
            "r2": self.r2,
            "mae": self.mae,
            "n_train": float(self.n_train),
            "n_test": float(self.n_test),
        }


@dataclass(frozen=True)
class TrainResult:
    """Resultado del entrenamiento: modelo entrenado y métricas en holdout."""

    model: TransformedTargetRegressor
    metrics: SurrogateMetrics
    feature_names: tuple[str, ...] = FEATURE_NAMES


def _build_pipeline(seed: int) -> TransformedTargetRegressor:
    """Construye el pipeline (StandardScaler + GBR) sobre target log-transformado.

    El esfuerzo crítico abarca varios órdenes de magnitud por el factor
    (t/b)²; entrenar sobre ``log(σ_cr)`` (y exponenciar al predecir) mantiene
    el error *relativo* bajo en todo el rango.
    """
    base = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "gbr",
                GradientBoostingRegressor(
                    n_estimators=500,
                    learning_rate=0.05,
                    max_depth=4,
                    subsample=1.0,
                    random_state=seed,
                ),
            ),
        ]
    )
    return TransformedTargetRegressor(
        regressor=base, func=np.log, inverse_func=np.exp
    )


def train_surrogate(
    n_samples: int = 400, seed: int = 0, test_size: float = 0.25
) -> TrainResult:
    """Entrena el surrogate y evalúa su desempeño en un holdout reproducible.

    Genera el dataset con :func:`build_dataset`, separa un conjunto de prueba
    con ``train_test_split`` (semilla fija), entrena un
    ``GradientBoostingRegressor`` (en pipeline con ``StandardScaler`` y target
    log-transformado) y calcula R² y MAE sobre el holdout.

    Args:
        n_samples: tamaño total del dataset generado.
        seed: semilla compartida por el muestreo, el split y el modelo.
        test_size: fracción reservada para el holdout (0 < test_size < 1).

    Returns:
        :class:`TrainResult` con el modelo entrenado y las
        :class:`SurrogateMetrics` del holdout.
    """
    if not (0.0 < test_size < 1.0):
        raise ValueError("test_size debe estar en (0, 1)")

    X, y = build_dataset(n_samples=n_samples, seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )

    model = _build_pipeline(seed)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = SurrogateMetrics(
        r2=float(r2_score(y_test, y_pred)),
        mae=float(mean_absolute_error(y_test, y_pred)),
        n_train=int(X_train.shape[0]),
        n_test=int(X_test.shape[0]),
    )
    return TrainResult(model=model, metrics=metrics)


class PlateBucklingSurrogate:
    """Envoltura de inferencia sobre el pipeline de surrogate entrenado.

    Acepta features como ``dict`` (claves en :data:`FEATURE_NAMES`), como
    objeto :class:`~coldformedjm.fsm.PlateBucklingInput`, o como array/lista
    numérica (un punto 1-D o un lote 2-D), y devuelve el esfuerzo crítico de
    pandeo estimado σ_cr en MPa.

    Ejemplo:
        >>> surr = PlateBucklingSurrogate.train(n_samples=300, seed=0)
        >>> surr.predict({"width_mm": 150, "thickness_mm": 2.0,
        ...               "E_MPa": 210000, "nu": 0.30, "k": 4.0})  # doctest: +SKIP
    """

    def __init__(self, train_result: TrainResult):
        self._result = train_result
        self._model = train_result.model
        self._feature_names = train_result.feature_names

    @classmethod
    def train(
        cls, n_samples: int = 400, seed: int = 0, test_size: float = 0.25
    ) -> "PlateBucklingSurrogate":
        """Atajo: entrena con :func:`train_surrogate` y envuelve el resultado."""
        return cls(train_surrogate(n_samples=n_samples, seed=seed, test_size=test_size))

    @property
    def metrics(self) -> SurrogateMetrics:
        """Métricas del holdout obtenidas en el entrenamiento."""
        return self._result.metrics

    @property
    def feature_names(self) -> tuple[str, ...]:
        """Nombres de las features en el orden esperado por :meth:`predict`."""
        return self._feature_names

    def _to_matrix(
        self,
        features: Mapping[str, float]
        | PlateBucklingInput
        | Sequence[float]
        | np.ndarray,
    ) -> np.ndarray:
        """Normaliza la entrada heterogénea a una matriz 2-D (n, n_features)."""
        if isinstance(features, PlateBucklingInput):
            return np.asarray([_features_from_input(features)], dtype=float)
        if isinstance(features, Mapping):
            try:
                row = [float(features[name]) for name in self._feature_names]
            except KeyError as exc:
                raise KeyError(
                    f"Falta la feature {exc} en el dict; "
                    f"se esperan {self._feature_names}"
                ) from exc
            return np.asarray([row], dtype=float)

        arr = np.asarray(features, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2 or arr.shape[1] != len(self._feature_names):
            raise ValueError(
                f"Se esperaban {len(self._feature_names)} features por muestra "
                f"({self._feature_names}); recibido shape {arr.shape}"
            )
        return arr

    def predict(
        self,
        features: Mapping[str, float]
        | PlateBucklingInput
        | Sequence[float]
        | np.ndarray,
    ) -> float | np.ndarray:
        """Predice σ_cr [MPa] para un punto o un lote de features.

        Args:
            features: un ``dict`` con claves :data:`FEATURE_NAMES`, un
                :class:`~coldformedjm.fsm.PlateBucklingInput`, un array 1-D
                (un punto) o un array 2-D ``(n, n_features)`` (lote).

        Returns:
            Un ``float`` si la entrada es un único punto, o un ``np.ndarray``
            de forma ``(n,)`` si es un lote.
        """
        X = self._to_matrix(features)
        y_pred = self._model.predict(X)
        if y_pred.shape[0] == 1 and not (
            isinstance(features, np.ndarray) and features.ndim == 2
        ):
            return float(y_pred[0])
        return np.asarray(y_pred, dtype=float)


__all__ = [
    "FEATURE_NAMES",
    "SAMPLING_RANGES",
    "SurrogateMetrics",
    "TrainResult",
    "build_dataset",
    "train_surrogate",
    "PlateBucklingSurrogate",
]
