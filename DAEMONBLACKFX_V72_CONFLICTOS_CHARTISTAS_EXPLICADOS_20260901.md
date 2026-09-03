# DaemonBlackFx v72 — Conflictos chartistas explicados

## Objetivo
Reemplazar el mensaje genérico `Conflicto chartista detectado` por una explicación
auditable de las fuerzas técnicas opuestas.

## Nuevos campos persistidos
- chart_pattern_supporting_pattern
- chart_pattern_supporting_direction
- chart_pattern_supporting_strength
- chart_pattern_supporting_evidence
- chart_pattern_conflicting_pattern
- chart_pattern_conflicting_direction
- chart_pattern_conflicting_strength
- chart_pattern_conflicting_evidence
- chart_pattern_conflict_level
- chart_pattern_conflict_reason
- chart_pattern_conflict_strength_delta

## Niveles
- DOMINANT_CONTRA: sólo existe patrón contrario suficientemente fuerte.
- CONTRA_MAS_FUERTE: el patrón contrario supera al alineado por >5 puntos porcentuales.
- FUERZAS_SIMILARES: la diferencia entre ambos es <=5 puntos porcentuales.
- CONTRA_SECUNDARIO: existe patrón contrario, pero el alineado es >5 puntos más fuerte.
- NONE: no hay conflicto válido.

## Dashboard
`Entrada vs. ahora` muestra:
- patrón principal;
- patrón a favor, dirección y fuerza;
- patrón en contra, dirección y fuerza;
- explicación textual del conflicto;
- nivel del conflicto.

## Persistencia
La explicación queda dentro del `entry_context` y del estado actual persistido
en SQLAlchemy, y `/account` expone los mismos detalles.
