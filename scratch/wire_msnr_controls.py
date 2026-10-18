from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root/'dashboard/strategy_bases_page.py'
source = path.read_text(encoding='utf-8')
start = source.index('      <section class="card" id="msnrRuntimeSettings"')
end = source.index('      <!-- KPI METRICS GRID -->', start)
source = source[:start]+'__MSNR_SETTINGS_PANEL__\n\n'+source[end:]
start = source.index('      let msnrSavedD1Veto = null;')
end = source.index('      // Inicialización', start)
source = source[:start]+'__MSNR_SETTINGS_SCRIPT__\n\n'+source[end:]
source = source.replace('from dashboard.page_loading import with_page_loading',
    'from dashboard.page_loading import with_page_loading\nfrom dashboard.msnr_settings_panel import PANEL_HTML, PANEL_JS')
source = source.replace('STRATEGY_BASES_HTML = with_page_loading(_STRATEGY_BASES_BASE)',
    "_STRATEGY_BASES_BASE = _STRATEGY_BASES_BASE.replace('__MSNR_SETTINGS_PANEL__', PANEL_HTML).replace('__MSNR_SETTINGS_SCRIPT__', PANEL_JS)\nSTRATEGY_BASES_HTML = with_page_loading(_STRATEGY_BASES_BASE)")
source = source.replace('msnr-v2.4-dynamic-fractal-distance','msnr-v2.5-configurable-opportunities')
# A running server must load the fresh panel before its page module is reloaded.
source = source.replace('from dashboard.msnr_settings_panel import PANEL_HTML, PANEL_JS',
    'import importlib\nimport dashboard.msnr_settings_panel as _msnr_panel\nimportlib.reload(_msnr_panel)\nPANEL_HTML, PANEL_JS = _msnr_panel.PANEL_HTML, _msnr_panel.PANEL_JS')
path.write_text(source,encoding='utf-8')

path = root/'tests/test_msnr_dynamic_d1_settings.py'
source = path.read_text(encoding='utf-8').replace('msnr-v2.4-dynamic-fractal-distance','msnr-v2.5-configurable-opportunities')
path.write_text(source,encoding='utf-8')
path = root/'tests/test_malaysian_snr_persistent_retest.py'
source = path.read_text(encoding='utf-8').replace('cfg = MalaysianSNRConfig(enable_scenario_1_continuation=True)',
    'cfg = MalaysianSNRConfig(enable_scenario_1_continuation=True, continuation_fresh_only=False)')
path.write_text(source,encoding='utf-8')
