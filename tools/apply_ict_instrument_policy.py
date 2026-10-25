"""Persiste en /Instruments la política única ICT + MSNR (config/ict_instrument_policy.py) — 20-oct-2026.

Deja las pestañas Sintéticos, Forex, ICT y Malaysian SNR con exactamente los instrumentos activos de la
política y sin ninguna PODA PREVENTIVA marcada. En Malaysian SNR también alinea `asset_modes` de sus ajustes
en base (live = activo, off = PODA PREVENTIVA), igual que el botón "Aplicar selección". Los workers releen la
selección en cada ciclo (no hace falta reiniciar).

Uso:
    .venv/Scripts/python.exe tools/apply_ict_instrument_policy.py            # solo muestra los cambios
    .venv/Scripts/python.exe tools/apply_ict_instrument_policy.py --apply    # guarda (con copia previa)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.ict_instrument_policy import POLICY_SELECTION_PROFILES, ict_active_symbols  # noqa: E402

DEFAULT_DB = Path.home() / "AppData" / "Local" / "BlackDaemonFx" / "trading_bot.sqlite3"


def plan_changes(repo, sources=("DEMO", "LIVE")):
    changes = []
    for source in sources:
        for profile in POLICY_SELECTION_PROFILES:
            current = (repo.latest_instrument_selection_profile(profile, source=source) or {}).get("selected_symbols") or []
            target = list(ict_active_symbols(profile))
            changes.append({
                "source": source,
                "profile": profile,
                "current": list(current),
                "target": target,
                "added": sorted(set(target) - set(current)),
                "removed_preventive_prune": sorted(set(current) - set(target)),
            })
    return changes


def msnr_asset_modes(current_modes, target, current_selection=()):
    """asset_modes de MSNR: live para lo activo y off para lo demás (solo símbolos de su catálogo de ajustes;
    fuera del catálogo MSNR no admite modo y los decide únicamente la selección de /Instruments)."""
    from strategy.malaysian_snr.runtime_settings import CATALOG_SYMBOLS
    catalog = set(CATALOG_SYMBOLS)
    modes = {s: m for s, m in dict(current_modes or {}).items() if s in catalog}
    for sym in target:
        if sym in catalog:
            modes[sym] = "live"
    for sym in (set(modes) | set(current_selection)) & catalog:
        if sym not in set(target):
            modes[sym] = "off"
    return modes


def apply_changes(repo, changes):
    for ch in changes:
        if ch["profile"] == "MALAYSIAN_SNR" and ch["source"] == "DEMO" and hasattr(repo, "save_msnr_runtime_settings"):
            current = repo.latest_msnr_runtime_settings(source="DEMO") or {}
            repo.save_msnr_runtime_settings(
                source="DEMO",
                asset_modes=msnr_asset_modes(current.get("asset_modes"), ch["target"], ch["current"]),
                additional_symbols_mode="off",
                additional_symbols=[],
            )
        repo.save_instrument_selection_profile(ch["target"], selection_profile=ch["profile"], source=ch["source"])
        saved = (repo.latest_instrument_selection_profile(ch["profile"], source=ch["source"]) or {}).get("selected_symbols")
        if sorted(saved or []) != sorted(ch["target"]):
            raise RuntimeError(f"Verificación fallida en {ch['source']}/{ch['profile']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--apply", action="store_true", help="guarda la política (por defecto solo muestra el plan)")
    args = ap.parse_args(argv)

    from database.repository import TradingRepository
    repo = TradingRepository(args.db)
    changes = plan_changes(repo)
    for ch in changes:
        print(f"{ch['source']:<5} {ch['profile']:<10} activos={len(ch['target']):>2}  "
              f"+{ch['added']}  -PODA PREVENTIVA {ch['removed_preventive_prune']}")
    if not args.apply:
        print("\nSolo vista previa. Ejecuta con --apply para guardar.")
        return 0
    backup = ROOT / "storage" / "analysis" / f"instrument_selection_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps(changes, ensure_ascii=False, indent=1), encoding="utf-8")
    apply_changes(repo, changes)
    print(f"\nSelección ICT guardada y verificada. Copia previa: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
