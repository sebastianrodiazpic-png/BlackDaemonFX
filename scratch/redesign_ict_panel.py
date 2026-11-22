# -*- coding: utf-8 -*-
import re

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    content = f.read()

# Buscamos desde id="ictAuditPanel" hasta el cierre del panel antes de <!-- PANEL DE AUDITORÍA TREND PULLBACK
pattern = re.compile(
    r'id="ictAuditPanel" style="display: none; margin-bottom: 24px;">.*?(?=\s*<!-- PANEL DE AUDITORÍA TREND PULLBACK)',
    re.DOTALL
)

match = pattern.search(content)
if not match:
    print("ERROR: No se encontro el bloque id=\"ictAuditPanel\"")
    exit(1)

print("Bloque encontrado, longitud:", len(match.group(0)))

new_ict_panel = '''<div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Estrategia ICT: Liquidez Institucional, Desequilibrios de Precio y Filtro con IA (Replay Fiel 5 Años)
              <!-- ICT Sabri Malle -->
            </h2>
            <div class="badge badge-cyan">Replay Fiel 5 Años · 59 Activos Ganadores (+50% Acierto) · +8,038.81R Netos Ganados · 14 Descartados · 73 Evaluados</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> analizada vela por vela, sin trucos ni anticipación, sobre los <strong>73 activos del catálogo oficial</strong>. Esta estrategia detecta la huella del dinero institucional mediante vacíos de liquidez (Fair Value Gaps en 15 minutos) y desequilibrios de precio, validando cada entrada con nuestro modelo predictivo de Inteligencia Artificial (83% de precisión histórica).<br>
            Bajo nuestra gestión profesional de 2 órdenes (asegurar ganancia en 1:1, mover a Break-Even y dejar correr la segunda orden hacia 1:2 o 1:4), <strong>59 activos resultaron altamente rentables, acumulando 37,918 operaciones ganadoras y +8,038.81 veces el riesgo asumido (60.5% de acierto ponderado)</strong>. Los 14 activos con ruido excesivo o comisiones desfavorables fueron descartados automáticamente para blindar tu cuenta.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <!-- CARD 1: SINTÉTICOS DERIV -->
            <div class="daemon-card daemon-card-accent-green">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚡ Sintéticos Deriv (33 Ganadores)</div>
                  <div class="daemon-card-badge">+500.1R Netos · 33 Activos</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Líderes de Alta Precisión:</strong> <code>Crash 300</code> (optimizado con <strong>+170.34R netos y 66.98% de acierto</strong>), <code>Volatility 25</code> (+55.3R, 59.2% acierto) y <code>Vol 100 1s</code> (+23.5R, 56.4% acierto) respetan los vacíos de liquidez con precisión milimétrica.</div>
                  <div class="daemon-card-bullet">• <strong>Especialistas en Impulsos (Boom & Jump):</strong> <code>Jump 25</code> (+35.6R), <code>Jump 10</code> (+33.6R), <code>Step 200</code> (+30.0R) y <code>Crash 500</code> (+29.9R) logran alta asimetría al entrar tras confirmación estructural.</div>
                  <div class="daemon-card-bullet">• <strong>Rehabilitados con Inteligencia Artificial:</strong> <code>Crash 1000</code> (+86.18R con <strong>55.4% de acierto</strong> en 814 operaciones) y <code>Jump 50</code> (+19.5R) pasaron de dar pérdidas a ser altamente rentables gracias al filtro de alta probabilidad.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SYNTHETICS ENGINE · HIGH PRECISION</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: FOREX LONDRES -->
            <div class="daemon-card daemon-card-accent-cyan">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">💱 Divisas Forex (Sesión de Londres)</div>
                  <div class="daemon-card-badge">+17.5R Netos · 9 Pares Élite</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pares con Mayor Volumen Institucional:</strong> Las mejores entradas se concentran en la sesión europea de Londres: <code>GBPUSD</code> (<strong>55.32% de acierto</strong>), <code>USDCHF</code> (<strong>54.90% de acierto</strong>), <code>EURJPY</code> (52.83% acierto) y <code>CADCHF</code> (52.63% acierto).</div>
                  <div class="daemon-card-bullet">• <strong>Protección Contra Rangos Muertos:</strong> Se descartan sesiones asiáticas y horarios de bajo volumen donde las trampas y falsos quiebres generan pérdidas innecesarias.</div>
                  <div class="daemon-card-bullet">• <strong>Micro-Lotes Sincronizados:</strong> Cada par opera con su variante micro sincronizada para garantizar que el cálculo de riesgo y tamaño de lote sea exacto en cualquier tamaño de cuenta.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">LONDON KILLZONE · SMART MONEY</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: METALES E ÍNDICES -->
            <div class="daemon-card daemon-card-accent-gold">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🪙 Índices Bursátiles y Metales</div>
                  <div class="daemon-card-badge">+76.5R a Mercado · Ratios 1:3 a 1:5</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>US Tech 100 (Nasdaq):</strong> Excelente rendimiento con <strong>75.00% de acierto</strong>, Factor de Beneficio 3.00 y <strong>+16.0R netos</strong>, capturando aceleraciones limpias tras la apertura.</div>
                  <div class="daemon-card-bullet">• <strong>Wall Street 30 (Dow Jones):</strong> Rescatado con <strong>56.76% de acierto</strong> y <strong>+4.5R</strong>, evitando la volatilidad inicial y montándose en la verdadera tendencia institucional.</div>
                  <div class="daemon-card-bullet">• <strong>Oro (XAUUSD) y Petróleo (US Oil):</strong> Rendimiento consistente con <strong>54.55% de acierto</strong> (+54.1R en petróleo a mercado) barriendo liquidez previa en temporalidades mayores.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">WALL STREET INDICES & COMMODITIES</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: PODA PREVENTIVA -->
            <div class="daemon-card daemon-card-accent-purple">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ Filtro de Ruido y Protección</div>
                  <div class="daemon-card-badge">14 Pares Descartados</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pares Descartados (Protección de Capital):</strong> Se excluyeron 12 pares de Forex inconsistentes (como EURAUD, AUDUSD, EURCAD y USDJPY) para evitar operaciones en contra de liquidez.</div>
                  <div class="daemon-card-bullet">• <strong>Sintéticos con Comisiones Altas:</strong> Se descartaron activos como VolSwitch High Vol y HF Vol 50 por spreads y comisiones excesivas que perjudicaban el beneficio neto.</div>
                  <div class="daemon-card-bullet">• <strong>Control y Transparencia Total:</strong> Todos los activos evaluados y sus resultados se encuentran 100% auditados y sincronizados en la sección de <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">Catálogo de Instrumentos</a>.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT RISK SHIELD · CAPITAL FIRST</div>
                </div>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 14px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12.5px;">
              💡 Los activos rentables y podados están sincronizados en tiempo real con el catálogo institucional en <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ver Todos los Instrumentos en /instruments →</a>
          </div>
        </div>
      </div>'''

new_content = content[:match.start()] + new_ict_panel + content[match.end():]

with open("dashboard/strategy_bases_page.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("dashboard/strategy_bases_page.py actualizado exitosamente.")
