# DaemonBlackFx v12 — módulo separado de instrumentos

## Objetivo
Separar la configuración de instrumentos habilitados para nuevas entradas del dashboard operativo principal.

## Rutas
- Dashboard principal: `http://127.0.0.1:8765/`
- Gestión de instrumentos: `http://127.0.0.1:8765/instruments`

Ambas rutas usan el mismo servidor local y el mismo estado del daemon. No se crea una segunda conexión a MetaTrader5.

## Dashboard principal
La selección completa fue retirada del dashboard. En su lugar se muestra un resumen de cuántos instrumentos están habilitados y un botón **Administrar instrumentos** que abre el módulo independiente.

## Módulo de instrumentos
Permite:
- ver el catálogo descubierto desde MT5/Deriv;
- agrupar por categoría;
- ordenar alfabéticamente;
- buscar por nombre;
- seleccionar múltiples instrumentos;
- seleccionar todos o limpiar la selección;
- aplicar cambios dinámicamente.

Los cambios se aplican desde el siguiente ciclo del daemon para no modificar una iteración que ya está en curso.

## Posiciones abiertas
Deshabilitar un instrumento sólo impide nuevas entradas. Una operación ya abierta continúa con:
- SL/TP;
- Break Even;
- monitor de salud;
- gráfico de auditoría;
- sincronización y cierre normal.

## Seguridad
El módulo `/instruments` consume la misma API local `/api/instruments/selection`. El navegador no se conecta a MT5 y no ejecuta órdenes.
