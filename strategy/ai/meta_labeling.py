"""Motor de meta-etiquetado: modos sombra, filtro y ranking.

El motor nunca crea señales. Recibe la señal ya confirmada por una estrategia y
devuelve probabilidad calibrada, expectativa neta y una decisión auditable.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from strategy.ai.feature_extraction import FEATURE_SCHEMA, FEATURE_NAMES, extract_meta_features, feature_vector
from strategy.ai.model import CalibratedLogisticModel
from strategy.ai.training import build_training_dataset, temporal_validation, train_worker_model


SHADOW_MODE = "SHADOW"
FILTER_MODE = "FILTER"
RANKING_MODE = "RANKING"


@dataclass
class MetaLabelingConfig:
    """Configuración por worker del meta-etiquetado."""

    enabled: bool = True
    # SHADOW puntúa y registra sin bloquear; FILTER bloquea órdenes de baja probabilidad o expectativa.
    mode: str = os.getenv("DAEMONBLACKFX_META_LABELING_MODE", FILTER_MODE)
    min_probability: float = 0.55
    min_probability_forex: float = 0.60
    min_probability_gold: float = 0.60
    min_probability_volatility: float = 0.52
    min_net_expectancy_r: float = 0.10
    ranking_enabled: bool = True
    max_signals_per_cycle: int = 1
    model_directory: str = "storage/ai_models"
    min_training_samples: int = 15
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
        self._model_mtimes: dict[str, tuple[float, float]] = {}
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

    def load_model(self, strategy_name: str = "ALL", reload: bool = False) -> CalibratedLogisticModel:
        """Carga el modelo del worker desde cache o disco con verificación de frescura.

        Si el fichero no existe o esta corrupto devuelve un modelo VACIO sin
        entrenar en lugar de propagar la excepcion: un modelo danado degrada
        el worker a modo sombra pero nunca detiene la operativa.

        Returns:
            El modelo del worker, entrenado o no.
        """
        key = self._model_key(strategy_name)
        with self._lock:
            path = self._model_path(strategy_name)
            current_mtime = path.stat().st_mtime if path.exists() else 0.0
            global_path = Path(self.config.model_directory) / f"metalabel_GLOBAL_{str(strategy_name or 'ALL').upper()}.json"
            global_mtime = global_path.stat().st_mtime if global_path.exists() else 0.0
            mtimes = (current_mtime, global_mtime)

            if not reload and key in self._models and self._model_mtimes.get(key) == mtimes:
                return self._models[key]
            path = self._model_path(strategy_name)
            model = CalibratedLogisticModel(worker=self.worker, strategy_name=str(strategy_name or "ALL"))
            if path.exists():
                try:
                    model = CalibratedLogisticModel.from_dict(
                        json.loads(path.read_text(encoding="utf-8"))
                    )
                    # El vector v112 añade contexto ORB/agotamiento. Un modelo
                    # v111 con otra dimensionalidad no puede reutilizarse sin
                    # reentrenar; se degrada de forma segura a no entrenado.
                    if (
                        tuple(model.model.feature_names) != tuple(FEATURE_NAMES)
                        or (model.model.weights and len(model.model.weights) != len(FEATURE_NAMES))
                    ):
                        model = CalibratedLogisticModel(
                            worker=self.worker,
                            strategy_name=str(strategy_name or "ALL"),
                        )
                except Exception:
                    # Un modelo corrupto nunca debe frenar la operativa.
                    model = CalibratedLogisticModel(
                        worker=self.worker, strategy_name=str(strategy_name or "ALL")
                    )

            # Fallback al modelo ALL del worker si la estrategia específica no tiene modelo propio
            if not model.trained and str(strategy_name or "ALL").upper() != "ALL":
                all_path = self._model_path("ALL")
                if all_path.exists():
                    try:
                        all_model = CalibratedLogisticModel.from_dict(
                            json.loads(all_path.read_text(encoding="utf-8"))
                        )
                        if all_model.trained and tuple(all_model.model.feature_names) == tuple(FEATURE_NAMES):
                            model.model = all_model.model
                            model.calibrator = all_model.calibrator
                            model.average_win_rr = all_model.average_win_rr
                            model.average_loss_rr = all_model.average_loss_rr
                            model.trained_at = all_model.trained_at
                    except Exception:
                        pass

            # Fallback jerárquico al modelo global si el worker no está entrenado individualmente
            if not model.trained and self.worker not in ("GLOBAL", "ALL"):
                candidates = [
                    Path(self.config.model_directory) / f"metalabel_GLOBAL_{str(strategy_name or 'ALL').upper()}.json",
                    Path(self.config.model_directory) / "metalabel_GLOBAL_ALL.json",
                ]
                for global_path in candidates:
                    if global_path.exists():
                        try:
                            g_model = CalibratedLogisticModel.from_dict(
                                json.loads(global_path.read_text(encoding="utf-8"))
                            )
                            if g_model.trained and tuple(g_model.model.feature_names) == tuple(FEATURE_NAMES):
                                model.model = g_model.model
                                model.calibrator = g_model.calibrator
                                model.average_win_rr = g_model.average_win_rr
                                model.average_loss_rr = g_model.average_loss_rr
                                model.trained_at = g_model.trained_at
                                break
                        except Exception:
                            pass

            self._models[key] = model
            self._model_mtimes[key] = mtimes
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
            json.dumps({**model.to_dict(), "feature_schema": FEATURE_SCHEMA}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with self._lock:
            key = self._model_key(model.strategy_name)
            self._models[key] = model
            current_mtime = path.stat().st_mtime if path.exists() else 0.0
            global_path = Path(self.config.model_directory) / f"metalabel_GLOBAL_{str(model.strategy_name or 'ALL').upper()}.json"
            global_mtime = global_path.stat().st_mtime if global_path.exists() else 0.0
            self._model_mtimes[key] = (current_mtime, global_mtime)
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
            allow_global_pooling=True,
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

    def update_online_trade(
        self,
        features: dict[str, float] | list[float],
        label: int,
        realized_rr: float | None = None,
        *,
        strategy_name: str = "ALL",
        learning_rate: float = 0.05,
    ) -> bool:
        """Bucle de aprendizaje continuo en tiempo real (Online SGD Feedback Loop)."""
        vector = features if isinstance(features, list) else feature_vector(features)
        model = self.load_model(strategy_name)
        if not model.trained:
            return False
        with self._lock:
            updated = model.update_one(vector, label, realized_rr=realized_rr, learning_rate=learning_rate)
            if updated:
                self.save_model(model)
                global_path = Path(self.config.model_directory) / f"metalabel_GLOBAL_{str(strategy_name or 'ALL').upper()}.json"
                if global_path.exists() and self.worker not in ("GLOBAL", "ALL"):
                    try:
                        g_model = CalibratedLogisticModel.from_dict(
                            json.loads(global_path.read_text(encoding="utf-8"))
                        )
                        if g_model.trained:
                            g_model.update_one(vector, label, realized_rr=realized_rr, learning_rate=learning_rate)
                            global_path.write_text(
                                json.dumps({**g_model.to_dict(), "feature_schema": FEATURE_SCHEMA}, ensure_ascii=False, indent=2),
                                encoding="utf-8",
                            )
                    except Exception:
                        pass
        return updated

    # ------------------------------------------------------------------
    # PUNTUACIÓN
    # ------------------------------------------------------------------

    def resolve_min_probability(self, symbol: str) -> float:
        """Determina el umbral de probabilidad adaptativo según la familia del activo.

        - FOREX y GOLD: umbral estricto >= 0.60 para filtrar falsos rompimientos y spread.
        - VOLATILITY: umbral >= 0.52 para aprovechar mayor ratio de recorrido.
        - OTRAS FAMILIAS (BOOM, CRASH, STEP, JUMP): umbral base >= 0.55.
        """
        sym = str(symbol or "").upper().strip()
        wk = str(self.worker or "").upper().strip()

        if "XAU" in sym or "GOLD" in sym or wk == "GOLD":
            return float(getattr(self.config, "min_probability_gold", 0.60))

        forex_currencies = ("EUR", "USD", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD")
        is_forex = any(c in sym for c in forex_currencies) and not any(k in sym for k in ("BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP"))
        if is_forex or wk.startswith("FOREX"):
            return float(getattr(self.config, "min_probability_forex", 0.60))

        if "VOLATILITY" in sym or "1S" in sym or wk.startswith("VOLATILITY"):
            return float(getattr(self.config, "min_probability_volatility", 0.52))

        return float(self.config.min_probability)

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
        effective_min_prob = self.resolve_min_probability(symbol)
        thresholds = {
            "min_probability": effective_min_prob,
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
        shadow = mode == SHADOW_MODE

        if not model.trained:
            allowed = not bool(self.config.block_when_untrained) or shadow
            reason = "MODEL_NOT_TRAINED_SHADOW_ONLY"
        elif shadow:
            allowed = True
            reason = "SHADOW_MODE_SCORED_WITHOUT_BLOCKING"
        elif mode == RANKING_MODE:
            # RANKING no aplica un umbral individual: todas las señales
            # entrenadas pasan a la comparación del ciclo y sólo las de mayor
            # expectativa se seleccionan antes de ejecutar.
            allowed = True
            reason = "RANKING_MODE_ELIGIBLE_FOR_CYCLE_SELECTION"
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
