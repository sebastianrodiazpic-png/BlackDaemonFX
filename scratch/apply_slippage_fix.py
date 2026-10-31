import os
from pathlib import Path

target_file = Path("strategy") / "execution" / "live_trading_engine.py"
tmp_file = Path("strategy") / "execution" / "live_trading_engine.py.tmp"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. En LiveTradingConfig
cfg_target = """    # Salida forzada de emergencia si el llenado real en el broker sufre slippage severo y queda con R:R inferior al umbral.
    emergency_unfavorable_rr_exit_enabled: bool = True
    min_acceptable_fill_rr: float = 1.0"""

cfg_replacement = """    # Salida forzada de emergencia si el llenado real en el broker sufre slippage severo y queda con R:R inferior al umbral.
    emergency_unfavorable_rr_exit_enabled: bool = True
    min_acceptable_fill_rr: float = 1.0
    min_acceptable_fill_rr_tp1: float = float(
        os.getenv("DAEMONBLACKFX_MIN_ACCEPTABLE_FILL_RR_TP1", "0.90")
    )"""

# 2. Helper en LiveTradingEngine
helper_target = """    def _analysis_invalidation_exit(
        self,
        *,
        trade: dict,
        metadata: dict,
        current_rr: float | None,
        close_position,
    ) -> dict:"""

helper_replacement = """    def _effective_min_acceptable_fill_rr(
        self, planned_rr: float | None = None, leg_name: str | None = None
    ) -> float:
        \"\"\"Determina el umbral mínimo aceptable de R:R tras el llenado en broker.

        Para la pierna TP1 (con objetivo base 1.0R) se admite una tolerancia
        configurable a micro-deslizamientos (por defecto 0.90R) para evitar que
        variaciones mínimas de spread de ticks (ej. 0.1 puntos) cierren de
        emergencia entradas institucionales legítimas.
        Para piernas runner (TP2 2.0R, etc.) o entradas estándar se exige min_acceptable_fill_rr (1.0).
        \"\"\"
        base_threshold = float(getattr(self.config, "min_acceptable_fill_rr", 1.0))
        tp1_threshold = float(getattr(self.config, "min_acceptable_fill_rr_tp1", 0.90))
        is_tp1 = (
            (leg_name and "TP1" in str(leg_name).upper())
            or (planned_rr is not None and float(planned_rr) <= 1.05)
        )
        if is_tp1:
            return min(base_threshold, tp1_threshold)
        return base_threshold

    def _analysis_invalidation_exit(
        self,
        *,
        trade: dict,
        metadata: dict,
        current_rr: float | None,
        close_position,
    ) -> dict:"""

# 3. Punto 1 en _analysis_invalidation_exit
pt1_target = """        # Cierre forzado si la posición fue llenada con un R:R inaceptable por slippage severo.
        exec_rr_audit = metadata.get("execution_rr_audit") or {}
        filled_target_rr = exec_rr_audit.get("filled_target_rr")
        min_acceptable_fill_rr = float(getattr(self.config, "min_acceptable_fill_rr", 1.0))"""

pt1_replacement = """        # Cierre forzado si la posición fue llenada con un R:R inaceptable por slippage severo.
        exec_rr_audit = metadata.get("execution_rr_audit") or {}
        filled_target_rr = exec_rr_audit.get("filled_target_rr")
        planned_target_rr = exec_rr_audit.get("planned_target_rr")
        min_acceptable_fill_rr = self._effective_min_acceptable_fill_rr(
            planned_rr=planned_target_rr,
            leg_name=metadata.get("trade_leg"),
        )"""

# 4. Punto 2 en execute_trade (leg fill check)
pt2_target = """                min_acceptable_fill_rr = float(getattr(self.config, "min_acceptable_fill_rr", 1.0))
                filled_rr = (lifecycle.metadata.get("execution_rr_audit") or {}).get("filled_target_rr")"""

pt2_replacement = """                min_acceptable_fill_rr = self._effective_min_acceptable_fill_rr(
                    planned_rr=leg.get("target_rr"),
                    leg_name=leg.get("name"),
                )
                filled_rr = (lifecycle.metadata.get("execution_rr_audit") or {}).get("filled_target_rr")"""

# 5. Punto 3 en execute_trade (direct executor)
pt3_target = """            min_acceptable_fill_rr = float(getattr(self.config, "min_acceptable_fill_rr", 1.0))
            filled_rr = execution_rr_audit.get("filled_target_rr")"""

pt3_replacement = """            min_acceptable_fill_rr = self._effective_min_acceptable_fill_rr(
                planned_rr=leg.get("target_rr"),
                leg_name=leg.get("name"),
            )
            filled_rr = execution_rr_audit.get("filled_target_rr")"""

def do_replace(txt, tgt, rep, name):
    if tgt in txt:
        print(f"{name} found with LF")
        return txt.replace(tgt, rep, 1)
    tgt_c = tgt.replace("\n", "\r\n")
    rep_c = rep.replace("\n", "\r\n")
    if tgt_c in txt:
        print(f"{name} found with CRLF")
        return txt.replace(tgt_c, rep_c, 1)
    print(f"ERROR: {name} NOT found!")
    return txt

content = do_replace(content, cfg_target, cfg_replacement, "cfg")
content = do_replace(content, helper_target, helper_replacement, "helper")
content = do_replace(content, pt1_target, pt1_replacement, "pt1")
content = do_replace(content, pt2_target, pt2_replacement, "pt2")
content = do_replace(content, pt3_target, pt3_replacement, "pt3")

with open(tmp_file, "w", encoding="utf-8") as f:
    f.write(content)

os.replace(tmp_file, target_file)
print("strategy/execution/live_trading_engine.py replaced successfully via tmp!")
