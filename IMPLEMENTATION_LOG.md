# Registro de funcionalidades implementadas

Fecha de actualización: 2026-08-26

## Objetivo de esta actualización

Mejorar el modo `demo-daemon` a partir del análisis del reporte
`deriv_demo_trading_report.xlsx` y del código fuente actual.

Esta actualización incorpora dos controles operativos principales:

1. Break Even real en posiciones DEMO abiertas.
2. Política estricta para evitar abrir operaciones cuyo volumen ejecutable no
   represente aproximadamente el riesgo objetivo configurado.

También mejora la persistencia de datos de riesgo en SQLite/XLSX.

---

## 1. Break Even real en el daemon

### Problema detectado

La funcionalidad de Break Even ya existía en:

- `position_manager.py`
- `monitoring/position_monitoring_service.py`
- `trade_lifecycle_manager.py`
- pruebas de lifecycle PAPER

Sin embargo, el ciclo `LiveTradingEngine.run_daemon()` analizaba símbolos y
sincronizaba cierres, pero no recorría las posiciones DEMO abiertas para mover
el Stop Loss real en MT5 cuando se alcanzaba 1R.

Por lo tanto, la lógica estaba implementada para PAPER/lifecycle, pero no estaba
conectada al monitoreo persistente de las posiciones reales DEMO.

### Implementación

Se agregaron a `LiveTradingConfig`:

```text
break_even_enabled = True
break_even_trigger_rr = 1.0
```

En cada ciclo del daemon se ejecuta:

```text
_monitor_break_even_positions()
```

El monitor:

1. Consulta las operaciones OPEN propias del bot en SQLite.
2. Consulta la posición real correspondiente en MT5.
3. Recupera el Stop Loss inicial persistido al abrir la operación.
4. Calcula el riesgo inicial en precio.
5. Calcula el nivel de activación de Break Even.
6. Cuando se alcanza 1R:
   - modifica el Stop Loss real de MT5;
   - lo mueve al precio de entrada;
   - conserva el Take Profit;
   - persiste el nuevo estado en SQLite;
   - actualiza el XLSX;
   - evita repetir la modificación en ciclos posteriores.

La implementación es resistente al reinicio del daemon porque el estado se
reconstruye desde SQLite y MT5, no solamente desde memoria.

### Ejemplo BUY

Entrada: 100
SL inicial: 90
Riesgo: 10
Trigger 1R: 110

Cuando precio actual >= 110:

SL nuevo = 100

### Ejemplo SELL

Entrada: 100
SL inicial: 110
Riesgo: 10
Trigger 1R: 90

Cuando precio actual <= 90:

SL nuevo = 100

---

## 2. Modificación real de Stop Loss en MT5

### Archivo

`brokers/mt5_execution.py`

Se agregó:

```text
modify_position_stops(...)
```

Utiliza `TRADE_ACTION_SLTP` para modificar una posición existente sin cerrarla.

El resultado devuelve:

- modified
- position_ticket
- symbol
- requested_stop_loss
- requested_take_profit
- retcode
- comment
- last_error
- request

### Adaptador de ejecución

En `brokers/mt5_trade_executor.py` se agregó:

```text
move_stop_loss(...)
```

Este método es utilizado por el daemon para solicitar el movimiento real del
Stop Loss a Break Even.

---

## 3. Política de riesgo objetivo

### Configuración

Se agregó:

```text
min_actual_risk_ratio = 0.95
max_actual_risk_tolerance = 0.01
```

Con un riesgo objetivo de 1%:

- no se acepta riesgo superior a 1.01% por tolerancia de redondeo;
- para sizing real del broker se exige alcanzar al menos el 95% del objetivo.

Si el máximo volumen permitido por el broker impide alcanzar el riesgo objetivo,
la operación se rechaza con:

```text
REJECTED_RISK_TARGET_UNREACHABLE
```

Motivo:

```text
BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK
```

Esto evita abrir una operación solo porque el broker acepta el volumen máximo,
cuando dicho volumen no representa el riesgo que la estrategia pretende usar.

---

## 4. Protección de margen

Se agregó:

```text
max_margin_fraction = 0.15
```

Después de un `order_check` válido, el daemon revisa el margen requerido.

Si:

```text
required_margin > risk_base_value * max_margin_fraction
```

