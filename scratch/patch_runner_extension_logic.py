path = 'strategy/execution/live_trading_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update stages in _manage_runner_extension
old_stages = """        first_trigger = float(self.config.runner_extension_first_trigger_rr or 2.0)
        first_lock = float(self.config.runner_extension_first_lock_rr or 1.0)
        second_trigger = float(self.config.runner_extension_second_trigger_rr or 3.0)
        second_lock = float(self.config.runner_extension_second_lock_rr or 2.5)

        stages = [
            (
                "2R_TO_3R",
                first_trigger,
                first_lock,
                3.0,
            ),
        ]
        if max_target_rr > 3.0:
            stages.append(
                (
                    "3R_TO_4R",
                    second_trigger,
                    second_lock,
                    max_target_rr,
                )
            )"""

new_stages = """        first_trigger = float(self.config.runner_extension_first_trigger_rr or 1.5)
        first_lock = float(self.config.runner_extension_first_lock_rr or 1.5)
        second_trigger = float(self.config.runner_extension_second_trigger_rr or 2.5)
        second_lock = float(self.config.runner_extension_second_lock_rr or 2.5)

        stage1_name = "1.5R_TO_3R" if abs(first_trigger - 1.5) < 0.05 else (
            "2R_TO_3R" if abs(first_trigger - 2.0) < 0.05 else f"{first_trigger:g}R_TO_3R"
        )
        stage2_name = "2.5R_TO_4R" if abs(second_trigger - 2.5) < 0.05 else (
            "3R_TO_4R" if abs(second_trigger - 3.0) < 0.05 else f"{second_trigger:g}R_TO_4R"
        )

        stages = [
            (
                stage1_name,
                first_trigger,
                first_lock,
                3.0,
            ),
        ]
        if max_target_rr > 3.0:
            stages.append(
                (
                    stage2_name,
                    second_trigger,
                    second_lock,
                    max_target_rr,
                )
            )"""

# 2. Update loop start and lock
old_loop = """        for stage_name, trigger_rr, lock_rr, next_target_rr in stages:
            if stage_name in completed_stages or current_rr + 1e-9 < trigger_rr:
                continue

            # ------------------------------------------------------------
            # 1) PROTEGER GANANCIA ANTES DE CUALQUIER EVALUACIÓN
            # ------------------------------------------------------------
            lock_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                lock_rr,
            )
            target_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                max_target_rr,
            )"""

new_loop = """        for stage_name, trigger_rr, lock_rr, next_target_rr in stages:
            is_stage1 = stage_name in {stage1_name, "1.5R_TO_3R", "2R_TO_3R"}
            is_stage2 = stage_name in {stage2_name, "2.5R_TO_4R", "3R_TO_4R"}
            stage_already_completed = (
                (is_stage1 and bool(completed_stages.intersection({"1.5R_TO_3R", "2R_TO_3R", stage1_name})))
                or (is_stage2 and bool(completed_stages.intersection({"2.5R_TO_4R", "3R_TO_4R", stage2_name})))
                or (stage_name in completed_stages)
            )
            if stage_already_completed or current_rr + 1e-9 < trigger_rr:
                continue

            # ------------------------------------------------------------
            # 1) PROTEGER GANANCIA ANTES DE CUALQUIER EVALUACIÓN
            # ------------------------------------------------------------
            lock_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                lock_rr,
            )
            target_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                next_target_rr,
            )"""

# 3. Update metadata assignment at extension
old_meta = """            metadata["runner_extension_stage"] = (
                "EXTENDED_TO_3R" if stage_name == "2R_TO_3R" else "EXTENDED_TO_4R"
            )
            if stage_name == "2R_TO_3R":
                metadata["runner_next_evaluation_rr"] = (
                    3.0
                    if is_forex_runner
                    else float(self.config.runner_extension_second_trigger_rr)
                )
            else:
                metadata["runner_next_evaluation_rr"] = max_target_rr"""

new_meta = """            metadata["runner_extension_stage"] = (
                "EXTENDED_TO_3R" if is_stage1 else "EXTENDED_TO_4R"
            )
            if is_stage1:
                metadata["runner_next_evaluation_rr"] = (
                    3.0
                    if is_forex_runner
                    else float(self.config.runner_extension_second_trigger_rr)
                )
            else:
                metadata["runner_next_evaluation_rr"] = max_target_rr"""

# 4. _plan_split_orders: runner_target_rr starts at eff_second_rr (1:2)
old_split_vol = """            elif is_vol_profile and is_volatility and strategy_name != "MALAYSIAN_SNR":
                eff_first_rr = float(self.config.volatility_first_target_rr)
                eff_second_rr = float(self.config.volatility_second_target_rr)
                if bool(self.config.runner_extension_enabled):
                    runner_target_rr = max(eff_second_rr, float(self.config.runner_extension_max_target_rr))
                else:
                    runner_target_rr = eff_second_rr
                split_specs = [
                    ("TP1", risk_fraction, eff_first_rr, eff_first_rr),
                    ("RUNNER", risk_fraction, eff_second_rr, runner_target_rr),
                ]"""

new_split_vol = """            elif is_vol_profile and is_volatility and strategy_name != "MALAYSIAN_SNR":
                eff_first_rr = float(self.config.volatility_first_target_rr)
                eff_second_rr = float(self.config.volatility_second_target_rr)
                # El runner nace siempre buscando 1:2 (eff_second_rr).
                # La extensión progresiva a 1:3 y 1:4 se gestiona dinámicamente en vivo.
                runner_target_rr = eff_second_rr
                split_specs = [
                    ("TP1", risk_fraction, eff_first_rr, eff_first_rr),
                    ("RUNNER", risk_fraction, eff_second_rr, runner_target_rr),
                ]"""

old_split_default = """                else:
                    runner_logical_rr = eff_second_rr
                    if bool(self.config.runner_extension_enabled):
                        runner_target_rr = max(eff_second_rr, float(self.config.runner_extension_max_target_rr))
                    else:
                        runner_target_rr = eff_second_rr
                split_specs = [
                    ("TP1", risk_fraction, eff_first_rr, eff_first_rr),
                    ("RUNNER", risk_fraction, runner_logical_rr, runner_target_rr),
                ]"""

new_split_default = """                else:
                    runner_logical_rr = eff_second_rr
                    runner_target_rr = eff_second_rr
                split_specs = [
                    ("TP1", risk_fraction, eff_first_rr, eff_first_rr),
                    ("RUNNER", risk_fraction, runner_logical_rr, runner_target_rr),
                ]"""

def replace_block(c, old_b, new_b, label):
    if old_b in c:
        c = c.replace(old_b, new_b, 1)
        print(f"OK: {label}")
        return c
    old_crlf = old_b.replace('\n', '\r\n')
    new_crlf = new_b.replace('\n', '\r\n')
    if old_crlf in c:
        c = c.replace(old_crlf, new_crlf, 1)
        print(f"OK (CRLF): {label}")
        return c
    print(f"FAIL: {label}")
    return c

content = replace_block(content, old_stages, new_stages, "stages")
content = replace_block(content, old_loop, new_loop, "loop")
content = replace_block(content, old_meta, new_meta, "meta")
content = replace_block(content, old_split_vol, new_split_vol, "split_vol")
content = replace_block(content, old_split_default, new_split_default, "split_default")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Finished patching.")
