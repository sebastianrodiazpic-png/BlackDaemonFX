# Trazabilidad de decisiones de entrada (Criterio Humano + Confluencia Tripartita + IA)

Estado: aplicado sin commit el 2026-11-11 (se activa al reiniciar los workers). Interruptor: `DAEMONBLACKFX_ENTRY_DECISION_TRACE` (1 por defecto; 0 la desactiva).

## Para qué sirve

Antes de este cambio nadie podía responder "¿el comité de admisión mejora el resultado?":

- Los trades no guardaban qué decidieron el Criterio Humano, la Tripartita y la IA.
- Los eventos `TRIPARTITE_CONFLUENCE_EVALUATED` y `HUMAN_CRITERIA_EVALUATED` no llevaban `execution_key`, así que no se podían unir con el trade ni con su resultado.
- El "replay de 5 años" de la Tripartita (`tools/replay_tripartite_confluence_5y.py`) usa multiplicadores fijos y no mide nada.

Ahora cada señal que llega al comité deja un registro compacto y cada operación abierta lo conserva.

## Qué se guarda y dónde

1. **Evento de auditoría** (tabla `daemon_audit_events`), tanto para aprobadas como para vetadas:
   - `HUMAN_CRITERIA_EVALUATED`: ahora con `execution_key`, y en el payload `allowed`, `mode`, `primary_veto_factor`, `strategy_key`, `direction` (además de `score`, `grade`, `breakdown`).
   - `TRIPARTITE_CONFLUENCE_EVALUATED`: ahora con `execution_key`, y en el payload `strategy_key` y `entry_decision` (el registro completo de abajo).
2. **Trade** (tabla `trades`, columna `details_json`): `details.metadata.entry_decision`, escrito apenas MT5 confirma el fill (`LiveTradingEngine._attach_entry_decision`, llamado desde `_persist_entry_audit_immediately`). Cada pata (TP1 / RUNNER) lleva su copia con `entered: true`.

### Esquema de `entry_decision` (schema 1)

| Campo | Contenido |
|---|---|
| `evaluated_at`, `symbol`, `direction`, `strategy_key`, `bot_profile`, `execution_key` | Quién, qué y cuándo |
| `human_criteria` | `action`, `allowed`, `mode`, `score` (0–100), `grade`, `reason`, `primary_veto_factor`, `breakdown` (macro, HTF, régimen, vela, racha, spread, spike) |
| `tripartite` | `action` (`APPROVED` / `VETO_*`), `allowed`, `reason`, pilares OK, `ai_probability`, `human_criteria_score`, `is_rehabilitated_asset` |
| `ai` | `available`, y si hay meta-etiquetado: `mode`, `probability`, `net_expectancy_r`, `allowed`, `shadow`, `trained` |
| `context` | `adx_used_by_gate`, `adx`, `regime_adx`, `candle_body_ratio`, `spike_danger` |
| `entered` | `true` solo en el registro guardado en el trade |

Los campos sin dato se omiten (no se guardan `null`). Si no hubo meta-etiquetado, `ai` es `{"available": false}`: así se distingue "la IA no opinó" de "la IA dio 0".

## Dónde verlo

- **Página `/decisions`** (menú "⚖ Decisiones de entrada"; también `/decisiones`). Ventana de 1 a 30 días. Muestra: embudo por etapa, por día, por estrategia, instrumentos más vetados, últimos vetos con su motivo, y para las operaciones con decisión registrada, acierto y R por puntaje humano, por probabilidad de IA y por estrategia, más las últimas operaciones con su decisión.
- **API** `GET /api/entry-decisions?days=3` (solo lectura, origen DEMO).
- **Código**: `strategy/confluence/entry_decision.py` (lógica pura), `database/repository.py::entry_decision_report`, `dashboard/decisions_page.py`.
- **Consulta directa** (SQLite), decisión de un trade:

```sql
SELECT id, instrument, result, realized_rr,
       json_extract(details_json, '$.metadata.entry_decision.human_criteria.score')   AS puntaje_humano,
       json_extract(details_json, '$.metadata.entry_decision.tripartite.action')      AS tripartita,
       json_extract(details_json, '$.metadata.entry_decision.ai.probability')         AS p_ia
FROM trades
WHERE json_extract(details_json, '$.metadata.entry_decision') IS NOT NULL
ORDER BY id DESC LIMIT 50;
```

## Cómo usarlo para decidir

1. Dejar acumular una o dos semanas de operaciones con decisión.
2. En `/decisions`, comparar acierto y R por tramo de puntaje humano y por probabilidad de IA. Si los tramos bajos (75–80, P(IA) < 0.60) no rinden peor que los altos, el comité no está filtrando calidad.
3. Los vetos no tienen resultado asociado (la señal no se operó). Para medir su valor hace falta el siguiente paso (resultado contrafáctico, ver Pendientes del registro de cambios).

## Límites conocidos

- Solo las operaciones abiertas **después del primer reinicio con este cambio** traen `entry_decision`. Los eventos antiguos no tienen `execution_key` y no se pueden unir a su resultado. La página muestra el porcentaje de cobertura.
- Una misma señal se evalúa en cada ciclo y puede generar muchos eventos: los conteos son de **evaluaciones**, no de señales únicas ni de operaciones.
- Las posiciones importadas desde MT5 (`MT5_EXTERNAL`, `RECOVERED_MT5`) no pasaron por el comité y no llevan decisión.
- La trazabilidad nunca debe impedir una entrada: si falla al guardar, se registra `ENTRY_DECISION_TRACE_ERROR` y la operación sigue.

## Pruebas

`tests/test_v125_entry_decision_trace.py` (8 casos: registro, adjuntar sin pisar metadata, interruptor, agregados de eventos y trades, informe del repositorio, método del motor). Los casos del repositorio y del motor se saltan solos si faltan SQLAlchemy o MetaTrader5.
