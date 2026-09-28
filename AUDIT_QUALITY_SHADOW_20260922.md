# Calidad de auditoría y comparaciones en sombra

Implementación en el orden autorizado: exportación y datos; trazabilidad;
comparaciones específicas sin autorización de órdenes.

## 1. Exportación y características

Excel conserva el historial de trades y limita telemetría: últimos 2.000 eventos,
1.000 snapshots Entrada vs Ahora y 1.000 snapshots de cuenta. Los JSON de contexto
se truncan a 1.000 caracteres por celda; las filas completas siguen en SQLite.
Las consultas acotadas usan la clave de inserción para no ordenar grandes payloads.
Se escribe a un archivo temporal, se da formato y se reemplaza atómicamente.
Si falla, el libro anterior permanece; no se borró el original.

Prueba real con base en modo lectura: strategy_audit_bounded_20260922.xlsx,
818.618 bytes, frente a 100.391.006 bytes del informe operativo previo. El informe
nuevo es una verificación, no una sustitución del archivo que los workers usan.

Características meta-features-v2: fuerza/delta chartista normalizados desde
fracciones nativas o porcentajes antiguos; indicadores presentes separados de
valores ausentes mediante máscaras. El spread se captura al puntuar, ATR/ADX se
copian desde la vela confirmatoria del pipeline cuando existen, y la estructura
M15 se adjunta a la señal antes de puntuar. Las características históricas no se
reescriben. Capturas/modelos con nombres incompatibles quedan excluidos del nuevo
vector; el panel de elegibilidad indica ESQUEMA_DE_FEATURES_ANTIGUO_REQUIERE_MIGRACION.
Esto puede reducir temporalmente las muestras elegibles. No se entrenó ni promovió
un modelo ni se inventaron valores ausentes.

Comparador de mercado: registra último timestamp de ambos proveedores, cobertura
coincidente, desfase firmado mediano, diferencia residual descontando el desfase,
última diferencia y bid/ask/spreads cuando hay ticks. Son diagnósticos en sombra:
no se cambia el proveedor principal ni se incorpora un veto global nuevo.

## 2. Trazabilidad

MT5: elegir el último deal de salida por tiempo/ticket, no por posición de la lista;
registrar código/motivo nativo (SL, TP, cliente, experto, stop-out...), comentario,
magic y último SL/TP conocido. Códigos desconocidos conservan el fallback histórico.
No se atribuyen bid/ask históricos inexistentes: se marca ausencia explícita.

El fill conserva execution_rr_audit: precio planificado/ejecutado, SL y TP,
RR planificado y RR desde fill. No modifica objetivos. El dashboard muestra
recuentos de fallos críticos por último análisis de cada setup único, sin sumar
cada reevaluación como nueva oportunidad.

## 3. Comparaciones específicas

ORB_REDUCED_RISK_SHADOW registra los casos donde el volumen no alcanza el riesgo
objetivo, con fracción utilizada y controles aún pendientes. entry_authorized=false;
no elimina el mínimo de riesgo de la política real ni aumenta volumen/cap.

GOLD Cuartos conserva su tolerancia operativa. tolerance_shadow compara la actual
con max(tolerancia, 0.10 ATR), acotada al 20% del cuarto, y desglosa mecha, cierre,
ubicación H1 y RR para cada dirección. No autoriza órdenes nuevas por esa variante.

strategy/smc/shadow_replay.py permite replay causal con velas BID posteriores al
cierre confirmatorio, spread ASK para ventas y barreras fijas. Si una misma vela
alcanza SL y TP, marca AMBIGUOUS_BOTH_BARRIERS; si falta desenlace, PENDING_BARRIERS.
Sus resultados no son etiquetas del modelo. El replay histórico real de XAGUSD/
XAGUSDmicro sigue pendiente de velas broker y plan causal completo: no se ha
inventado un resultado de esa tesis. La variante de tres velas permanece en sombra.

## Validación y activación

Suite ampliada inicial: 100 pruebas aprobadas. Comprobación de sintaxis JS del
panel aprobada. Existe un test histórico v113_external_market_data que importa una
clase retirada; se validó el conjunto vigente v113_1_deriv_only_market_data.

Reiniciar workers/dashboard para cargar los cambios; no se reiniciaron procesos
ni se enviaron órdenes reales durante esta implementación. El cierre Forex sigue
con sus horarios configurados; la conversión/horario broker no se cambió aquí.
