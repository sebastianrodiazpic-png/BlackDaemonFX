# -*- coding: utf-8 -*-
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    content = f.read()

# Buscar el cierre de orbAuditPanel y la apertura de ictAuditPanel
target = """                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT CAPITAL SHIELD · NO NOISE</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">"""

replacement = """                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT CAPITAL SHIELD · NO NOISE</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">"""

if target not in content:
    print("ERROR: Target no encontrado")
    exit(1)

content = content.replace(target, replacement, 1)

with open("dashboard/strategy_bases_page.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Cierre de orbAuditPanel corregido con éxito.")