la operación se rechaza con:

```text
REJECTED_MARGIN_EXCEEDED
```

Motivo:

```text
ORDER_CHECK_MARGIN_EXCEEDS_LIMIT
```

Este límite es independiente del riesgo del Stop Loss. Una operación puede tener
un riesgo monetario correcto y, al mismo tiempo, requerir demasiado margen.

---

## 5. Persistencia del riesgo en los reportes

El lifecycle ya almacenaba los valores dentro de `details.metadata`, pero las
columnas principales del reporte podían quedar vacías.

Se actualizó `reporting/trade_reporting_service.py` para persistir:

- risk_percent
- risk_amount
- balance_before
- equity

Además se mantiene dentro de metadata:

- initial_stop_loss
- actual_risk_amount
- risk_base
- risk_base_value
- break_even_enabled
- break_even_trigger_rr
- break_even_activated
- break_even_trigger_price
- break_even_activated_at_price
- break_even_broker_result

---

## 6. Diagnóstico del caso Volatility 75 Index

El reporte analizado muestra:

- volumen ejecutado: 15.0
- volumen máximo del símbolo: 15.0
- riesgo objetivo: 94.79
- riesgo calculado real al SL: aproximadamente 40.71

Por lo tanto, el dato disponible no indica un riesgo superior al 1% en el Stop
Loss. Indica que el sizing quedó limitado por el volumen máximo del broker y
solo alcanzó aproximadamente el 43% del riesgo objetivo.

Sin embargo, el volumen 15.0 consumió un margen considerable en relación con
otras operaciones. Por ese motivo se incorporaron ambas protecciones:

1. riesgo objetivo mínimo alcanzable;
2. límite de margen.

---

## 7. Pruebas agregadas

### `tests/test_daemon_break_even_live.py`

Valida:

- activación del Break Even en una posición DEMO simulada al llegar a 1R;
- movimiento del SL al precio de entrada;
- persistencia del estado;
- idempotencia cuando el Break Even ya está activo.

### `tests/test_daemon_risk_target_policy.py`

Valida:

- rechazo cuando el volumen máximo del broker impide alcanzar el riesgo mínimo
  configurado.

---

## 8. Flujo actual del daemon

Cada ciclo ejecuta:

```text
INICIO CICLO
    |
    +--> MONITOR BREAK EVEN DE POSICIONES OPEN
    |       |
    |       +--> SQLite
    |       +--> MT5 posición real
    |       +--> ¿alcanzó 1R?
    |               |
    |               +--> modificar SL real a entrada
    |               +--> persistir SQLite
    |               +--> actualizar XLSX
    |
    +--> sincronizar cierres anteriores
    |
    +--> analizar H1 -> M15 -> M5
    |
    +--> validar dirección
    |
    +--> validar RR
    |
    +--> validar posición duplicada
    |
    +--> validar entrada actual
    |
    +--> validar SL/TP reales del símbolo
    |
    +--> calcular riesgo objetivo
    |
    +--> calcular volumen broker-aware
    |
    +--> ¿riesgo real dentro de rango?
    |       |
    |       +--> no: RECHAZAR
    |
    +--> ORDER CHECK
    |
    +--> ¿margen dentro del límite?
    |       |
    |       +--> no: RECHAZAR
    |
    +--> ejecutar DEMO
    |
    +--> registrar lifecycle
    |
    +--> SQLite
    |
    +--> XLSX
```

---

## 9. Validación ejecutada

En el entorno de revisión se ejecutó un subconjunto independiente de MT5 con:

```text
33 passed
```

El conjunto completo no pudo ejecutarse en este entorno porque el paquete
`MetaTrader5` no está disponible aquí. El proyecto debe ejecutar la suite
completa en el equipo Windows donde está instalado MetaTrader5.

Comando recomendado:

```bash
python -m pytest -q
```

