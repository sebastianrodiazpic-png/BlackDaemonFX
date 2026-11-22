import re

with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    orig = f.read()

assert orig.startswith("_INSTRUMENTS_HTML = r'''")
inner = orig[len("_INSTRUMENTS_HTML = r'''"):]

# 1. Update CSS
style_start = inner.find('<style>')
style_end = inner.find('</style>')

new_css = """
      :root {
        color-scheme: dark;
        --bg: #050708;
        --panel: #0a0e10;
        --panel2: #0c1015;
        --panel3: #12181e;
        --text: #f5f5f2;
        --muted: #9fa2a5;
        --line: #5b4514;
        --line-bright: #8a6820;
        --good: #00db79;
        --good-dim: rgba(0, 219, 121, 0.12);
        --bad: #ff453a;
        --bad-dim: rgba(255, 69, 58, 0.12);
        --gold: #f6cb57;
        --accent: #d79b19;
        --accent-dim: rgba(215, 155, 25, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        background: radial-gradient(circle at 78% 0, rgba(215, 155, 25, 0.08), transparent 28%), #050708;
        color: var(--text);
        font: 14px/1.45 system-ui, -apple-system, Segoe UI, sans-serif;
      }

      .appShell {
        display: grid;
        grid-template-columns: 270px minmax(0, 1fr);
        min-height: 100vh;
      }

      .brandSidebar {
        border-right: 1px solid #6b4d13;
        background: linear-gradient(180deg, #050708, #070b0d 65%, #090806);
        padding: 18px 14px;
        display: flex;
        flex-direction: column;
        gap: 14px;
        position: sticky;
        top: 0;
        height: 100vh;
        box-sizing: border-box;
        align-self: start;
        z-index: 50;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #3b2a0c transparent;
      }

      .brandSidebar::-webkit-scrollbar {
        width: 6px;
      }
      .brandSidebar::-webkit-scrollbar-thumb {
        background: #3b2a0c;
        border-radius: 4px;
      }

      .brandLogo {
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-radius: 14px;
        border: 1px solid #7b5816;
        box-shadow: 0 0 28px rgba(215, 155, 25, 0.12);
      }

      .brandName {
        font-size: 20px;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-align: center;
      }
      .brandName span {
        color: #f6cb57;
      }

      .brandTag {
        text-align: center;
        color: #c9a34a;
        font-size: 11px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }

      .sideNav {
        display: grid;
        gap: 7px;
        margin-top: 4px;
      }

      .sideNav a {
        color: #d9dde0;
        text-decoration: none;
        padding: 11px 12px;
        border: 1px solid transparent;
        border-radius: 9px;
        font-weight: 650;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s ease;
      }

      .sideNav a:hover,
      .sideNav a.active {
        background: linear-gradient(90deg, rgba(215, 155, 25, 0.24), rgba(215, 155, 25, 0.05));
        border-color: #6f5015;
        color: #ffd465;
      }

      .sideStatus {
        margin-top: auto;
        border: 1px solid #725116;
        background: #0d1214;
        border-radius: 12px;
        padding: 12px;
      }
      .sideStatus b {
        color: var(--good);
        font-size: 13px;
        display: block;
      }
      .sideStatus .sub {
        color: var(--muted);
        font-size: 11px;
        margin-top: 2px;
      }

      .wrap {
        max-width: none;
        margin: 0;
        padding: 18px 24px 28px;
        min-width: 0;
      }

      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 14px;
        flex-wrap: wrap;
        margin-bottom: 16px;
      }

      .title {
        font-size: 22px;
        font-weight: 850;
        letter-spacing: 0.02em;
        color: #f5f5f2;
      }
      .title strong {
        color: #f6cb57;
      }

      .sub {
        color: var(--muted);
        font-size: 12.5px;
        margin-top: 2px;
      }

      .badge {
        padding: 6px 14px;
        border: 1px solid #725116;
        border-radius: 999px;
        background: #0d1214;
        font-size: 11px;
        font-weight: 750;
        color: #ffd465;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 14px rgba(215, 155, 25, 0.15);
      }

      @media (max-width: 1050px) {
        .appShell {
          grid-template-columns: 1fr;
        }
        .brandSidebar {
          position: relative;
          height: auto;
          display: grid;
          grid-template-columns: 90px 1fr;
          align-items: center;
        }
        .brandLogo {
          width: 90px;
        }
        .sideNav {
          grid-column: 1/-1;
          grid-template-columns: repeat(4, 1fr);
        }
        .sideStatus {
          display: none;
        }
      }

      @media (max-width: 620px) {
        .sideNav {
          grid-template-columns: 1fr 1fr;
        }
        .brandSidebar {
          grid-template-columns: 72px 1fr;
          padding: 10px;
        }
      }

      /* Card principal con acabado biselado dorado de Strategy-bases */
      .card {
        background: #0a0e10;
        border: 1px solid rgba(91, 69, 20, 0.55);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(246, 203, 87, 0.08);
      }

      .head {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 12px;
      }

      /* Pestañas de perfiles al estilo de Strategy-bases */
      #profileTabs {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        background: #080c0f;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(91, 69, 20, 0.45);
      }

      .profileTab {
        background: transparent;
        color: var(--muted);
        border: 1px solid transparent;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.02em;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

      .profileTab:hover {
        color: #ffd465;
        background: rgba(215, 155, 25, 0.08);
        border-color: rgba(215, 155, 25, 0.3);
      }

      .profileTab.active {
        background: linear-gradient(90deg, rgba(215, 155, 25, 0.25), rgba(215, 155, 25, 0.06));
        border: 1px solid #d79b19;
        color: #ffd465;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4), 0 0 14px rgba(215, 155, 25, 0.2);
      }

      .actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: center;
      }

      .btn {
        display: inline-block;
        border: 1px solid rgba(91, 69, 20, 0.45);
        background: #0d1214;
        color: #d9dde0;
        text-decoration: none;
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 12.5px;
        font-weight: 650;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .btn:hover {
        border-color: #ffd465;
        color: #ffd465;
        background: rgba(215, 155, 25, 0.08);
      }

      #selectProfitable {
        background: rgba(0, 219, 121, 0.08);
        border: 1px solid rgba(0, 219, 121, 0.45);
        color: #00db79;
        font-weight: 750;
      }

      #selectProfitable:hover {
        background: rgba(0, 219, 121, 0.16);
        border-color: #00db79;
        box-shadow: 0 0 14px rgba(0, 219, 121, 0.25);
      }

      .btn.primary, #save {
        background: linear-gradient(135deg, #d79b19 0%, #f6cb57 100%);
        color: #050708;
        border: 1px solid #ffd465;
        font-weight: 850;
        box-shadow: 0 4px 14px rgba(215, 155, 25, 0.35);
      }

      .btn.primary:hover, #save:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(215, 155, 25, 0.5);
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      /* Barra de estadísticas */
      .stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 10px;
        margin: 14px 0;
      }

      .metric {
        background: #0c1015;
        border: 1px solid rgba(91, 69, 20, 0.45);
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        transition: border-color 0.2s ease;
      }

      .metric:hover {
        border-color: rgba(215, 155, 25, 0.6);
      }

      .metric .sub {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--muted);
        font-weight: 650;
      }

      .metric b {
        font-size: 18px;
        font-weight: 850;
        line-height: 1.2;
      }

      /* Barra de búsqueda */
      .search {
        width: 100%;
        max-width: 400px;
        background: #080c10;
        border: 1px solid rgba(91, 69, 20, 0.45);
        color: #f5f5f2;
        border-radius: 9px;
        padding: 9px 14px;
        font-size: 13px;
        transition: all 0.2s ease;
      }

      .search:focus {
        outline: none;
        border-color: #ffd465;
        box-shadow: 0 0 14px rgba(215, 155, 25, 0.25);
        background: #0a0f14;
      }

      /* Grilla de grupos de instrumentos */
      .instrumentGrid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-top: 14px;
        align-items: start;
      }

      @media (max-width: 1200px) {
        .instrumentGrid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }

      @media (max-width: 768px) {
        .instrumentGrid { grid-template-columns: 1fr; }
      }

      .group {
        border: 1px solid rgba(91, 69, 20, 0.45);
        border-radius: 14px;
        padding: 12px 14px;
        background: linear-gradient(180deg, #0e1319 0%, #080b0f 100%);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(246, 203, 87, 0.06);
        display: flex;
        flex-direction: column;
        min-width: 0;
        overflow: hidden;
        transition: border-color 0.2s ease;
      }

      .group:hover {
        border-color: rgba(215, 155, 25, 0.45);
      }

      .groupHeader {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 9px;
        padding-bottom: 7px;
        border-bottom: 1px solid rgba(91, 69, 20, 0.35);
      }

      .groupHeader h3 {
        margin: 0;
        font-size: 13.5px;
        font-weight: 800;
        color: #f5f5f2;
        display: flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.01em;
      }

      .groupCount {
        font-size: 11px;
        font-weight: 600;
        color: #ffd465;
        background: rgba(215, 155, 25, 0.12);
        border: 1px solid rgba(215, 155, 25, 0.25);
        border-radius: 999px;
        padding: 1px 7px;
      }

      .cardTag {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        white-space: nowrap;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        flex-shrink: 0;
      }

      .tagIct { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }
      .tagMsnr { background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.35); }
      .tagOrb { background: rgba(0, 219, 121, 0.12); color: #00db79; border: 1px solid rgba(0, 219, 121, 0.35); }
      .tagTp { background: rgba(192, 132, 252, 0.12); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.35); }

      .groupItems {
        max-height: none !important;
        overflow: visible !important;
        overflow-y: visible !important;
        padding-right: 0;
        display: flex;
        flex-direction: column;
        gap: 3px;
      }

      /* Micro-tarjeta de cada instrumento */
      .item {
        display: flex;
        gap: 10px;
        align-items: center;
        justify-content: space-between;
        padding: 7px 11px;
        border-radius: 8px;
        border: 1px solid rgba(91, 69, 20, 0.25);
        background: rgba(255, 255, 255, 0.02);
        transition: all 0.18s ease;
        cursor: pointer;
        min-width: 0;
        margin-bottom: 3px;
      }

      .item:hover {
        background: rgba(215, 155, 25, 0.07);
        border-color: rgba(215, 155, 25, 0.45);
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.35);
      }

      .item input[type="checkbox"] {
        accent-color: #00db79;
        width: 15px;
        height: 15px;
        cursor: pointer;
        flex-shrink: 0;
      }

      .symName {
        font-weight: 700;
        font-size: 13px;
        color: #f5f5f2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        margin-right: 6px;
      }

      .prunedItem {
        opacity: 0.82;
      }

      .prunedItem:hover {
        opacity: 1;
      }

      /* BADGES DE ESTADO (ESTRICTO SEGÚN INSTRUCCIÓN) */
      .activeBadge {
        font-size: 10.5px;
        font-weight: 750;
        letter-spacing: 0.03em;
        background: rgba(0, 219, 121, 0.12);
        color: #00db79;
        border: 1px solid rgba(0, 219, 121, 0.45);
        padding: 2.5px 8.5px;
        border-radius: 999px;
        margin-left: auto;
        white-space: nowrap;
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        box-shadow: 0 0 8px rgba(0, 219, 121, 0.15);
      }

      .pruneBadge {
        font-size: 10.5px;
        font-weight: 750;
        letter-spacing: 0.03em;
        background: rgba(255, 69, 58, 0.12);
        color: #ff453a;
        border: 1px solid rgba(255, 69, 58, 0.45);
        padding: 2.5px 8.5px;
        border-radius: 999px;
        margin-left: auto;
        white-space: nowrap;
        flex-shrink: 0;
        cursor: help;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        box-shadow: 0 0 8px rgba(255, 69, 58, 0.15);
      }

      .msg {
        margin-top: 14px;
        color: #ffd465;
        font-size: 12.5px;
        font-weight: 600;
        min-height: 24px;
      }

      .note {
        margin-top: 14px;
        padding: 12px 16px;
        border-left: 3px solid #d79b19;
        background: #0c1015;
        border-radius: 8px;
        font-size: 12px;
      }
"""

