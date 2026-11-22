"""
tools/patch_live_trading_engine_tripartite.py
=============================================
Integra TripartiteConfluenceGate en LiveTradingEngine:
1. Agrega los campos de configuración a LiveTradingEngineConfig.
2. Instancia self.tripartite_confluence_gate en LiveTradingEngine.__init__.
3. Agrega el método _evaluate_tripartite_confluence_gate.
4. Conecta el filtro en el pipeline de evaluación de órdenes.
"""

from pathlib import Path

FILE_PATH = Path("strategy/execution/live_trading_engine.py")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Configuración
config_target = """    human_criteria_msnr_min_score: float = float(
        os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_MSNR_MIN_SCORE", "60.0")
    )"""

config_replacement = """    human_criteria_msnr_min_score: float = float(
        os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_MSNR_MIN_SCORE", "60.0")
    )

    # Gatillo de Confluencia Tripartita (Estrategia + Criterio Humano + Filtro Activo de IA)
    tripartite_confluence_enabled: bool = (
        os.getenv("DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    tripartite_ai_filter_active: bool = (
        os.getenv("DAEMONBLACKFX_TRIPARTITE_AI_FILTER_ACTIVE", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    tripartite_human_criteria_active: bool = (
        os.getenv("DAEMONBLACKFX_TRIPARTITE_HUMAN_CRITERIA_ACTIVE", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    tripartite_rehabilitated_enabled: bool = (
        os.getenv("DAEMONBLACKFX_TRIPARTITE_REHABILITATED_ENABLED", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )"""

assert config_target in text, "No se encontró config_target"
text = text.replace(config_target, config_replacement, 1)

# 2. Instanciación en __init__
init_target = """        from strategy.human_criteria import HumanCriteriaEngine, HumanCriteriaConfig
        self.human_criteria_engine = HumanCriteriaEngine("""

init_replacement = """        from strategy.confluence.tripartite_confluence_gate import (
            TripartiteConfluenceGate,
            TripartiteConfluenceConfig,
        )
        self.tripartite_confluence_gate = TripartiteConfluenceGate(
            TripartiteConfluenceConfig(
                enabled=bool(getattr(self.config, "tripartite_confluence_enabled", True)),
                ai_filter_active=bool(getattr(self.config, "tripartite_ai_filter_active", True)),
                human_criteria_active=bool(getattr(self.config, "tripartite_human_criteria_active", True)),
                rehabilitated_assets_enabled=bool(getattr(self.config, "tripartite_rehabilitated_enabled", True)),
            )
        )
        from strategy.human_criteria import HumanCriteriaEngine, HumanCriteriaConfig
        self.human_criteria_engine = HumanCriteriaEngine("""

assert init_target in text, "No se encontró init_target"
text = text.replace(init_target, init_replacement, 1)

# 3. Método _evaluate_tripartite_confluence_gate
# Insertar justo después de _human_criteria_entry_gate
method_target = """        if not decision.allowed:
            return {
                "symbol": str(symbol),
                "action": "HUMAN_CRITERIA_FILTER_REJECTED",
                "reason": decision.reason,
                "execution_key": key,
                "direction": direction,
                "human_criteria": decision.to_dict(),
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        return None"""

method_replacement = """        if not decision.allowed:
            return {
                "symbol": str(symbol),
                "action": "HUMAN_CRITERIA_FILTER_REJECTED",
                "reason": decision.reason,
                "execution_key": key,
                "direction": direction,
                "human_criteria": decision.to_dict(),
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        return None

    def _evaluate_tripartite_confluence_gate(
        self,
        symbol: str,
        direction: str,
        signal: dict[str, Any],
        analysis: dict[str, Any] | None,
        key: str,
    ) -> dict[str, Any] | None:
        \"\"\"Gatillo de Confluencia Tripartita (Estrategia + Criterio Humano + Filtro Activo de IA).\"\"\"
        gate = getattr(self, "tripartite_confluence_gate", None)
        if gate is None or not bool(getattr(gate.config, "enabled", True)):
            return None

        strategy_name = str(
            signal.get("strategy_name")
            or getattr(self.config, "bot_profile", "")
            or "ICT"
        ).upper()

        human_crit = signal.get("human_criteria")
        ai_eval = signal.get("meta_labeling") or signal.get("meta_labeling_prediction") or signal.get("ai_evaluation")

        candle_body_ratio = signal.get("candle_body_ratio")
        adx_val = signal.get("adx") or signal.get("regime_adx")
        is_spike_danger = bool(signal.get("spike_danger", False))

        decision = gate.evaluate_confluence(
            symbol=symbol,
            strategy_name=strategy_name,
            direction=direction,
            signal=signal,
            human_criteria_decision=human_crit,
            ai_evaluation=ai_eval,
            candle_body_ratio=candle_body_ratio,
            adx_value=adx_val,
            is_spike_danger=is_spike_danger,
        )

        signal["tripartite_confluence"] = decision.to_dict()

        if hasattr(self, "_persist_audit_event") and getattr(self, "repository", None) is not None:
            self._persist_audit_event(
                "TRIPARTITE_CONFLUENCE_EVALUATED",
                instrument=str(symbol),
                action=decision.action,
                reason=decision.reason,
                payload=decision.to_dict(),
            )

        if not decision.allowed:
            return {
                "symbol": str(symbol),
                "action": "TRIPARTITE_CONFLUENCE_FILTER_REJECTED",
                "reason": decision.reason,
                "execution_key": key,
                "direction": direction,
                "tripartite_decision": decision.to_dict(),
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        return None"""

assert method_target in text, "No se encontró method_target"
text = text.replace(method_target, method_replacement, 1)

# 4. Pipeline de entrada: conectar justo después de human_criteria_gate
pipeline_target = """        human_criteria_gate = self._human_criteria_entry_gate(
            exact_symbol, direction, signal, analysis, key
        )
        if human_criteria_gate is not None:
            return human_criteria_gate"""

pipeline_replacement = """        human_criteria_gate = self._human_criteria_entry_gate(
            exact_symbol, direction, signal, analysis, key
        )
        if human_criteria_gate is not None:
            return human_criteria_gate

        tripartite_gate = self._evaluate_tripartite_confluence_gate(
            exact_symbol, direction, signal, analysis, key
        )
        if tripartite_gate is not None:
            return tripartite_gate"""

assert pipeline_target in text, "No se encontró pipeline_target"
text = text.replace(pipeline_target, pipeline_replacement, 1)

with open(FILE_PATH, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print(f"[SUCCESS] Patched {FILE_PATH.name} with Tripartite Confluence Gate successfully!")
