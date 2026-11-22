import sys
sys.path.insert(0, '.')

from config.ict_instrument_policy import ICT_SYNTHETIC_FAMILIES, ICT_5Y_RESCUED_SYNTHETICS, ICT_5Y_SYNTH_PRUNED
import inspect
from strategy.execution.live_trading_engine import LiveTradingEngine
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

print("1. Familia STEP activa en Policy:", ICT_SYNTHETIC_FAMILIES["STEP"])
print("2. Step Index 200 en Rescatados:", "Step Index 200" in ICT_5Y_RESCUED_SYNTHETICS)
print("3. Step Index 200 fuera de Podados:", "Step Index 200" not in ICT_5Y_SYNTH_PRUNED)

engine_src = inspect.getsource(LiveTradingEngine._validate_post_fill_risk)
print("4. Tolerancia 6.5% en Engine (_validate_post_fill_risk):", "DAEMONBLACKFX_STEP_HARD_RISK_TOLERANCE" in engine_src)

gate_src = inspect.getsource(LiveTradingEngine._step_quality_gate)
print("5. ADX dinámico y gatillo M5 en _step_quality_gate:", "high_conviction_step" in gate_src and "DAEMONBLACKFX_STEP_MIN_ADX" in gate_src)

print("6. Pestaña MultiStrategia en Dashboard (/Strategy-bases):", "setStrategyTab('multistrategy')" in STRATEGY_BASES_HTML)
print("7. Total 68 Workers MT5 reflejados en Tab-Bar:", "68 Workers MT5" in STRATEGY_BASES_HTML)
print("8. Jump 10 (+748.0R) del Censo en Dashboard:", "748.0" in STRATEGY_BASES_HTML and "74800.0" in STRATEGY_BASES_HTML)
print("9. Jump 75 (+602.8R) del Censo en Dashboard:", "602.8" in STRATEGY_BASES_HTML and "60280.0" in STRATEGY_BASES_HTML)
print("10. Dummy de 3750 trades de Jump 50 eliminado:", "3750" not in STRATEGY_BASES_HTML)
