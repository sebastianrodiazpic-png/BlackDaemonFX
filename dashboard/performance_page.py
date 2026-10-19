"""Plantilla HTML de la pantalla "Historial y Rendimiento" del dashboard.

Página dedicada para el análisis mensual de rendimiento, rankings de estrategias
por PnL neto y calendario de operaciones completas.
Incluye el banner del Plan de Activación Gradual de Malaysian SNR validado a 2 años.
"""

from dashboard.page_loading import with_page_loading
from dashboard.period_panel import PANEL

MSNR_PLAN_HTML = r'''
<style>
  .msnr-plan-card {
    background: linear-gradient(135deg, rgba(16, 22, 26, 0.95), rgba(10, 14, 16, 0.98));
    border: 1px solid #675321;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 22px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(244, 206, 99, 0.08);
  }
  .msnr-plan-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(103, 83, 33, 0.4);
  }
  .msnr-plan-title {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .msnr-plan-title h2 {
    font-size: 19px;
    margin: 0;
    color: #f4ce63;
    font-weight: 700;
    letter-spacing: 0.02em;
  }
  .msnr-plan-subtitle {
    font-size: 12px;
    color: #9fa2a5;
    margin-top: 4px;
  }
  .msnr-phase-badge {
    background: rgba(0, 219, 121, 0.15);
    border: 1px solid #00db79;
    color: #00db79;
    font-size: 11px;
    font-weight: 800;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .msnr-phase-badge::before {
    content: "●";
    font-size: 12px;
    color: #00db79;
    animation: pulseGlow 1.8s infinite;
  }
  @keyframes pulseGlow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.3); }
  }
  .msnr-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
    margin-bottom: 18px;
  }
  .msnr-kpi-item {
    background: rgba(8, 12, 14, 0.7);
    border: 1px solid #232d32;
    border-radius: 10px;
    padding: 12px 14px;
    transition: border-color 0.2s;
  }
  .msnr-kpi-item:hover {
    border-color: #f4ce63;
  }
  .msnr-kpi-label {
    font-size: 11px;
    color: #8e9da2;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .msnr-kpi-val {
    font-size: 18px;
    font-weight: 800;
    color: #f5f5f2;
    margin-top: 4px;
    display: block;
  }
  .msnr-kpi-val.gold { color: #f4ce63; }
  .msnr-kpi-val.green { color: #34d399; }
  .msnr-kpi-val.red { color: #f87171; }
  .msnr-kpi-sub {
    font-size: 10px;
    color: #64748b;
    margin-top: 2px;
  }
  .msnr-plan-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }
  .msnr-tab-btn {
    background: #141b1f;
    border: 1px solid #2a343a;
    color: #94a3b8;
    padding: 6px 14px;
    border-radius: 7px;
    font-size: 12px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
  }
  .msnr-tab-btn.active, .msnr-tab-btn:hover {
    background: rgba(244, 206, 99, 0.15);
    border-color: #f4ce63;
    color: #f4ce63;
  }
  .msnr-chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    max-height: 220px;
    overflow-y: auto;
    padding-right: 4px;
    margin-bottom: 16px;
  }
  .msnr-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 600;
    background: #10171b;
    border: 1px solid #1f2a30;
    color: #e2e8f0;
  }
  .msnr-chip.lead {
    border-color: rgba(56, 189, 248, 0.4);
    background: rgba(6, 182, 212, 0.08);
  }
  .msnr-chip.gold-lead {
    border-color: rgba(245, 158, 11, 0.4);
    background: rgba(245, 158, 11, 0.08);
  }
  .msnr-chip.green-lead {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.08);
  }
  .msnr-chip.toxic {
    border-color: rgba(248, 113, 113, 0.35);
    background: rgba(248, 113, 113, 0.08);
    color: #fca5a5;
  }
  .msnr-chip small {
    font-size: 10px;
    opacity: 0.8;
  }
  .msnr-actions-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    padding-top: 12px;
    border-top: 1px solid rgba(103, 83, 33, 0.3);
  }
  .msnr-actions-bar a.btn-cta {
    background: #f4ce63;
    color: #0c1113;
    font-weight: 800;
    border: 1px solid #f4ce63;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-size: 12px;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .msnr-actions-bar a.btn-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(244, 206, 99, 0.35);
  }
  .msnr-actions-bar a.btn-link {
    color: #94a3b8;
    text-decoration: none;
    font-size: 12px;
  }
  .msnr-actions-bar a.btn-link:hover {
    color: #f4ce63;
  }
</style>

<section class="msnr-plan-card" id="msnrGradualPlanCard">
  <div class="msnr-plan-header">
    <div class="msnr-plan-title">
      <span style="font-size:24px">🎯</span>
      <div>
        <h2>Plan de Activación Gradual · Malaysian SNR</h2>
        <div class="msnr-plan-subtitle">
          Auditoría causal bar-a-bar de 2 años (Oct 2024 - Oct 2026) · Maximización de volumen seguro con exclusión de activos tóxicos.
        </div>
      </div>
    </div>
    <div class="msnr-phase-badge">Fase 1 Activa · Núcleo de Alta Rentabilidad</div>
  </div>

  <div class="msnr-kpi-grid">
    <div class="msnr-kpi-item">
      <div class="msnr-kpi-label">Activos Operando</div>
      <span class="msnr-kpi-val green">25 Activos</span>
      <div class="msnr-kpi-sub">Step, Jump, Boom, Crash, Macro & Forex</div>
    </div>
    <div class="msnr-kpi-item">
      <div class="msnr-kpi-label">Resultado 2A Auditado</div>
      <span class="msnr-kpi-val gold">+34.820 R</span>
      <div class="msnr-kpi-sub">Retorno total acumulado en backtest causal</div>
    </div>
    <div class="msnr-kpi-item">
      <div class="msnr-kpi-label">Win Rate Promedio</div>
      <span class="msnr-kpi-val green">53.2% WR</span>
      <div class="msnr-kpi-sub">TP1 (2R) + Runner (3R-4R) con BE automático</div>
    </div>
    <div class="msnr-kpi-item">
      <div class="msnr-kpi-label">Poda Activa (Bloqueados)</div>
      <span class="msnr-kpi-val red">19 Tóxicos</span>
      <div class="msnr-kpi-sub">Excluidos por caída libre o expectativa &lt; 0</div>
    </div>
    <div class="msnr-kpi-item">
      <div class="msnr-kpi-label">Gatillo Ejecutado</div>
      <span class="msnr-kpi-val" style="font-size:14px;color:#38bdf8">Directo M15 + Breaker</span>
      <div class="msnr-kpi-sub">Toque a nivel respetado en velas cerradas</div>
    </div>
  </div>

  <div class="msnr-plan-tabs">
    <button type="button" class="msnr-tab-btn active" id="tabActiveAssetsBtn" onclick="toggleMsnrPlanTab('active')">
      ✓ Activos Activos en Operación (25)
    </button>
    <button type="button" class="msnr-tab-btn" id="tabPrunedAssetsBtn" onclick="toggleMsnrPlanTab('pruned')">
      ⚠️ Activos en Poda Preventiva (19 Excluidos)
    </button>
  </div>

  <div id="msnrActiveAssetsBox" class="msnr-chips-container">
    <span class="msnr-chip lead"><b>Jump 25 Index</b> <small>+3.325R · 55.3% WR</small></span>
    <span class="msnr-chip lead"><b>Jump 50 Index</b> <small>+3.240R · 54.6% WR</small></span>
    <span class="msnr-chip gold-lead"><b>Step Index 500</b> <small>+3.168R · 54.6% WR</small></span>
    <span class="msnr-chip lead"><b>Jump 10 Index</b> <small>+3.108R · 53.9% WR</small></span>
    <span class="msnr-chip gold-lead"><b>Step Index 200</b> <small>+3.082R · 53.6% WR</small></span>
    <span class="msnr-chip gold-lead"><b>Step Index 400</b> <small>+3.007R · 54.5% WR</small></span>
    <span class="msnr-chip gold-lead"><b>Step Index</b> <small>+2.982R · 53.0% WR</small></span>
    <span class="msnr-chip green-lead"><b>Boom 1000 Index</b> <small>+1.738R · 51.5% WR</small></span>
    <span class="msnr-chip green-lead"><b>Crash 300 Index</b> <small>+1.715R · 50.8% WR</small></span>
    <span class="msnr-chip green-lead"><b>Boom 600 Index</b> <small>+1.701R · 51.1% WR</small></span>
    <span class="msnr-chip green-lead"><b>Crash 500 Index</b> <small>+1.699R · 50.8% WR</small></span>
    <span class="msnr-chip green-lead"><b>Boom 300 Index</b> <small>+1.697R · 50.8% WR</small></span>
    <span class="msnr-chip green-lead"><b>Crash 600 Index</b> <small>+1.678R · 50.9% WR</small></span>
    <span class="msnr-chip green-lead"><b>Boom 500 Index</b> <small>+1.672R · 51.1% WR</small></span>
    <span class="msnr-chip green-lead"><b>Crash 1000 Index</b> <small>+1.632R · 50.5% WR</small></span>
    <span class="msnr-chip gold-lead"><b>BTCUSD</b> <small>+1.792R · 51.0% WR</small></span>
    <span class="msnr-chip lead"><b>US Tech 100</b> <small>+1.644R · 49.7% WR</small></span>
    <span class="msnr-chip gold-lead"><b>XAUUSD (Oro)</b> <small>+1.617R · 50.2% WR</small></span>
    <span class="msnr-chip lead"><b>Wall Street 30</b> <small>+1.502R · 49.1% WR</small></span>
    <span class="msnr-chip green-lead"><b>USDJPY</b> <small>+1.164R · 54.5% WR</small></span>
    <span class="msnr-chip green-lead"><b>EURUSD</b> <small>+416R · 55.6% WR</small></span>
    <span class="msnr-chip green-lead"><b>GBPUSD</b> <small>+339R · 42.9% WR</small></span>
    <span class="msnr-chip green-lead"><b>GBPJPY</b> <small>+5.16R · 62.5% WR</small></span>
    <span class="msnr-chip green-lead"><b>AUDNZD</b> <small>+5.76R · 50.0% WR</small></span>
    <span class="msnr-chip green-lead"><b>GBPAUD</b> <small>+2.76R · 50.0% WR</small></span>
  </div>

  <div id="msnrPrunedAssetsBox" class="msnr-chips-container" style="display:none">
    <span class="msnr-chip toxic"><b>Volatility 50 Index</b> <small>0.1% WR (-4.637R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 100 Index</b> <small>0.2% WR (-4.635R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 250 (1s) Index</b> <small>6.1% WR (-3.696R)</small></span>
    <span class="msnr-chip toxic"><b>CADCHF</b> <small>5.4% WR (-2.655R)</small></span>
    <span class="msnr-chip toxic"><b>EURGBP</b> <small>5.7% WR (-2.583R)</small></span>
    <span class="msnr-chip toxic"><b>AUDCHF</b> <small>7.9% WR (-2.440R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 75 (1s) Index</b> <small>15.7% WR (-2.409R)</small></span>
    <span class="msnr-chip toxic"><b>EURCHF</b> <small>8.3% WR (-2.357R)</small></span>
    <span class="msnr-chip toxic"><b>US Oil</b> <small>7.4% WR (-2.306R)</small></span>
    <span class="msnr-chip toxic"><b>GBPCHF</b> <small>13.0% WR (-1.941R)</small></span>
    <span class="msnr-chip toxic"><b>AUDCAD</b> <small>15.7% WR (-1.665R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 10 Index</b> <small>28.0% WR (-11.7R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 25 Index</b> <small>27.6% WR (-6.8R)</small></span>
    <span class="msnr-chip toxic"><b>Volatility 75 Index</b> <small>34.1% WR (-4.3R)</small></span>
    <span class="msnr-chip toxic"><b>AUDUSD</b> <small>23.1% WR (-5.14R)</small></span>
    <span class="msnr-chip toxic"><b>USDCAD</b> <small>25.1% WR (-0.21R)</small></span>
    <span class="msnr-chip toxic"><b>USDCHF</b> <small>20.0% WR (-6.66R)</small></span>
    <span class="msnr-chip toxic"><b>EURJPY</b> <small>15.8% WR (-12.2R)</small></span>
    <span class="msnr-chip toxic"><b>EURNZD</b> <small>0.0% WR (-11.1R)</small></span>
  </div>

  <div class="msnr-actions-bar">
    <div>
      <span style="font-size:11px;color:#94a3b8">¿Deseas activar o pausar un activo puntual?</span>
    </div>
    <div style="display:flex;gap:10px;align-items:center">
      <a class="btn-link" href="/strategy-bases">📚 Bases de Estrategias & Backtest 2A ↗</a>
      <a class="btn-cta" href="/instruments">⚙️ Ajustar Selección en /Instruments ↗</a>
    </div>
  </div>
</section>

<script>
  function toggleMsnrPlanTab(tab) {
    const activeBox = document.getElementById('msnrActiveAssetsBox');
    const prunedBox = document.getElementById('msnrPrunedAssetsBox');
    const btnActive = document.getElementById('tabActiveAssetsBtn');
    const btnPruned = document.getElementById('tabPrunedAssetsBtn');
    if (tab === 'active') {
      activeBox.style.display = 'flex';
      prunedBox.style.display = 'none';
      btnActive.classList.add('active');
      btnPruned.classList.remove('active');
    } else {
      activeBox.style.display = 'none';
      prunedBox.style.display = 'flex';
      btnActive.classList.remove('active');
      btnPruned.classList.add('active');
    }
  }
</script>
'''

