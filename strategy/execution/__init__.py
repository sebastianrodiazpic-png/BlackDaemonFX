"""Paquete de ejecución: del análisis multi-temporal a la orden y su gestión.

Reexporta la superficie publica del paquete para que el resto del proyecto
importe desde `strategy.execution` sin conocer la estructura interna.

Contenido principal:
- `multi_timeframe`: analizador H1/M15/M5 que produce las senales.
- `trade_pipeline`: orquesta el pipeline SMC sobre un marco temporal.
- `trade_executor`: contrato abstracto de ejecucion (peticion y resultado).
- `paper_trade_executor`: implementacion simulada de ese contrato.
- `live_trading_engine` y `live_paper_trading_engine`: los bucles de operativa.
- `runner_extension_manager`: decide si extender la porcion runner.
- `trade_outcome_policy`: clasifica el desenlace de lo ya cerrado.

CICLO DE IMPORTACION: los motores de trading no se importan aqui de forma
directa. Ver `__getattr__`.
"""

from strategy.execution.trade_executor import (
    TradeExecutor,
    TradeExecutionRequest,
    TradeExecutionResult,
)

from strategy.execution.paper_trade_executor import (
    PaperTradeExecutor,
)

from reporting.trade_report_exporter import (
    TradeReportExporter,
)


def __getattr__(name):
    """Importa de forma diferida los símbolos que crearían un ciclo de imports.

    `LivePaperTradingConfig` y `LivePaperTradingEngine` NO pueden importarse
    en la cabecera del paquete porque existe este ciclo:

        trade_lifecycle_manager -> strategy.execution.trade_executor
        -> strategy.execution.__init__ -> live_paper_trading_engine
        -> trade_lifecycle_manager

    Al resolverlos aqui, el modulo solo se carga cuando alguien accede de
    verdad al atributo, momento en que el ciclo ya esta cerrado.

    Args:
        name: atributo solicitado sobre el paquete.

    Returns:
        La clase pedida.

    Raises:
        AttributeError: para cualquier otro nombre, como es habitual.
    """
    # Importación diferida para evitar el ciclo:
    # trade_lifecycle_manager -> strategy.execution.trade_executor
    # -> strategy.execution.__init__ -> live_paper_trading_engine
    if name in {"LivePaperTradingConfig", "LivePaperTradingEngine"}:
        from .live_paper_trading_engine import (
            LivePaperTradingConfig,
            LivePaperTradingEngine,
        )
        return {
            "LivePaperTradingConfig": LivePaperTradingConfig,
            "LivePaperTradingEngine": LivePaperTradingEngine,
        }[name]
    raise AttributeError(name)
