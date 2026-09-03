# DaemonBlackFx v38 — Preferencias persistentes de instrumentos

## Objetivo
La selección realizada en `/instruments` ahora se almacena en SQLAlchemy.

Tabla:
`instrument_selection_preferences`

Cada vez que el usuario pulsa Guardar selección:
- se persiste la lista completa de instrumentos;
- se incrementa la versión de la preferencia;
- la selección se sigue aplicando al próximo ciclo del daemon.

## Reinicios
La preferencia sobrevive a:
- reinicio del navegador;
- reinicio del dashboard;
- reinicio del daemon;
- reinicio del PC;
- eliminación de `storage/dashboard/last_state.json`.

En el siguiente arranque, si no se especifica un filtro manual, el daemon:
1. descubre los instrumentos actualmente disponibles en MT5;
2. lee la última preferencia de SQLAlchemy;
3. intersecta ambas listas;
4. opera únicamente los instrumentos persistidos que sigan disponibles.

## Overrides CLI
`--symbol` y `--categories` tienen prioridad temporal.

Ejemplo:
```bash
python -m app.main --mode demo-daemon --symbol "Volatility 75 Index"
```

Ese arranque utiliza el símbolo explícito, pero no reemplaza la preferencia
guardada desde `/instruments`.

## Seguridad
Si un instrumento persistido deja de existir o cambia de nombre en MT5:
- se ignora para ese arranque;
- no bloquea el daemon;
- el resto de preferencias válidas continúa utilizándose.

La lista nunca puede guardarse vacía desde el dashboard.