_PERFORMANCE_BASE = r'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Historial y Rendimiento</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #050708;
        --p: #0a0e10;
        --p2: #10161a;
        --t: #f5f5f2;
        --m: #9fa2a5;
        --l: #5b4514;
        --g: #00db79;
        --r: #ff453a;
        --y: #f5bd36;
        --b: #d79b19;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--t);
        font: 14px system-ui;
      }
      .w {
        max-width: 1380px;
        margin: auto;
        padding: 18px;
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--l);
      }
      .brand img {
        width: 54px;
        height: 54px;
        object-fit: cover;
        border-radius: 10px;
        border: 1px solid #765719;
      }
      .brand strong {
        font-size: 20px;
        letter-spacing: 0.04em;
      }
      .brand strong span {
        color: #f4c84f;
      }
      .top {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: start;
        flex-wrap: wrap;
        margin-bottom: 18px;
      }
      .top h1 {
        margin: 0;
      }
      .muted {
        color: var(--m);
      }
      .nav {
        display: flex;
        gap: 8px;
      }
      .btn {
        color: var(--t);
        background: var(--p2);
        border: 1px solid var(--l);
        padding: 8px 11px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        transition: border-color 0.2s, color 0.2s;
      }
      .btn:hover, .btn.active {
        border-color: #f4ce63;
        color: #f4ce63;
      }
      #periodPerformance {
        margin: 0 !important;
      }
    </style>
  </head>
  <body>
    <main class="w">
      <div class="brand">
        <img src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <strong>BLACKDAEMON<span>FX</span></strong>
          <div class="muted">ESTRATEGIA · DISCIPLINA · RESULTADOS</div>
        </div>
      </div>
      <div class="top">
        <div>
          <h1>Historial y rendimiento</h1>
          <div class="muted">
            La rentabilidad se calcula por setup completo, no por piernas TP individuales · Calendario de Santiago.
          </div>
        </div>
        <div class="nav">
          <a class="btn" href="/">Dashboard</a>
          <a class="btn" href="/account">Cuenta en vivo</a>
          <a class="btn active" href="/performance">Rendimiento</a>
          <a class="btn" href="/instruments">Instrumentos</a>
          <a class="btn" href="/strategy-bases">Bases de Estrategias</a>
        </div>
      </div>
      <!-- MSNR_PLAN_PLACEHOLDER -->
      <!-- PERIOD_PANEL_PLACEHOLDER -->
    </main>
  </body>
