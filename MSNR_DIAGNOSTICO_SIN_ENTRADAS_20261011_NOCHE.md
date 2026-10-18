# Por qué Malaysian SNR sigue sin abrir entradas

Corte reproducible: **12 de octubre de 2026, 01:27:08 UTC**, equivalente a las 22:27 del 11 de octubre en Santiago. Consulta de logs, auditoría y velas; no se alteraron parámetros ni se enviaron órdenes.

## Hallazgo principal

La estrategia está activa, utiliza `msnr-v2.6-structural-opportunities` y tiene ejecución habilitada. La preferencia 9, guardada a las **00:52:22 UTC**, tiene continuación y las cinco variantes nuevas en **Operar**. El problema observado está antes del envío de órdenes: no se registra una señal que complete estructura, retest y condiciones de entrada.

Se verificaron conexión, trading permitido en terminal, trading permitido en cuenta y autorización de expertos, todos activos. La cuenta consultada es demo. El argumento de datos `shadow` compara el feed Deriv con MT5; no convierte la ejecución de SNR en simulación. El control de Observación de escenarios es independiente y está en Operar en esta preferencia.

## Qué muestran los ciclos posteriores a Operar

Se separó la ventana posterior a la preferencia 9: **66 ciclos completos**, desde 00:52:49 hasta 01:26:11 UTC. Contienen **1.518 evaluaciones**, **0 órdenes** y **0 errores**.

| Resultado | Lecturas | Interpretación |
|---|---:|---|
| Fuera de sesión | 726 | Los 11 instrumentos tradicionales no están dentro de Londres/NY |
| Sin setup confirmado | 555 | Falta estructura completa o alguno de sus requisitos |
| Retest consumido | 66 | Boom 1000: la primera visita no confirmó y hubo un contacto posterior |
| Esperando primer retest | 66 | Step 200: el precio no volvió a la zona del hombro |
| Nivel consumido | 66 | Volatility 90: el nivel previo excede la penetración permitida |
| Setup vencido | 39 | Referencias antiguas fuera de su ventana |

Los sintéticos suman 792 lecturas; 555, aproximadamente el **70,1%**, son sin setup. Los conteos son evaluaciones repetidas, no oportunidades únicas. La auditoría está muestreada: contiene 119 eventos posteriores al ajuste, cero señales válidas y seis identificadores principales de setup. Los diagnósticos también incluyen candidatos secundarios.

La mediana de ciclo es 23,75 s; p95 31,70 s; máximo 40,07 s. Cinco ciclos exceden el objetivo de 30 s. En esta ventana no aparecen bloqueos de activo ni rechazos de órdenes; no hay evidencia de que la demora explique la ausencia de entradas confirmadas.

## Casos concretos reconstruidos con el feed de análisis

### Boom 1000 — QM ampliado

Ruptura cerrada a las **00:00 UTC**, nivel **15.818,423**, ATR H1 **52,2393**.

- A las 00:15, el cierre fue 15.853,557. El cuerpo direccional M15 era fuerte, 83,35%, pero la distancia al nivel fue **0,6726 ATR**, superior al máximo **0,50**.
- A las 00:30, la vela fue bajista y no confirmó una recuperación alcista.
- A las 00:45, el precio volvió a contactar la zona después de haberse separado. La lógica de primer retest lo clasificó como consumido.
- A las 01:15 hubo recuperación alcista cercana al nivel, pero la visita inicial ya estaba consumida; no se puede convertir ese retorno en otro primer retest.

La comparación estática con distancia QM/A/V 0,70 permitió confirmar el retest de las 00:15, pero lo rechazó después por **obstáculo antes del objetivo mínimo de 2R**. Ampliar solo esa distancia tampoco habría generado una entrada válida. El cierre de las 00:15 ocurrió antes de activar Operar a las 00:52:22; esta reconstrucción no representa una orden perdida durante la nueva preferencia.

El control visible de distancia **Fractal** no cambia el máximo de QM ni A/V: estos usan el parámetro general de 0,50 ATR. Es una diferencia de alcance que debe tenerse en cuenta al ajustar el formulario.

### Step Index 200 — QM ampliado

Setup vendedor desde las **00:00 UTC**, hombro **10.670,2**, ATR H1 **16,1429**. Con tolerancia 0,35 ATR, la zona empieza aproximadamente en **10.664,55** por debajo del nivel. El máximo M15 posterior observado hasta el corte fue **10.654,6**: no llegó a la zona.

