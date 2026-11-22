with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            else:
                if self._trend_pullback_active() and str(exact_symbol) in getattr(getattr(self, "trend_pullback_strategy", None), "config", None).symbols:
                    pullback_analysis = self.trend_pullback_strategy.analyze_symbol(exact_symbol)
                    if pullback_analysis.get("valid"):
                        analysis = pullback_analysis
                        analysis["context_policy"] = "TREND_PULLBACK_NATIVE"
                    else:
                        analysis = self._ict_analysis_with_virtual_limit(exact_symbol)
                        analysis["context_policy"] = "ICT_NATIVE"
                else:
                    analysis = self._ict_analysis_with_virtual_limit(exact_symbol)
                    analysis["context_policy"] = "ICT_NATIVE" """

replacement = """            else:
                is_step_target = str(exact_symbol).strip().removesuffix('micro').removesuffix('MICRO') in {
                    "Step Index", "Step Index 200", "Step Index 300", "Step Index 400", "Step Index 500"
                }
                step_multistrat = os.getenv("DAEMONBLACKFX_STEP_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
                msnr_strat = getattr(self, "malaysian_snr_strategy", None)
                if is_step_target and step_multistrat and msnr_strat is not None and (getattr(self.config, "malaysian_snr_enabled", False) or str(self.config.bot_profile or "").upper() == "STEP"):
                    msnr_analysis = msnr_strat.analyze_symbol(exact_symbol)
                    if msnr_analysis.get("valid"):
                        analysis = msnr_analysis
                        analysis["strategy_name"] = "MALAYSIAN_SNR"
                        analysis["context_policy"] = "MALAYSIAN_SNR_NATIVE"
                    else:
                        analysis = self._ict_analysis_with_virtual_limit(exact_symbol)
                        analysis["strategy_name"] = "ICT"
                        analysis["context_policy"] = "ICT_NATIVE"
                elif self._trend_pullback_active() and str(exact_symbol) in getattr(getattr(self, "trend_pullback_strategy", None), "config", None).symbols:
                    pullback_analysis = self.trend_pullback_strategy.analyze_symbol(exact_symbol)
                    if pullback_analysis.get("valid"):
                        analysis = pullback_analysis
                        analysis["context_policy"] = "TREND_PULLBACK_NATIVE"
                    else:
                        analysis = self._ict_analysis_with_virtual_limit(exact_symbol)
                        analysis["context_policy"] = "ICT_NATIVE"
                else:
                    analysis = self._ict_analysis_with_virtual_limit(exact_symbol)
                    analysis["context_policy"] = "ICT_NATIVE" """

norm = content.replace('\r\n', '\n')
if target in norm:
    norm = norm.replace(target, replacement)
    with open('strategy/execution/live_trading_engine.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(norm)
    print("SUCCESS: live_trading_engine.py updated")
else:
    print("ERROR: target not found in live_trading_engine.py")
