@echo off
cd /d "C:\TradingBoot\smc_synthetic_bot"
py -3 "tools\daily_gold_quarters_analysis.py" >> "storage\logs\daily_gold_quarters.log" 2>&1
