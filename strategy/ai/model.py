"""Modelo probabilístico del meta-etiquetado.

Regresión logística implementada con NumPy (sin dependencias nuevas) y una
calibración isotónica ligera para que la probabilidad sea comparable entre
workers e instrumentos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from strategy.ai.feature_extraction import FEATURE_NAMES


@dataclass
class LogisticRegressionModel:
    """Clasificador binario entrenado por descenso de gradiente.

    Implementacion propia con NumPy, sin scikit-learn, para no anadir
    dependencias al bot. Estandariza internamente las caracteristicas y
    guarda media y escala junto con los pesos, de modo que el modelo
    serializado es autosuficiente.

    Atributos:
        feature_names: nombres de las 20 caracteristicas, en orden.
        weights: pesos aprendidos, en el espacio estandarizado.
        bias: termino independiente.
        mean, scale: estadisticos de estandarizacion del entrenamiento.
        trained: si es False, `predict_proba` devuelve la tasa base.
        samples: numero de muestras con las que se entreno.
        positive_rate: proporcion de aciertos en el entrenamiento.

    Vinculaciones:
    - Lo envuelve `CalibratedLogisticModel` en este mismo modulo.
    - Lo entrena `strategy.ai.training.train_worker_model`.
    """

    feature_names: tuple[str, ...] = FEATURE_NAMES
    weights: list[float] = field(default_factory=list)
    bias: float = 0.0
    mean: list[float] = field(default_factory=list)
    scale: list[float] = field(default_factory=list)
    trained: bool = False
    samples: int = 0
    positive_rate: float = 0.0

    @staticmethod
    def _sigmoid(values: np.ndarray) -> np.ndarray:
        """Sigmoide estable: recorta a [-35, 35] para evitar desbordamiento en exp."""
        return 1.0 / (1.0 + np.exp(-np.clip(values, -35.0, 35.0)))

    def fit(
        self,
        features: np.ndarray | list[list[float]],
        labels: np.ndarray | list[int],
        *,
        learning_rate: float = 0.10,
        epochs: int = 600,
        l2: float = 1e-3,
    ) -> "LogisticRegressionModel":
        """Entrena los pesos por descenso de gradiente con regularizacion L2.

        Detalles relevantes:
        - Estandariza las caracteristicas y protege las de varianza nula
          fijando su escala a 1.0, evitando dividir por cero.
        - El sesgo NO arranca en cero sino en el log-odds de la muestra, lo
          que acelera la convergencia cuando las clases estan desbalanceadas.
        - La regularizacion L2 se aplica solo a los pesos, no al sesgo.

        Args:
            features: matriz de muestras x caracteristicas.
            labels: vector binario (1 = operacion ganadora).
            learning_rate: tasa de aprendizaje.
            epochs: iteraciones completas sobre el conjunto.
            l2: intensidad de la regularizacion.

        Returns:
            El propio modelo, para poder encadenar. Si la matriz esta vacia o
            no cuadra con las etiquetas, deja `trained=False` y no lanza
            excepcion.

        Vinculaciones:
        - Lo llama `CalibratedLogisticModel` a traves de
          `strategy.ai.training.train_worker_model`.
        """
        matrix = np.asarray(features, dtype=float)
        target = np.asarray(labels, dtype=float).ravel()
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != target.shape[0]:
            self.trained = False
            return self

        mean = matrix.mean(axis=0)
        scale = matrix.std(axis=0)
        scale[scale < 1e-9] = 1.0
        standard = (matrix - mean) / scale

        rows, columns = standard.shape
        weights = np.zeros(columns, dtype=float)
        bias = 0.0
        # Arranque informado: el sesgo parte del log-odds de la muestra.
        positive_rate = float(np.clip(target.mean(), 1e-6, 1 - 1e-6))
        bias = float(np.log(positive_rate / (1.0 - positive_rate)))

        for _ in range(max(1, int(epochs))):
            predictions = self._sigmoid(standard @ weights + bias)
            error = predictions - target
            gradient_w = (standard.T @ error) / rows + l2 * weights
            gradient_b = float(error.mean())
            weights -= learning_rate * gradient_w
            bias -= learning_rate * gradient_b

        self.weights = [float(value) for value in weights]
        self.bias = float(bias)
        self.mean = [float(value) for value in mean]
        self.scale = [float(value) for value in scale]
        self.samples = int(rows)
        self.positive_rate = float(target.mean())
        self.trained = True
        return self

    def predict_proba(self, features: np.ndarray | list[list[float]]) -> np.ndarray:
        """Devuelve la probabilidad de exito de cada muestra.

        SALVAGUARDA IMPORTANTE: si el modelo no esta entrenado devuelve la
        tasa base (`positive_rate`, o 0.5 si no la conoce) en vez de fallar.
        Es la pieza que permite al motor operar en modo sombra sin modelo.

        Args:
            features: matriz o vector unico (se redimensiona solo).

        Returns:
            Array de probabilidades entre 0 y 1.
        """
        matrix = np.asarray(features, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        if not self.trained or not self.weights:
            return np.full(matrix.shape[0], float(self.positive_rate or 0.5))
        mean = np.asarray(self.mean, dtype=float)
        scale = np.asarray(self.scale, dtype=float)
        weights = np.asarray(self.weights, dtype=float)
        standard = (matrix - mean) / scale
        return self._sigmoid(standard @ weights + self.bias)

    def predict_one(self, vector: list[float]) -> float:
        """Atajo para puntuar una sola senal. Devuelve la probabilidad como float."""
        return float(self.predict_proba([vector])[0])

    def to_dict(self) -> dict:
        """Serializa el modelo completo a un dict apto para JSON.

        Incluye media y escala ademas de los pesos, de modo que el modelo
        restaurado no necesita el conjunto de entrenamiento original.

        Vinculaciones:
        - Lo usa `strategy.ai.meta_labeling.MetaLabelingEngine.save_model`
          para persistir el modelo por worker en disco.
        """
        return {
            "feature_names": list(self.feature_names),
            "weights": list(self.weights),
            "bias": float(self.bias),
            "mean": list(self.mean),
            "scale": list(self.scale),
            "trained": bool(self.trained),
            "samples": int(self.samples),
            "positive_rate": float(self.positive_rate),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "LogisticRegressionModel":
        """Reconstruye el modelo desde su forma serializada.

        Tolerante a datos corruptos o incompletos: si `payload` no es un dict
        o le faltan claves, devuelve un modelo sin entrenar en lugar de
        lanzar excepcion. Asi un fichero danado degrada a modo sombra en vez
        de tumbar el bot.

        Vinculaciones:
        - Lo usa `strategy.ai.meta_labeling.MetaLabelingEngine.load_model`.
        """
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            feature_names=tuple(payload.get("feature_names") or FEATURE_NAMES),
            weights=[float(v) for v in (payload.get("weights") or [])],
            bias=float(payload.get("bias", 0.0)),
            mean=[float(v) for v in (payload.get("mean") or [])],
            scale=[float(v) for v in (payload.get("scale") or [])],
            trained=bool(payload.get("trained", False)),
            samples=int(payload.get("samples", 0)),
            positive_rate=float(payload.get("positive_rate", 0.0)),
        )


@dataclass
class ProbabilityCalibrator:
    """Calibración por binning isotónico: ajusta la probabilidad a la frecuencia real.

    La regresion logistica suele estar mal calibrada: cuando dice 0.80 quiza
    la frecuencia real de acierto sea 0.65. Este calibrador corrige ese sesgo
    agrupando las predicciones en tramos y sustituyendo cada tramo por la
    frecuencia observada, forzando ademas que la curva no decrezca.

    Es imprescindible para el modo FILTRO: sin calibrar, un umbral de
    probabilidad no significaria lo que dice.

    Vinculaciones:
    - Lo envuelve `CalibratedLogisticModel` en este mismo modulo.
    - Lo ajusta `strategy.ai.training.train_worker_model`.
    """

    bin_edges: list[float] = field(default_factory=list)
    bin_values: list[float] = field(default_factory=list)
    trained: bool = False

    def fit(
        self,
        probabilities: np.ndarray | list[float],
        labels: np.ndarray | list[int],
        *,
        bins: int = 10,
    ) -> "ProbabilityCalibrator":
        """Ajusta la curva de calibracion sobre probabilidades ya predichas.

        Proceso:
        1. Limita el numero de tramos segun la muestra (aprox. 5 casos por
           tramo) para no crear tramos vacios con pocos datos.
        2. Calcula la frecuencia real de acierto dentro de cada tramo; los
           tramos sin datos heredan la tasa global.
        3. Fuerza monotonia no decreciente, que es lo que hace que la
           calibracion sea isotonica.

        ANTIFUGA: estas probabilidades deben proceder de datos NO usados para
        entrenar el modelo base. En `temporal_validation` el calibrador se
        ajusta con la cola del bloque de entrenamiento, nunca con el test.

        Args:
            probabilities: probabilidades crudas del modelo.
            labels: resultados reales (1 = acierto).
            bins: numero maximo de tramos.

        Returns:
            El propio calibrador. Si los datos estan vacios o descuadrados,
            queda con `trained=False` y `calibrate` pasa a ser identidad.
        """
        probs = np.asarray(probabilities, dtype=float).ravel()
        target = np.asarray(labels, dtype=float).ravel()
        if probs.size == 0 or probs.size != target.size:
            self.trained = False
            return self

        bins = max(2, min(int(bins), max(2, probs.size // 5 or 2)))
        edges = np.linspace(0.0, 1.0, bins + 1)
        values = []
        global_rate = float(target.mean())
        for index in range(bins):
            low, high = edges[index], edges[index + 1]
            if index == bins - 1:
                mask = (probs >= low) & (probs <= high)
            else:
                mask = (probs >= low) & (probs < high)
            values.append(float(target[mask].mean()) if mask.any() else global_rate)

        # Monotonía: la probabilidad calibrada nunca debe decrecer.
        for index in range(1, len(values)):
            values[index] = max(values[index], values[index - 1])

        self.bin_edges = [float(v) for v in edges]
        self.bin_values = values
        self.trained = True
        return self

    def calibrate(self, probability: float) -> float:
        """Corrige una probabilidad cruda usando la curva aprendida.

        Si el calibrador no esta entrenado actua como identidad (solo recorta
        al rango 0-1), de modo que el modelo sigue siendo utilizable.

        Returns:
            Probabilidad calibrada entre 0 y 1.
        """
        value = float(np.clip(probability, 0.0, 1.0))
        if not self.trained or not self.bin_values:
            return value
        edges = self.bin_edges
        for index in range(len(self.bin_values)):
            high = edges[index + 1]
            if value < high or index == len(self.bin_values) - 1:
                return float(np.clip(self.bin_values[index], 0.0, 1.0))
        return value

    def to_dict(self) -> dict:
        """Serializa la curva de calibracion a un dict apto para JSON."""
        return {
            "bin_edges": list(self.bin_edges),
            "bin_values": list(self.bin_values),
            "trained": bool(self.trained),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ProbabilityCalibrator":
        """Reconstruye el calibrador, tolerando datos ausentes o corruptos."""
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            bin_edges=[float(v) for v in (payload.get("bin_edges") or [])],
            bin_values=[float(v) for v in (payload.get("bin_values") or [])],
            trained=bool(payload.get("trained", False)),
        )


@dataclass
class CalibratedLogisticModel:
    """Modelo entrenado por worker: regresión logística + calibración.

    Es la unidad que se persiste en disco: un modelo INDEPENDIENTE por worker,
    tal y como se diseno el meta-etiquetado. Ademas de la probabilidad guarda
    la ganancia y perdida medias en R del worker, necesarias para convertir
    esa probabilidad en expectativa monetaria.

    Atributos:
        worker: identificador del worker (por ejemplo `VOLATILITY_1`).
        strategy_name: estrategia asociada, o `ALL`.
        model: la regresion logistica.
        calibrator: la curva de calibracion.
        trained_at: marca temporal del entrenamiento.
        average_win_rr / average_loss_rr: medias historicas en R.

    Vinculaciones:
    - Lo crea `strategy.ai.training.train_worker_model`.
    - Lo carga, guarda y consulta `strategy.ai.meta_labeling.MetaLabelingEngine`.
    """

    worker: str = "DEFAULT"
    strategy_name: str = "ALL"
    model: LogisticRegressionModel = field(default_factory=LogisticRegressionModel)
    calibrator: ProbabilityCalibrator = field(default_factory=ProbabilityCalibrator)
    trained_at: str | None = None
    average_win_rr: float = 1.0
    average_loss_rr: float = 1.0

    @property
    def trained(self) -> bool:
        """Indica si el modelo base esta entrenado. La calibracion es opcional."""
        return bool(self.model.trained)

    def probability(self, vector: list[float]) -> float:
        """Predice y calibra en un paso: probabilidad final de que la senal gane.

        Args:
            vector: caracteristicas en el orden de `FEATURE_NAMES`.

        Returns:
            Probabilidad calibrada entre 0 y 1.
        """
        raw = self.model.predict_one(vector)
        return float(self.calibrator.calibrate(raw))

    def net_expectancy_r(self, probability: float) -> float:
        """Expectativa neta en R: p*ganancia media - (1-p)*pérdida media.

        Traduce la probabilidad a valor esperado usando el historial real del
        worker. Es la segunda condicion del modo FILTRO: no basta con que la
        probabilidad sea alta, la expectativa tambien debe superar su umbral.
        Una senal con 60% de acierto pero recorrido corto puede ser peor que
        una del 45% con recorrido amplio.

        Args:
            probability: probabilidad calibrada, se recorta a 0-1.

        Returns:
            Expectativa en multiplos de R. Negativa significa que operar esa
            senal pierde dinero a largo plazo.

        Vinculaciones:
        - La llama `strategy.ai.meta_labeling.MetaLabelingEngine.score_signal`
          para decidir el filtro y para ordenar el ranking.
        """
        probability = float(np.clip(probability, 0.0, 1.0))
        win = abs(float(self.average_win_rr or 0.0))
        loss = abs(float(self.average_loss_rr or 0.0))
        return probability * win - (1.0 - probability) * loss

    def to_dict(self) -> dict:
        """Serializa modelo, calibrador y estadisticas de R a un dict JSON."""
        return {
            "worker": self.worker,
            "strategy_name": self.strategy_name,
            "model": self.model.to_dict(),
            "calibrator": self.calibrator.to_dict(),
            "trained_at": self.trained_at,
            "average_win_rr": float(self.average_win_rr),
            "average_loss_rr": float(self.average_loss_rr),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CalibratedLogisticModel":
        """Reconstruye el modelo por worker desde su fichero persistido.

        Tolerante a ficheros incompletos o corruptos: devuelve un modelo sin
        entrenar en lugar de fallar, de forma que el worker afectado degrada
        a modo sombra.

        Vinculaciones:
        - Lo usa `strategy.ai.meta_labeling.MetaLabelingEngine.load_model`.
        """
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            worker=str(payload.get("worker") or "DEFAULT"),
            strategy_name=str(payload.get("strategy_name") or "ALL"),
            model=LogisticRegressionModel.from_dict(payload.get("model") or {}),
            calibrator=ProbabilityCalibrator.from_dict(payload.get("calibrator") or {}),
            trained_at=payload.get("trained_at"),
            average_win_rr=float(payload.get("average_win_rr", 1.0)),
            average_loss_rr=float(payload.get("average_loss_rr", 1.0)),
        )
