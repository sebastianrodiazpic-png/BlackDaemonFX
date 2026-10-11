@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX - GATEWAY CENTRAL DE DATOS DE MERCADO (ZeroMQ)
echo PUB: tcp://127.0.0.1:5555  ^|  REP: tcp://127.0.0.1:5556
echo ============================================================
.\.venv\Scripts\python.exe -m marketdata.market_data_feeder --pub-port 5555 --rep-port 5556
pause
