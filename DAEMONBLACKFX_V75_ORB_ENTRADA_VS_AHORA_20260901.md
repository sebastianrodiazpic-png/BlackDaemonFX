# DaemonBlackFx v75 — ORB Entrada vs. Ahora en tiempo real

El refresco de current_strategy_view excluía explícitamente ORB_NEW_YORK.
Ahora los trades ORB abiertos se reanalizan con orb_strategy.analyze_symbol()
en el refresco periódico, sin llamar process_symbol ni ejecutar órdenes.

Se persisten también opening range, midpoint, VWAP, POC, breakout y retest
actuales. La tesis de entrada permanece inmutable y el estado actual se
almacena como snapshots append-only.
