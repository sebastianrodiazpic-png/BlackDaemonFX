# Revisión de cuarentena XAGUSDmicro

Incidente 14-09-2026 15:20:58 UTC; trade 167, posición 4725699382.
SQLite registra CLOSED y emergency_split_risk_hard_cap_breach.

| Medida | Valor |
| --- | ---: |
| Precio usado al calcular | 63.054 |
| Precio al ejecutar | 63.064 |
| Stop | 62.949 |
| Volumen | 6.07 |
| Riesgo calculado previo | 31.87 |
| Objetivo por pierna | 32.22215 |
| Límite máximo | 33.34992525 |
| Riesgo tras ejecución | 34.90 |

La distancia al stop pasó de 0.105 a 0.115: aumento de 9.52%.
El exceso sobre objetivo fue 8.31%; sobre el límite, 1.55007475.
El order_check archivado ya utilizaba 63.071, sin recalcular el lote.
La evidencia atribuye el exceso al movimiento del precio entre cálculo y fill;
no a un stop modificado ni a un cambio de volumen. El cierre de emergencia
está registrado a 63.029. La validez técnica ORB no sustituye el límite de riesgo.

Protección implementada:
- El presupuesto monetario máximo de cada pierna llega hasta el proveedor MT5.
- Antes de order_send se actualiza el precio y calcula riesgo con un margen
  adverso de deviation * point.
- Si supera el presupuesto, rechaza antes de enviar; no aumenta el límite,
  ni desplaza el stop, ni cambia el lote automáticamente.
- Conserva el control posterior al fill: el margen no garantiza un fill máximo.
- Con 6.07 lotes el escenario archivado es rechazado.
- Posible efecto: menos entradas con stops estrechos o mercado rápido.

Liberación:
- Revisión autorizada registrada en storage/analysis/xagusdmicro_quarantine_review.json.
- El registro activo conserva la cuarentena con release_after_guard=PRE_SEND_RISK_CAP_V1.
- Solo un engine actualizado con el proveedor protegido puede consumirla.
- Antes de retirar el registro escribe el incidente y la revisión en
  storage/risk_quarantine_releases.jsonl.
- El proceso anterior no se reinició durante esta tarea. La liberación efectiva
  queda pendiente de recargar el worker y de su próxima evaluación del símbolo.
- No se enviaron órdenes. No se elevaron límites ni se borraron otros bloqueos.

Se corrigió además la lectura de fechas vacías/NaT de cuarentenas temporales.
Validación: 63 pruebas aprobadas, incluidas la reproducción del incidente sin
order_send, BUY/SELL con margen, cap inválido, liberación condicionada y riesgo.
Se actualizaron fixtures de pruebas anteriores para proporcionar rangos SMC y
verificar el objetivo TP2 vigente, sin modificar la política de producción.