Luego, para DEMO:

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5
```


## 2026-08-29 — v32 ORB New York
- Segunda estrategia independiente `ORB_NEW_YORK`.
- Exclusiva para XAUUSDmicro, Wall Street 30, US Tech 100 y US500.
- Opening Range 09:30-09:45 America/New_York con M1.
- Ruptura fresca posterior a 09:45, sólo hasta 16:00 NY.
- VWAP y POC obligatorios y alineados con la dirección.
- POC basado en volumen del feed MT5 (real_volume o tick_volume fallback).
- Router estricto: mercados ORB no hacen fallback a SMC fuera de horario.
- Reutiliza motor de riesgo/TP1/RUNNER/BE común.
- 204 pruebas no-MT5 aprobadas.


## 2026-08-29 — v34 ORB dual Gold selector
- ORB acepta XAUUSD y XAUUSDmicro como contratos alternativos de Oro.
- Selección automática por precisión de riesgo 0,5%, spread y margen.
- Bloqueo de exposición duplicada entre ambos contratos.
- TP1 0,5% a 1R + RUNNER 0,5% a 2R con BE +2 puntos.
- Diagnóstico `gold_contract_selection` persistido en la operación.


## 2026-08-30 — v36 Cuenta activa persistente SQLAlchemy
- `/account` consume `/api/account`, no `/api/state`.
- KPIs, Win rate, PnL y cierres se reconstruyen desde `trade_journal`.
- Balance/equity/margen/profit se leen del último `account_snapshots` persistido.
- `last_state.json` deja de ser dependencia de Cuenta activa.


## 2026-08-30 — v37 Reset Win Rate / Cuenta activa
- Nuevo comando `python -m app.main --reset-account-stats`.
- Confirmación interactiva escribiendo `RESET`.
- Opción `--confirm-reset-account-stats` para ejecución no interactiva.
- Reset persistido en `account_stats_resets`, sin borrar `trade_journal`.
- Posiciones OPEN se conservan y sus cierres posteriores cuentan en la nueva ventana.


## 2026-08-30 — v38 Preferencias persistentes de instrumentos
- Nueva tabla `instrument_selection_preferences`.
- Guardar selección en `/instruments` escribe en SQLAlchemy.
- Arranque sin filtros recupera automáticamente la última selección persistida.
- `--symbol` y `--categories` conservan prioridad temporal y no sobrescriben preferencias.
- `last_state.json` deja de ser necesario para recordar instrumentos.


## 2026-08-30 — v39 Búsqueda sólo sesión New York
- Filtro global de nuevas entradas: 09:30 <= NY < 16:00, lunes a viernes.
- Zona `America/New_York` con DST automático.
- Fuera de sesión se omiten SMC, ORB, selector de Oro y sizing de nuevas señales.
- Gestión de posiciones abiertas y Break Even permanecen activas fuera de sesión.


## 2026-08-30 — v40 ORB independiente / SMC 24/7
- Se elimina el filtro NY global introducido en v39.
- SMC/sintéticos vuelven a analizarse a cualquier hora.
- ORB conserva 09:30–16:00 America/New_York exclusivamente para sus mercados.
- Selector XAUUSD/XAUUSDmicro se omite fuera de la sesión ORB.


## 2026-08-30 — v41 Critical Gates + RUNNER TP3/TP4
- BOS requiere rechazo M5; CHOCH requiere microestructura M5.
- Score visible limitado a 100; raw_trade_score preservado.
- Jump en demo-daemon usa filtro reforzado >=90% y sin SINGLE fallback.
- RUNNER dinámico: 2R lock +1R -> 3R; 3R lock +2R -> 4R.
- Profit lock se aplica antes de evaluar continuación.
- MFE/MAE persistentes en metadata y exportados al reporte.
- Cuenta activa clasifica TP3 y TP4.


## 2026-08-31 — v43 Protección rollover Forex
- Nuevas entradas Forex bloqueadas desde 16:30 NY.
- Posiciones Forex del daemon forzadas a cerrar desde 16:45 NY.
- Ventana de protección termina a las 17:15 NY.
- DST automático con America/New_York.
- Sintéticos y ORB no son afectados.


## 2026-08-31 — v44 Forex reinicia en Londres
- Protección rollover ya no termina 17:15 NY.
- Forex permanece bloqueado durante Asia.
- Nuevo ciclo habilitado a las 08:00 Europe/London.
- DST automático para New York y Londres.


## 2026-08-31 — v45 Forex visible y seleccionable
- Forex agregado al catálogo dinámico de instrumentos MT5.
- Nueva categoría visual Forex en /instruments.
- Selección/persistencia reutiliza el mecanismo existente.
- Se conservan restricciones rollover/Londres de v44.


## 2026-08-31 — v46 Persistencia total DB + XLSX
- Nueva tabla append-only daemon_audit_events.
- Cada resultado por símbolo queda auditado en DB.
- Lifecycle FILLED/REJECTED/UPDATED/FINALIZED queda auditado.
- Auto-reparación de posiciones MT5 faltantes en SQLite.
- Persistencia defensiva posterior a FILLED.
- XLSX se reconstruye desde trade_journal y añade Audit Log.
- Error de XLSX no interrumpe ni revierte persistencia DB.


## 2026-08-31 — v47 Arquitectura Multi-Bot
- Bots independientes SYNTHETICS/FOREX/ORB.
- Magic exclusivo por estrategia.
- Ownership estricto para BE/Runner/cierres.
- SQLite WAL + busy_timeout para concurrencia.
- Coordinador multi-bot con reinicio de workers y XLSX centralizado.
- Logs separados por worker.


## 2026-08-31 — v48 Break Even estadístico
- Banda neutral RR ±0.25R.
- Break Even excluido de wins/losses y del denominador Win Rate.
- Dashboard, repository y XLSX usan criterio coherente.


## 2026-08-31 — v49 Sintéticos por proceso
- BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP como workers independientes.
- Magic exclusivo por familia sintética.
- synthetics-split-daemon coordina los seis workers.
- report-daemon centraliza XLSX para ejecución manual independiente.
- multi-bot-daemon usa sintéticos divididos + Forex + ORB.


## 2026-08-31 — v50 Audit Log compacto
- Payload completo permanece sólo en daemon_audit_events.
- XLSX exporta resumen <= 4000 caracteres.
- Se eliminan payload/payload_json gigantes de Audit Log.
- Defensa de 30000 caracteres por celda textual.


## 2026-08-31 — v51 Dashboard central Multi-Bot
- synthetics-split-daemon ahora respeta --dashboard.
- Un único dashboard se inicia desde el coordinador.
- Workers coordinados siguen sin abrir servidores HTTP propios.
- Catálogo consolidado por perfiles y DB compartida.


## 2026-08-31 — v52 Dashboard por familias
- Nueva tabla worker_runtime_states.
- Worker heartbeat/ciclo/progreso/instrumento persistidos.
- Dashboard central muestra BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP por separado.
- Se elimina dependencia visual del ciclo único stale para modo multi-bot.


## 2026-08-31 — v53 Telemetría runtime + UTF-8
- UTF-8 forzado en procesos Windows.
- Caracteres problemáticos de consola reemplazados.
- Runtime worker antes de audit log.
- Heartbeat y resumen de workers en coordinador.
- Fingerprint de versión en consola/dashboard.
- Guard contra instalaciones con archivos mezclados.


## 2026-08-31 — v54 Dashboard contextual + Salud + Auditoría visual
- Último candidato persistente por bot desde daemon_audit_events.
- Ownership explícito de posiciones por profile/magic.
- Salud sin score artificial cuando falta telemetría.
- Nueva tabla position_visual_audits.
- Workers persisten gráficos aunque no tengan dashboard propio.
- Coordinador reconstruye auditoría visual desde SQLAlchemy.


## 2026-08-31 — v55 Auditoría de entrada persistente
- Nueva tabla trade_visual_audits por trade_id.
- entry_chart/entry_context inmutables.
- latest_chart/latest_market dinámicos.
- Dashboard alterna ENTRADA / ACTUAL.
- Cierre del trade no elimina evidencia histórica.


## 2026-08-31 — v56 Selección independiente FOREX / ORB
- Nueva persistencia por perfil SYNTHETICS / FOREX / ORB.
- FOREX y ORB ya no comparten selección.
- Workers releen la preferencia en cada ciclo.
- Dashboard /instruments con pestañas independientes.
- 65 pruebas específicas/regresión aprobadas.

## v68 — Dataset persistente Entrada vs. Ahora (2026-09-01)
- Nueva tabla append-only trade_audit_snapshots.
- /account muestra conteo, último estado y últimas 20 observaciones por trade.
- XLSX agrega hoja Entrada vs Ahora con una fila por snapshot.
- Se corrige el join de auditoría usando source_trade_id del trade_journal.
