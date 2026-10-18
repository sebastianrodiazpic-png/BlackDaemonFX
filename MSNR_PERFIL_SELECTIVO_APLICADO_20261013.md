# Malaysian SNR — perfil selectivo aplicado en DEMO

Se guardó el perfil solicitado el 13 de octubre de 2026 a las 12:56:27 UTC, como **versión de preferencias 15**. La lectura posterior de la API verificó los 35 controles enviados y la conservación de los restantes valores. El trabajador SNR siguió en RUNNING, con estrategia `msnr-v2.9-video-evidence`, y su ciclo 139 registró la versión de preferencias 15 a las 12:56:59 UTC. No fue necesario reiniciarlo.

Los parámetros principales ya coincidían con el perfil acordado. Se realizaron cuatro cambios efectivos:

| Parámetro | Antes | Guardado |
|---|---|---|
| Definición de obstáculos H1/D1 | Giro de cuerpos | Envolvente |
| Breaker Pair | Operar | Observación |
| Pinbar | Operar | Observación |
| Obstáculos H4 | Aplicar | Observación sin veto |

Se verificaron además:

| Control | Valor aplicado |
|---|---|
| Cuerpo mínimo Fractal H1 | 45% |
| Distancias Fractal / Continuación / QM | 0,50 ATR H1 |
| Continuación | Operar; cuerpo 50%, ADX 20, mecha máxima 25% |
| Exigir únicamente Fresh | Desactivado; permanecen las reglas de consumido y confirmación reforzada |
| Ventana de setup / recuperación | 90 / 45 minutos |
| Cuerpo mínimo de recuperación | 35% |
| ADX de ejecución Step | 23 para Step Index; 25 como mínimo general para los otros Step |
| M5 | Operar en Step Index, Step Index 200, Step Index 400 y Step Index 500; general en Observación |
| Activos y Continuación de los cuatro Step | Operar |
| Veto direccional D1 en sintéticos | Desactivado |
| Dirección macro donde es obligatoria | Estructura D1, radio de pivote 2 |
| Horario | UTC anterior |
| H4 cuando D1 queda neutral | Observación |
| Breaker Pair | Cuerpos 50%, desplazamiento 0,50 ATR H1; Observación |
| Pinbar | Mecha mínima 55%, cierre favorable mínimo 75%; Observación |
| Criterios de investigación | Frecuencia 105%, mejora WinRate 1 punto, 50 resultados resueltos |

Las excepciones y selecciones de otros instrumentos se conservaron. También se conservaron las opciones IA, los otros escenarios estructurales, el riesgo, los objetivos y la configuración de otros trabajadores. Este perfil sigue siendo una prueba DEMO: no acredita una mejora futura del WinRate ni una ventaja validada después de todos los costes.

La aplicación se realizó por la API existente de `/strategy-bases`, sin usar el navegador, sin reiniciar procesos y sin enviar órdenes desde la herramienta. El trabajador que ya estaba activo continúa aplicando sus reglas de ejecución.

Evidencia en `storage/analysis/msnr_perfil_selectivo_20261013/`: `settings_before.json`, `requested_profile.json`, `changes.json`, `settings_after.json`, `applied.json` y `worker_after_save.json`. Los ajustes permanecen guardados; “Volver a valores por defecto” puede sustituir este perfil por la referencia general de la pestaña.
