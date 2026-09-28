# Diagnóstico y prioridades — 18 septiembre 2026

Corte aproximado10:50 Santiago. No hay trades desde17sept00:00 local en SQLite.
Workers confirman H1_PRIMARY / ATR_BOUNDED activos. No es falta de reinicio.

Panel (evaluaciones repetidas hoy):
Forex H1neutral1348, sinM15 792, sinM5 692, antiguas146, noticias35.
Sintéticos H1neutral1821, sinM5 1776, sinM15 262, dirección488,
antiguas360, ERROR30, ubicaciónH1 6.
GOLD H1neutral276, sinM5 242, antiguas168, sinM15 84.
GOLD incluye XAU, XAG e índices; no representa exclusivamente oro.
SQLite persiste una muestra/selección de evaluaciones; no mezclar sus conteos
con los contadores del panel. Archivo de detalle: smc_groups_20260918.json.

Hallazgo prioritario: NameError diagnostics en live_trading_engine.py al armar
metadata de una señal, antes de execute_with_executor.121 eventos desde17sept:
USDCHF87, V10Index4, Crash150Index30. La variable está definida en el resumen
compacto pero no en esta ruta. El bloque fue introducido con la auditoría;
las pruebas anteriores no cubrieron esta ruta completa. Es un defecto del código,
no un rechazo de mercado. No prueba121 oportunidades diferentes ni rentables.
No se corrigió ni reinició en esta revisión solicitada de análisis.

Comparaciones SQLite hoy:1318 registros de retest, cero casos adicionales limpios
con ATR. Cuatro comparaciones de zona, ninguna mejora H1 frente tres marcos.
El casoNZDJPY del17 sí cambió ubicación, pero no demuestra ejecución rentable.

GOLD deja de analizar al09:30NY (10:30Santiago); última evaluación10:25 coherente.
ÚltimoXAU H1neutral, XAGsinM15. No ampliar horario por ausencia de entradas.

Plan:
1 Corregir NameError y agregar test integral con executor simulado; recorrer
  metadata, riesgo, orden simulada y persistencia, nunca órdenes reales en tests.
2 Reiniciar controladamente y verificar versiones/configuraciones por worker;
  no dar por resuelto porque deje de aparecer error sin nuevas señales elegibles.
3 Separar señales únicas, primera detección, edad y resultado final en panel;
  distinguir sin candidato, candidato inválido, error técnico y ejecución.
4 Auditar neutralH1 por duración y eventos nuevos; validar alternativa de transición
  con CHOCH/BOS cerrado y nuevo swing, sin reciclar BOSviejo ni eliminar filtro.
5 Calibrar rechazo/desplazamiento por familia con replay. ATR actual sólo cambia
  penetración: no compensa falta de mecha o desplazamiento. No reducir80% global.
6 Caducar candidatos antiguos para selección/pantalla conservando histórico:
  USDCHF815min, Crash1350min, XAG700min en muestras. No ampliar ventana para entrar tarde.
7 Evaluar fuera de muestra con costes, riesgo, drawdown y señales únicas antes
  de generalizar nuevos parámetros. Mantener controlesRR/spread y riesgo.
