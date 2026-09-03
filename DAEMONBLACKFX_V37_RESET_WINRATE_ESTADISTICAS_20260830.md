# DaemonBlackFx v37 — Reset persistente de Win Rate y estadísticas

## Comando interactivo recomendado

```bash
python -m app.main --reset-account-stats
```

El sistema solicita:

```text
Escriba RESET para continuar:
```

También se admite:

```bash
python -m app.main --mode reset-account-stats
```

Para ejecución no interactiva:

```bash
python -m app.main --reset-account-stats --confirm-reset-account-stats
```

## Qué reinicia visualmente
Desde la fecha/hora del reset, Cuenta activa vuelve a:
- Cerrados: 0
- Win Rate: 0%
- PnL neto: 0
- TP1: 0
- TP2: 0
- TP histórico: 0
- Stop Loss: 0
- BE/Otro: 0
- Emergencia: 0

`Trades` conserva las posiciones OPEN existentes. Por ejemplo, si hay 2 posiciones
abiertas en el momento del reset, la nueva ventana mostrará inicialmente:
- Trades: 2
- Abiertos: 2
- Cerrados: 0

## Qué NO se borra
- posiciones OPEN;
- `trade_journal`;
- tabla operacional de trades;
- account snapshots;
- Balance / Equity / Margen / Profit persistidos.

El reset crea una fila en `account_stats_resets`. Por eso reiniciar Python, el daemon,
el dashboard o el PC no hace reaparecer el Win Rate anterior.

Una posición que ya estaba abierta antes del reset y cierra después del reset sí se
contabiliza en la nueva ventana estadística, porque su `exit_time` es posterior al corte.
