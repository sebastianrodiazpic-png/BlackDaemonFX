# -*- coding: utf-8 -*-
with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "r", encoding="utf-8") as f:
    content = f.read()

target = "## Historial de cambios (más reciente primero)\n"
if target not in content:
    print("ERROR: Target no encontrado")
    exit(1)

new_entry = """## Historial de cambios (más reciente primero)

### 2026-11-09 — Rediseño .daemon-card y humanización pedagógica en Trend Pullback H1/M15  ·  Estado: aplicado sin commit
- **Qué**:
  1. Rediseño completo del panel `trendPullbackAuditPanel` en `dashboard/strategy_bases_page.py` adoptando el estándar de cartas coleccionables legendarias `.daemon-card` con doble marco dorado biselado, máscara obsidian y chapas metálicas grabadas en 3D `BLACKDAEMON FX`.
  2. Humanización integral de los textos para cualquier trader:
     - Explicación de la "zona de valor" conformada por la media rápida EMA 20 y lenta EMA 50 en 1 hora, prohibiendo operar contra la marea institucional.
     - Detalle del gatillo estructural en 15 minutos (quiebre de swing con cuerpo de vela), evitando el error común del trader minorista de comprar al simple toque.
     - Justificación de por qué los 30 índices sintéticos de Deriv (como Volatility 25 +133.25R y Jump 10 +129.00R) son el escenario ideal al operar 24/7 sin noticias macro imprevistas.
     - Claridad total sobre la poda de los 35 activos de mercados reales (Forex, Metales e Índices) debido al rollover nocturno (swap) y cierres diarios que degradan la señal de pullback.
- **Por qué / evidencia**: Homogeneizar visual y conceptualmente todas las pestañas de auditoría de `/strategy-bases` solicitadas por el usuario, manteniendo la integridad del Replay Fiel de 5 Años (+811.45R netos y 50.93% WR).
- **Ficheros**:
  - `dashboard/strategy_bases_page.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**: No requiere nuevos interruptores. Sincronizado con `/instruments`.
- **Tests**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (6 passed).
  - `tests/test_strategy_bases_5y_all_records.py` (6 passed).
  - Verificación de balance de divs HTML (0 tags desbalanceados).
"""

content = content.replace(target, new_entry, 1)

with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "w", encoding="utf-8") as f:
    f.write(content)

print("REGISTRO_CAMBIOS_ESTRATEGIA.md actualizado con éxito.")
