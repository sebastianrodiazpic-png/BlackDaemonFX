path = 'tests/test_malaysian_snr_augmented_rules.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

new_tests = '''    def test_crt_sweep_and_rejection_trigger(self):
        from strategy.malaysian_snr.validation import confirmed_crt_retest
        # Setup: Level at 100.0, BUY direction, ATR = 2.0
        # Case 1: Valid sweep (low=99.5 <= 100.2) and rejection close (close=100.5 > open=100.0)
        df_valid = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 100.0, "high": 100.8, "low": 99.5, "close": 100.5}
        ])
        self.assertTrue(confirmed_crt_retest(df_valid, level=100.0, direction="BUY", atr=2.0))

        # Case 2: No sweep (low=101.0 > 100.2)
        df_no_sweep = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 101.2, "high": 101.8, "low": 101.0, "close": 101.5}
        ])
        self.assertFalse(confirmed_crt_retest(df_no_sweep, level=100.0, direction="BUY", atr=2.0))

        # Case 3: Sweep but closes bearish (failed rejection)
        df_bearish_fail = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 100.5, "high": 100.8, "low": 99.5, "close": 99.8}
        ])
        self.assertFalse(confirmed_crt_retest(df_bearish_fail, level=100.0, direction="BUY", atr=2.0))

    def test_validated_portfolio_allowlist(self):
        config = MalaysianSNRConfig()
        # Validados en replay 2 anos
        for sym in ["EURUSD", "USDJPY", "GBPUSD", "USDCAD", "XAUUSD", "XAGUSD", "BTCUSD", "Boom 1000 Index", "Crash 1000 Index", "Step Index"]:
            self.assertIn(sym, config.allowed_symbols)
        # Excluidos formalmente de MSNR
        for sym in ["US Tech 100", "Wall Street 30", "US SP 500", "US Oil", "AUDUSD", "USDCHF"]:
            self.assertNotIn(sym, config.allowed_symbols)
'''

target = 'if __name__ == "__main__":'
assert target in text
text = text.replace(target, new_tests + '\n\n' + target)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated", path)
