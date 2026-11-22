import os

p_repo = "database/repository.py"
with open(p_repo, "r", encoding="utf-8") as f:
    c = f.read()

c_unix = c.replace("\r\n", "\n")

target = """            # Inferencia inteligente de pata y vinculación de trade hermano cuando daemon_owned=True
            parent_exec_key = None
            inferred_strategy = None
            if trade_leg is None and daemon_owned:
                try:
                    recent_candidates = self.get_trades(
                        source=trade_source,
                        symbol=symbol,
                        limit=10,
                    ) if hasattr(self, "get_trades") else []
                    for cand in (recent_candidates or []):
                        if str(cand.get("broker_position_ticket")) == str(ticket):
                            continue
                        if str(cand.get("direction", "")).upper() != direction:
                            continue
                        cand_meta = (cand.get("details") or {}).get("metadata") or {}
                        cand_leg = str(cand_meta.get("trade_leg") or "").upper()
                        cand_parent = cand_meta.get("parent_execution_key") or (cand.get("execution_key") or "").replace(":TP1", "").replace(":RUNNER", "")
                        cand_strat = cand_meta.get("strategy_name") or cand.get("strategy_version")

                        if cand_leg == "TP1" or (cand.get("planned_rr") and planned_rr and planned_rr > float(cand["planned_rr"])):
                            trade_leg = "RUNNER"
                            parent_exec_key = cand_parent
                            inferred_strategy = cand_strat
                            break
                        elif cand_leg == "RUNNER" or (cand.get("planned_rr") and planned_rr and planned_rr < float(cand["planned_rr"])):
                            trade_leg = "TP1"
                            parent_exec_key = cand_parent
                            inferred_strategy = cand_strat
                            break

                    if trade_leg is None and planned_rr is not None and planned_rr >= 1.5:
                        trade_leg = "RUNNER"
                except Exception:
                    pass"""

replacement = """            # Inferencia inteligente de pata y vinculación de trade hermano cuando daemon_owned=True
            parent_exec_key = None
            inferred_strategy = None
            if trade_leg is None and daemon_owned:
                try:
                    recent_candidates = []
                    try:
                        recent_candidates.extend(self.open_trades(source=trade_source) or [])
                    except Exception:
                        pass
                    try:
                        with self.session() as s:
                            from database.models import Trade
                            from sqlalchemy import desc
                            q = s.query(Trade).filter(
                                Trade.instrument == symbol,
                                Trade.direction == direction,
                            ).order_by(desc(Trade.id)).limit(10)
                            for db_t in q.all():
                                recent_candidates.append(self._trade_dict(db_t))
                    except Exception:
                        pass

                    for cand in recent_candidates:
                        if str(cand.get("broker_position_ticket")) == str(ticket):
                            continue
                        if str(cand.get("instrument")) != symbol:
                            continue
                        if str(cand.get("direction", "")).upper() != direction:
                            continue
                        cand_meta = (cand.get("details") or {}).get("metadata") or {}
                        cand_leg = str(cand_meta.get("trade_leg") or "").upper()
                        cand_parent = cand_meta.get("parent_execution_key") or (cand.get("execution_key") or "").replace(":TP1", "").replace(":RUNNER", "")
                        cand_strat = cand_meta.get("strategy_name") or cand.get("strategy_version")

                        if cand_leg == "TP1" or (cand.get("planned_rr") and planned_rr and planned_rr > float(cand["planned_rr"])):
                            trade_leg = "RUNNER"
                            parent_exec_key = cand_parent
                            inferred_strategy = cand_strat
                            break
                        elif cand_leg == "RUNNER" or (cand.get("planned_rr") and planned_rr and planned_rr < float(cand["planned_rr"])):
                            trade_leg = "TP1"
                            parent_exec_key = cand_parent
                            inferred_strategy = cand_strat
                            break

                    if trade_leg is None and planned_rr is not None and planned_rr >= 1.5:
                        trade_leg = "RUNNER"
                except Exception:
                    pass"""

if target in c_unix:
    c_unix = c_unix.replace(target, replacement)
    if "\r\n" in c:
        c_unix = c_unix.replace("\n", "\r\n")
    with open(p_repo, "w", encoding="utf-8") as f:
        f.write(c_unix)
    print("Repository infer logic updated successfully.")
else:
    print("target NOT found in repository!")
