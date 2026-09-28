"""Motor de meta-etiquetado con IA para DaemonBlackFx.

El meta-etiquetado no genera señales: puntúa las que ya produjo cada estrategia
y estima la probabilidad de acierto junto con la expectativa neta en R.
"""

from strategy.ai.feature_extraction import (
    FEATURE_NAMES,
    extract_meta_features,
    feature_vector,
)
from strategy.ai.meta_labeling import (
    FILTER_MODE,
    RANKING_MODE,
    SHADOW_MODE,
    MetaLabelDecision,
    MetaLabelingConfig,
    MetaLabelingEngine,
)
from strategy.ai.model import (
    CalibratedLogisticModel,
    LogisticRegressionModel,
    ProbabilityCalibrator,
)
from strategy.ai.ranking import rank_signals
from strategy.ai.training import (
    TemporalValidationReport,
    build_training_dataset,
    temporal_validation,
    train_worker_model,
)

__all__ = [
    "FEATURE_NAMES",
    "FILTER_MODE",
    "RANKING_MODE",
    "SHADOW_MODE",
    "extract_meta_features",
    "feature_vector",
    "MetaLabelDecision",
    "MetaLabelingConfig",
    "MetaLabelingEngine",
    "CalibratedLogisticModel",
    "LogisticRegressionModel",
    "ProbabilityCalibrator",
    "rank_signals",
    "TemporalValidationReport",
    "build_training_dataset",
    "temporal_validation",
    "train_worker_model",
]
