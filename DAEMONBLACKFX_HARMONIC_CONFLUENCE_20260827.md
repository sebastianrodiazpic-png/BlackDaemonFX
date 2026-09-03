# DaemonBlackFx — Confirmación por patrones armónicos

## Objetivo

Agregar patrones armónicos como **confluencia** de las confirmaciones existentes H1 → M15 → M5, sin convertir el patrón armónico en una señal independiente.

## Patrones implementados

- Gartley
- Bat
- Butterfly
- Crab

La detección usa cinco swings confirmados X-A-B-C-D y relaciones de Fibonacci con tolerancia configurable.

## Integración

La secuencia queda:

H1 contexto → M15 setup → liquidity sweep → CHOCH/BOS → Order Block → retest M5 → rechazo → displacement → micro BOS → strong close → **patrón armónico opcional** → score → Risk Engine.

El punto D del patrón debe estar dentro del Order Block o a una distancia máxima del 50% del ancho del OB. Además, D no puede ser demasiado antiguo ni posterior a la vela de confirmación.

## Configuración inicial recomendada

```python
harmonic_enabled = True
harmonic_tolerance = 0.10
harmonic_minimum_score = 75.0
harmonic_bonus_points = 10.0
require_harmonic = False
```

### Por qué `require_harmonic = False`

Un patrón armónico válido es relativamente infrecuente. Hacerlo obligatorio desde el primer día podría reducir demasiado el número de operaciones y sesgar las pruebas. Inicialmente se utiliza como confluencia: si existe, suma 10 puntos; si no existe, la entrada todavía puede ser válida si supera el resto de filtros.

Cuando tengamos suficiente muestra, podemos probar por separado:

- sin armónicos;
- armónico como bonus;
- armónico obligatorio;
- cada patrón individual.

## Auditoría

Cada confirmación devuelve:

- `harmonic_confirmed`
- `harmonic_pattern`
- `harmonic_direction`
- `harmonic_score`
- `harmonic_bonus`
- `harmonic_x_time`
- `harmonic_a_time`
- `harmonic_b_time`
- `harmonic_c_time`
- `harmonic_d_time`
- `harmonic_ratios`
- `harmonic_rejection_reason`

Esto permitirá analizar posteriormente si los trades con Gartley/Bat/Butterfly/Crab tienen mejor expectativa que los trades sin patrón.

## Nota metodológica

Los patrones armónicos son aproximaciones geométricas basadas en ratios; no garantizan una reversión. Por eso el sistema exige que estén alineados con el Order Block y las confirmaciones SMC existentes.