inner = inner[:style_start + len('<style>')] + new_css + inner[style_end:]

# 2. Update HTML stats labels and buttons in inner
new_stats_markup = """        <div class="stats">
          <div class="metric">
            <span class="sub">Activos Seleccionados</span><b id="selectedCount" style="color:#00db79;">0</b>
          </div>
          <div class="metric">
            <span class="sub">Podados Desactivados</span><b id="prunedOffCount" style="color:#ff453a;">0</b>
          </div>
          <div class="metric"><span class="sub">Catálogo Total</span><b id="totalCount" style="color:#ffd465;">0</b></div>
          <div class="metric"><span class="sub">Aplicación</span><b style="color:#f5f5f2;">Próximo ciclo</b></div>
        </div>"""

inner = re.sub(
    r'<div class="stats">\s*<div class="metric">\s*<span class="sub">Seleccionados \(Activos\)</span>.*?<div class="metric"><span class="sub">Aplicación</span><b>Próximo ciclo</b></div>\s*</div>',
    new_stats_markup,
    inner,
    flags=re.DOTALL
)

# 3. Exact target block for badge rendering in function render(s)
badge_start_marker = "let badge = isPruned"
badge_end_marker = "const selectiveAllowed = Boolean(s.allow_selective_activation ?? true)"

