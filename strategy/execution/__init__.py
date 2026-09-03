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
