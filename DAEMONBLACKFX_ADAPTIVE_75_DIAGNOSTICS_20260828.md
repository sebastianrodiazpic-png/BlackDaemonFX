# DaemonBlackFx - Confirmación explicable y modo adaptativo 75%

Fecha: 2026-08-28

## Objetivo

El daemon ahora informa por qué una entrada se confirma o se rechaza y separa dos métricas:

- `trade_score`: calidad ponderada de la señal.
- `confirmation_percentage`: porcentaje real de confirmaciones evaluadas que se cumplieron.

## Regla de decisión

### STRICT_CONFIRMED

La entrada cumple todas las condiciones configuradas como obligatorias y el score mínimo estricto.

### ADAPTIVE_75_CONFIRMED

La entrada puede considerarse viable aunque falte alguna confirmación secundaria cuando se cumplen simultáneamente:

1. `confirmation_percentage >= 75%`.
2. Todas las confirmaciones críticas están presentes.
3. `trade_score >= 75`.

### REJECTED

Se rechaza cuando ocurre cualquiera de estas situaciones:

- Falta una confirmación crítica SMC/contextual.
- El porcentaje de confirmaciones es inferior a 75%.
- El trade score viable es inferior a 75.

## Confirmaciones críticas

No pueden compensarse con un porcentaje alto:

- Tendencia H1 alineada.
- Setup M15 existente.
- Liquidity Sweep.
- Ruptura de estructura M15 (CHOCH/BOS).
- Premium/Discount correcto.
- Order Block fresco.
- Retest limpio.
- Vela direccional coherente.
- Modo de confirmación del OB satisfecho.

## Confirmaciones secundarias

Pueden aportar calidad sin bloquear automáticamente una entrada adaptativa si el resto del contexto es sólido:

- Rejection.
- Displacement.
- Microestructura M5.
- Strong close.
- Momentum, cuando está habilitado.
- Patrón armónico.

Los patrones armónicos permanecen habilitados y aportan bonus al score, pero ya no son obligatorios por defecto en el modo daemon.

## Diagnóstico en consola

Cuando existe un candidato M5 evaluable, la consola puede mostrar información similar a:

```text
Confirmaciones: 11/14 | 78.6% | score=85.00 | decisión=ADAPTIVE_75_CONFIRMED
Faltantes: harmonic_confirmation, strong_close
```

Si la señal se rechaza:

```text
Confirmaciones: 12/14 | 85.7% | score=90.00 | decisión=REJECTED
Críticas faltantes: premium_discount
Rechazo: CRITICAL_CONFIRMATION_MISSING
```

Esto evita aceptar señales sólo porque superan 75%: una falla estructural crítica continúa bloqueando la entrada.

## Configuración por defecto

```python
adaptive_confirmation_enabled = True
minimum_confirmation_ratio = 0.75
minimum_viable_trade_score = 75.0
harmonic_enabled = True
require_harmonic = False
harmonic_bonus_points = 10.0
```

## Gestión monetaria conservada

No se modifica la gestión implementada anteriormente:

- Riesgo total lógico: 1%.
- TP1: 0.5% de riesgo, objetivo 1R.
- RUNNER: 0.5% de riesgo, objetivo 2R.
- Break Even del RUNNER al alcanzar 1R.
- Break Even desplazado 2 puntos hacia beneficio.

## Pruebas

- 160 pruebas aprobadas en el entorno disponible.
- 8 módulos no se pueden recolectar en Linux porque importan directamente el paquete nativo `MetaTrader5`, destinado al entorno Windows/MT5.
