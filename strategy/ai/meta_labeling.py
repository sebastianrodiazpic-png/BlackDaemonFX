"""Motor de meta-etiquetado: modos sombra, filtro y ranking.

El motor nunca crea señales. Recibe la señal ya confirmada por una estrategia y
devuelve probabilidad calibrada, expectativa neta y una decisión auditable.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from strategy.ai.feature_extraction import extract_meta_features, feature_vector
from strategy.ai.model import CalibratedLogisticModel
from strategy.ai.training import build_training_dataset, temporal_validation, train_worker_model


SHADOW_MODE = "SHADOW"
FILTER_MODE = "FILTER"


@dataclass
class MetaLabelingConfig:
    """Configuración por worker del meta-etiquetado."""

    enabled: bool = True
    # SHADOW puntúa y registra sin bloquear ninguna entrada.
    mode: str = SHADOW_MODE
    min_probability: float = 0.55
    min_net_expectancy_r: float = 0.10
    ranking_enabled: bool = True
    max_signals_per_cycle: int = 1
    model_directory: str = "storage/ai_models"
    min_training_samples: int = 30
    # Sin modelo entrenado el filtro no debe bloquear operativa real.
    block_when_untrained: bool = False


@dataclass
class MetaLabelDecision:
    """Resultado auditable de puntuar una señal."""

    symbol: str
    worker: str
    strategy_name: str
    mode: str
    probability: float
    net_expectancy_r: float
    allowed: bool
    shadow: bool
    reason: str
    trained: bool
    features: dict = field(default_factory=dict)
    thresholds: dict = field(default_factory=dict)
    evaluated_at: str = ""

    def to_dict(self) -> dict:
        """Convierte la decision a dict plano para auditarla en la bitacora.

        Vinculaciones:
        - El resultado lo persiste `strategy.execution.live_trading_engine`
          como evento `META_LABEL_SIGNAL_SCORED`, que despues agrega
          `database.repository.meta_label_decision_summary` para el panel de
          IA de la pantalla Cuenta.
        """
        return asdict(self)


class MetaLabelingEngine:
    """Puntúa señales por worker con modelos independientes y persistentes.

    Nunca crea senales: recibe una ya confirmada por la estrategia y decide si
    dejarla pasar, con que probabilidad y con que prioridad.

    Modos de operacion:
    - `SHADOW`: observa y registra sin afectar a la operativa. Es el modo por
      defecto y el unico seguro mientras no haya modelo entrenado.
    - `FILTER`: bloquea las senales cuya probabilidad o expectativa no
      superan los umbrales.
    - `RANKING`: cuando concurren varias senales, prioriza las de mayor
      probabilidad.

    SEGURIDAD: con `block_when_untrained=False` (valor por defecto) la IA
    jamas bloquea una entrada si no tiene modelo entrenado.

    Vinculaciones:
    - Lo instancia `strategy.execution.live_trading_engine` en su `__init__`,
      uno por worker.
    - Usa `strategy.ai.training` para entrenar y `strategy.ai.model` para
      predecir.
    - `strategy.ai.ranking.rank_signals` ordena sus decisiones.
    """

    def __init__(self, config: MetaLabelingConfig | None = None, *, worker: str = "DEFAULT"):
        """Prepara el motor para un worker concreto.

        Los modelos se cachean en memoria y se protegen con un `RLock` porque
        cada worker corre en su propio hilo.

        Args:
            config: parametros de umbrales, modo y rutas.
            worker: identificador del worker; se normaliza a mayusculas.
        """
        self.config = config or MetaLabelingConfig()
        self.worker = str(worker or "DEFAULT").upper()
        self._models: dict[str, CalibratedLogisticModel] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # PERSISTENCIA POR WORKER
    # ------------------------------------------------------------------

    def _model_path(self, strategy_name: str) -> Path:
        """Construye la ruta del fichero del modelo.

        El nombre es `metalabel_<WORKER>_<ESTRATEGIA>.json`. Sanea las barras
        para que un nombre de simbolo no genere subdirectorios accidentales.
        """
        directory = Path(self.config.model_directory)
        safe_worker = self.worker.replace("/", "_")
        safe_strategy = str(strategy_name or "ALL").upper().replace("/", "_")
        return directory / f"metalabel_{safe_worker}_{safe_strategy}.json"

    def _model_key(self, strategy_name: str) -> str:
        """Clave de cache en memoria, con formato `WORKER:ESTRATEGIA`."""
        return f"{self.worker}:{str(strategy_name or 'ALL').upper()}"

    def load_model(self, strategy_name: str = "ALL") -> CalibratedLogisticModel:
        """Carga el modelo del worker desde cache o disco.

        Si el fichero no existe o esta corrupto devuelve un modelo VACIO sin
        entrenar en lugar de propagar la excepcion: un modelo danado degrada
        el worker a modo sombra pero nunca detiene la operativa.

        Returns:
            El modelo del worker, entrenado o no.
        """
        key = self._model_key(strategy_name)
        with self._lock:
            if key in self._models:
                return self._models[key]
            path = self._model_path(strategy_name)
            model = CalibratedLogisticModel(worker=self.worker, strategy_name=str(strategy_name or "ALL"))
            if path.exists():
                try:
                    model = CalibratedLogisticModel.from_dict(
                        json.loads(path.read_text(encoding="utf-8"))
                    )
                except Exception:
                    # Un modelo corrupto nunca debe frenar la operativa.
                    model = CalibratedLogisticModel(
                        worker=self.worker, strategy_name=str(strategy_name or "ALL")
                    )
            self._models[key] = model
            return model

    def save_model(self, model: CalibratedLogisticModel) -> str:
        """Persiste el modelo en disco y refresca la cache en memoria.

        Crea el directorio si no existe. El JSON se guarda indentado para
        poder inspeccionar a mano los pesos aprendidos.

        Returns:
            La ruta del fichero escrito.
        """
        path = self._model_path(model.strategy_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(model.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with self._lock:
            self._models[self._model_key(model.strategy_name)] = model
        return str(path)

    def train(self, trades, *, strategy_name: str = "ALL") -> dict:
        """Entrena y persiste el modelo del worker desde su historial."""
        scoped_strategy = None if str(strategy_name).upper() == "ALL" else strategy_name
        dataset_rows = int(
            build_training_dataset(
                trades, worker=self.worker, strategy_name=scoped_strategy
            )["rows"]
        )
        model = train_worker_model(
            trades,
            worker=self.worker,
            strategy_name=None if str(strategy_name).upper() == "ALL" else strategy_name,
            min_samples=int(self.config.min_training_samples),
        )
        model.worker = self.worker
        model.strategy_name = str(strategy_name or "ALL")
        path = self.save_model(model)
        validation = temporal_validation(
            trades,
            worker=self.worker,
            strategy_name=None if str(strategy_name).upper() == "ALL" else strategy_name,
        )
        return {
            "worker": self.worker,
            "strategy_name": model.strategy_name,
            "trained": bool(model.trained),
            "samples": int(model.model.samples),
            "available_samples": int(dataset_rows),
            "min_training_samples": int(self.config.min_training_samples),
            "reason": (
                "MODEL_TRAINED"
                if model.trained
                else "INSUFFICIENT_HISTORY_FOR_TRAINING"
            ),
            "model_path": path,
            "average_win_rr": model.average_win_rr,
            "average_loss_rr": model.average_loss_rr,
            "temporal_validation": validation.to_dict(),
        }

    # ------------------------------------------------------------------
    # PUNTUACIÓN
    # ------------------------------------------------------------------

    def score_signal(
        self,
        *,
        symbol: str,
        signal: dict | None = None,
        analysis: dict | None = None,
        market: dict | None = None,
        strategy_name: str = "ALL",
    ) -> MetaLabelDecision:
        """Calcula probabilidad calibrada y expectativa neta de una señal."""
        mode = str(self.config.mode or SHADOW_MODE).upper()
        evaluated_at = datetime.now(timezone.utc).isoformat()
        features = extract_meta_features(
            signal=signal,
            analysis=analysis,
            market=market,
            evaluated_at=evaluated_at,
        )
        thresholds = {
            "min_probability": float(self.config.min_probability),
            "min_net_expectancy_r": float(self.config.min_net_expectancy_r),
        }

        if not bool(self.config.enabled):
            return MetaLabelDecision(
                symbol=str(symbol), worker=self.worker, strategy_name=str(strategy_name),
                mode="DISABLED", probability=0.0, net_expectancy_r=0.0,
                allowed=True, shadow=True, reason="META_LABELING_DISABLED",
                trained=False, features=features, thresholds=thresholds,
                evaluated_at=evaluated_at,
            )

        model = self.load_model(strategy_name)
        probability = model.probability(feature_vector(features)) if model.trained else 0.0
        expectancy = model.net_expectancy_r(probability) if model.trained else 0.0
        shadow = mode != FILTER_MODE

        if not model.trained:
            allowed = not bool(self.config.block_when_untrained) or shadow
            reason = "MODEL_NOT_TRAINED_SHADOW_ONLY"
        elif shadow:
            allowed = True
            reason = "SHADOW_MODE_SCORED_WITHOUT_BLOCKING"
        elif probability + 1e-9 < thresholds["min_probability"]:
            allowed = False
            reason = "PROBABILITY_BELOW_THRESHOLD"
        elif expectancy + 1e-9 < thresholds["min_net_expectancy_r"]:
            allowed = False
            reason = "NET_EXPECTANCY_BELOW_THRESHOLD"
        else:
            allowed = True
            reason = "PROBABILITY_AND_EXPECTANCY_ACCEPTED"

        return MetaLabelDecision(
            symbol=str(symbol),
            worker=self.worker,
            strategy_name=str(strategy_name),
            mode=mode,
            probability=round(float(probability), 6),
            net_expectancy_r=round(float(expectancy), 6),
            allowed=bool(allowed),
            shadow=bool(shadow),
            reason=reason,
            trained=bool(model.trained),
            features=features,
            thresholds=thresholds,
            evaluated_at=evaluated_at,
        )