Esperar primer retest es coherente con esos datos. Entrar habría significado vender lejos del hombro; bajar cuerpo Fractal no corrige la ausencia de retorno. Su ventana terminaba a las 01:30 UTC y las lecturas posteriores observadas ya muestran el vencimiento.

### Volatility 90 — continuación

Nivel **24.857,426**, ruptura de las **00:00 UTC**. El diagnóstico del nivel previo registra una visita y penetración de **0,7521 ATR**, frente al límite existente **0,20 ATR**. Por eso se considera consumido incluso con «Exigir nivel realmente Fresh» desmarcado: desmarcarlo permite una visita controlada, no cualquier penetración.

Además, el diagnóstico registra un candidato secundario con **recuperación de retest vencida**. Las variantes se están detectando, pero ese candidato tampoco completa la entrada.

### Jump 25 — Fractal

En la vela H1 cerrada a las **01:00 UTC** hay barrido y ruptura alcistas, pero cuerpo **38,39%**, inferior al mínimo guardado **45%**. Es un caso donde el cuerpo sí limita la detección.

Comparar 40% no cambia el resultado. Comparar 35% reconoce el Fractal, pero devuelve **esperando recuperación del retest M15**, sin señal válida. Se compararon seis activos con cuerpo 40% y 35%; ninguno produjo una señal válida al mismo corte. Esta prueba es un diagnóstico puntual, no un backtest de rentabilidad.

Step Index 400 presenta cuerpo 48,86%, superior al mínimo 45%, pero no tiene la ruptura direccional requerida. Reducir el cuerpo no resuelve ese caso.

## Por qué los cambios no equivalen todavía a más entradas

Los controles Fractal actúan solo sobre Fractal. Continuación, A/V ampliado y cambio de función conservan cuerpo mínimo 50%, ADX 20 y mecha máxima 25%. QM necesita geometría, ruptura y retest; Open–Close necesita una separación material y retorno confirmado. En los diagnósticos sintéticos consultados, Open–Close aparece sin separación material, no con fallo de permiso de trading.

La mayoría de las esperas repetidas corresponde a setups de las 00:00, anteriores al cambio a Operar. Cambiar el modo no reinicia el historial de visitas ni permite entrar retrospectivamente en una confirmación anterior. Tras el ajuste solo se había observado un nuevo cierre H1 a las 01:00; la ventana en Operar era de unos 35 minutos.

El modo de activos adicionales también está en Operar, pero **su lista está vacía**. No se añadieron Jump 50/100/75 ni Volatility 75 (1s): el ciclo conserva 23 activos, de los que 12 son sintéticos. Esto describe la selección guardada; no se modificó.

## Qué investigar a continuación

La evidencia permite priorizar un diagnóstico por candidato que conserve el primer motivo de rechazo, no solo el estado final «consumido» o «vencido». El caso Boom 1000 muestra por qué: detrás de ese estado había primero exceso de distancia y, al relajarlo en comparación, un obstáculo.

Conviene separar en el panel el alcance de la distancia Fractal y la de QM/A/V, y medir primero cuántas candidatas completas recuperaría cada variante sin perder el espacio de objetivos. También conviene comparar confirmación M15 con M5 usando datos nativos, si las primeras recuperaciones se alejan antes del cierre M15. Estos son experimentos pendientes; no justifican activar más relajaciones ni afirmar mayor WinRate.

No se demostró un fallo de registro: el worker y la auditoría registran las evaluaciones, pero no existe una entrada válida en el período analizado. El journal global consultado tampoco tiene entradas nuevas en las seis horas revisadas. Las instantáneas de otros workers muestran espera de estructura, sesión y filtros propios; eso no sustituye una auditoría detallada de cada estrategia.

## Evidencia guardada

Directorio: `storage/analysis/msnr_no_entries_20261012_012708/`.

- `summary.json`: conteos de ciclos, motivos y configuración.
- `details.json`: auditoría muestreada, candidatos, ciclos e instantáneas de workers.
- `entry_probes.json` y archivos de velas: reconstrucción de seis activos a un corte fijo.
- `frozen_timelines.json`: secuencia de cierres M15 y comparaciones estáticas.
- `broker_permissions.json`: permisos consultados, sin identificadores de cuenta.

La reconstrucción emplea el mismo feed primario Deriv con fallback MT5 del proyecto y utiliza únicamente velas cerradas al corte. Las comparaciones no envían órdenes, no aplican cambios y no validan ejecución real, costes ni WinRate.
