with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

badge_css_target = ".activeBadge {"
badge_css_addition = """.msnrBadge { background: rgba(251, 191, 36, 0.12) !important; color: #fbbf24 !important; border-color: rgba(251, 191, 36, 0.4) !important; }
      .ictBadge { background: rgba(56, 189, 248, 0.12) !important; color: #38bdf8 !important; border-color: rgba(56, 189, 248, 0.4) !important; }
      .tpBadge { background: rgba(192, 132, 252, 0.12) !important; color: #c084fc !important; border-color: rgba(192, 132, 252, 0.4) !important; }
      .orbBadge { background: rgba(0, 219, 121, 0.12) !important; color: #00db79 !important; border-color: rgba(0, 219, 121, 0.4) !important; }

      .activeBadge {"""

if ".msnrBadge" not in text:
    text = text.replace(badge_css_target, badge_css_addition, 1)
    with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added .msnrBadge CSS classes back for backwards compatibility.")
else:
    print(".msnrBadge already in text.")
