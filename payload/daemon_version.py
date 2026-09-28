"""Sello de versión y fecha de compilación del daemon.

Modulo deliberadamente minimo y sin dependencias, para poder importarlo
desde cualquier punto sin arrastrar nada.

`DAEMONBLACKFX_VERSION` no es un numero semantico: es una etiqueta
descriptiva que resume las funcionalidades incorporadas en la version. Se
actualiza a mano en cada hito.

Vinculaciones:
- Lo muestran el dashboard y la cabecera de arranque de `app.main`.
- Queda registrado en la telemetria para poder correlacionar el
  comportamiento observado con la version que lo produjo.
"""

DAEMONBLACKFX_VERSION = "v116-deriv-annotated-trade-audit"
BUILD_DATE = "2026-09-14"