b_start = inner.find(badge_start_marker)
b_end = inner.find(badge_end_marker, b_start)

assert b_start != -1, "Could not find badge_start_marker"
assert b_end != -1, "Could not find badge_end_marker"

new_badge_snippet = """let badge = isPruned
                          ? `<span class="badge pruneBadge" title="${esc(warning)}">⛔ PODADO</span>`
                          : `<span class="badge activeBadge" title="Instrumento operable con ventaja matemática confirmada">✓ ACTIVO</span>`;
                        """

inner = inner[:b_start] + new_badge_snippet + inner[b_end:]
print("Replaced exact badge snippet cleanly")

# 4. Update profBtn text in render(s)
prof_btn_start_marker = "const profBtn = $('selectProfitable');"
prof_btn_end_marker = "$('profileNote').innerHTML ="

p_start = inner.find(prof_btn_start_marker)
p_end = inner.find(prof_btn_end_marker, p_start)

assert p_start != -1, "Could not find prof_btn_start_marker"
assert p_end != -1, "Could not find prof_btn_end_marker"

new_prof_btn_snippet = """const profBtn = $('selectProfitable');
        if (profBtn) {
          profBtn.textContent = '✓ Seleccionar solo ACTIVOS (excluir PODADOS)';
        }
        """

inner = inner[:p_start] + new_prof_btn_snippet + inner[p_end:]
print("Replaced exact profBtn snippet cleanly")

# 5. Update initial button markup in HTML head
inner = re.sub(
    r'<button class="btn"[^>]*id="selectProfitable"[^>]*>.*?<\/button>',
    '<button class="btn" id="selectProfitable" type="button">✓ Seleccionar solo ACTIVOS (excluir PODADOS)</button>',
    inner
)

# 6. Save result to scratch/instruments_new.html
with open('scratch/instruments_new.html', 'w', encoding='utf-8') as out:
    out.write("_INSTRUMENTS_HTML = r'''" + inner)

print("Saved new instruments HTML to scratch/instruments_new.html successfully")