</html>
'''

PERFORMANCE_HTML = with_page_loading(
    _PERFORMANCE_BASE.replace("<!-- MSNR_PLAN_PLACEHOLDER -->", MSNR_PLAN_HTML).replace("<!-- PERIOD_PANEL_PLACEHOLDER -->", PANEL)
)


def _hot_sync_realtime_dashboard() -> None:
    """Sincroniza en caliente constantes y plantillas de realtime_dashboard sin reiniciar el runner."""
    try:
        import gc
        import importlib.util
        import sys
        from pathlib import Path

        rt_mod = sys.modules.get("dashboard.realtime_dashboard")
        if rt_mod is None:
            return
        rt_path = Path(__file__).resolve().parent / "realtime_dashboard.py"
        if not rt_path.exists():
            return
        mtime = (rt_path.stat().st_mtime, 2)
        if getattr(rt_mod, "_hot_synced_mtime", None) == mtime:
            return

        spec = importlib.util.spec_from_file_location("_rt_dash_fresh", str(rt_path))
        if spec is None or spec.loader is None:
            return
        fresh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fresh)

        for attr in (
            "DEFAULT_PRIORITIZED_SYMBOLS",
            "PRUNED_INSTRUMENTS_INFO",
            "FOREX_PRUNED_INFO",
            "MALAYSIAN_SNR_PRUNED_INFO",
            "ORB_PRUNED_INFO",
            "ICT_PRUNED_INFO",
            "_SELECTION_PROFILES",
            "_WORKER_PROFILE_META",
            "_CATEGORY_LABELS",
            "_INSTRUMENTS_HTML",
            "_HTML",
            "_selection_profile_for_category",
            "_selection_profile_for_symbol",
            "_catalog_symbols_by_profile",
            "_enrich_worker_state_with_selection",
        ):
            if hasattr(fresh, attr):
                setattr(rt_mod, attr, getattr(fresh, attr))

        old_cls = getattr(rt_mod, "RealtimeDashboardService", None)
        fresh_cls = getattr(fresh, "RealtimeDashboardService", None)
        if old_cls is not None and fresh_cls is not None:
            for method_name in (
                "_cached_instruments_payload",
                "_refresh_selection_profiles_from_db_locked",
                "set_instrument_catalog",
                "update_selected_symbols",
                "snapshot",
            ):
                if hasattr(fresh_cls, method_name):
                    setattr(old_cls, method_name, getattr(fresh_cls, method_name))

            for obj in gc.get_objects():
                try:
                    if isinstance(obj, old_cls):
                        obj._invalidate_navigation_caches(instruments=True)
                        srv = getattr(obj, "_server", None)
                        handler_cls = getattr(srv, "RequestHandlerClass", None)
                        if handler_cls is not None and not getattr(handler_cls, "_case_insensitive_instruments_patched", False):
                            orig_do_get = handler_cls.do_GET

                            def _patched_do_get(self_h, _orig=orig_do_get):
                                if str(getattr(self_h, "path", "")).lower() in ("/instruments", "/instruments/"):
                                    self_h.path = "/instruments"
                                return _orig(self_h)

                            handler_cls.do_GET = _patched_do_get
                            setattr(handler_cls, "_case_insensitive_instruments_patched", True)
                except Exception:
                    pass

        setattr(rt_mod, "_hot_synced_mtime", mtime)
    except Exception:
        pass


_hot_sync_realtime_dashboard()


