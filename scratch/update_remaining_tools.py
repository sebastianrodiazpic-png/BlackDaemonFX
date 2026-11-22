import os

tools = [
    r"tools\compare_all_assets_strategies.py",
    r"tools\replay_ict_5y_real_markets_audit.py",
    r"tools\replay_ict_60_assets_2year_audit.py",
    r"tools\replay_ict_sabri_malle.py",
    r"tools\shadow_mode_synchronizer.py",
    r"tools\update_strategy_bases_page.py",
    r"tools\update_strategy_bases_tripartite.py",
]

for t in tools:
    if os.path.exists(t):
        with open(t, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = content.replace("ICT Sabri Malle", "ICT")
        new_content = new_content.replace("ict sabri malle", "ict")
        with open(t, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {t}")
