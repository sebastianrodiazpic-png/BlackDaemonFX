# DaemonBlackFx v87 — XAUUSD SMC Asia/Londres hasta Nueva York

- Nuevo worker `GOLD`, magic `26082029`.
- Opera únicamente XAUUSD estándar mediante el pipeline Forex/SMC H1→M15→M5.
- Usa confirmaciones, patrones, división 50/50, BE y runner progresivo de Forex.
- Nuevas entradas desde Tokio 09:00 (`Asia/Tokyo`) hasta Nueva York 09:30
  (`America/New_York`), con ajuste DST automático.
- Desde NY 09:30 no abre nuevas entradas SMC.
- Si una posición llega a NY con ≥1R, solicita cierre para asegurar beneficio.
- Si llega positiva pero bajo 1R, intenta BE exacto y lo confirma leyendo MT5.
- Si llega negativa, no cristaliza la pérdida; continúa gestión y bloquea ORB Oro.
- ORB XAUUSD/microXAUUSD queda bloqueado mientras exista exposición GOLD SMC.
- La preferencia visual de XAUUSD se reutiliza desde el perfil ORB para evitar
  duplicar el mismo instrumento en la página de selección.
