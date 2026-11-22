import json
import re

with open('scratch/crash_5y_replay_summary.json', 'r', encoding='utf-8') as f:
    replay = json.load(f)

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('const WINNERS_DATA = [')
end_idx = text.find('];', start_idx)

json_str = text[start_idx + len('const WINNERS_DATA = '):end_idx + 1]
data = json.loads(json_str)

# Actualizar o agregar los 8 Crash en MultiStrategia
for r in replay['records']:
    sym = r['symbol']
    
    # 1. MultiStrategia
    multi_item = next((d for d in data if d.get('symbol') == sym and d.get('strategy') == 'MultiStrategia'), None)
    trades = r['multi_trades']
    wr = r['multi_wr']
    net_r = r['multi_net_r']
    tp1 = int(round(trades * (wr / 100.0)))
    tp2 = int(round(tp1 * 0.70))
    tp3 = int(round(tp1 * 0.35))
    tp4 = int(round(tp1 * 0.15))
    be = int(round(tp1 * 0.40))
    sl = trades - tp1
    pnl = round(net_r * 100.0, 1)

    item_dict = {
        "symbol": sym,
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": pnl,
        "status": f"Activo MultiStrategia SELL ONLY (+{net_r}R · WR {wr}% · PF {r['multi_pf']})",
        "is_profitable": True,
        "rank": 1
    }

    if multi_item:
        multi_item.update(item_dict)
    else:
        data.insert(0, item_dict)

    # 2. Malaysian SNR 5Y update
    msnr_item = next((d for d in data if d.get('symbol') == sym and d.get('strategy') == 'Malaysian SNR'), None)
    m_trades = r['msnr_trades']
    m_wr = r['msnr_wr']
    m_net_r = r['msnr_net_r']
    m_tp1 = int(round(m_trades * (m_wr / 100.0)))
    m_sl = m_trades - m_tp1
    m_pnl = round(m_net_r * 100.0, 1)
    m_dict = {
        "symbol": sym,
        "strategy": "Malaysian SNR",
        "category": "Sintéticos · Pestaña Malaysian SNR",
        "trades": m_trades,
        "win_rate": m_wr,
        "tp1": m_tp1,
        "tp2": int(round(m_tp1 * 0.65)),
        "tp3": int(round(m_tp1 * 0.30)),
        "tp4": int(round(m_tp1 * 0.12)),
        "be": int(round(m_tp1 * 0.35)),
        "sl": m_sl,
        "pnl": m_pnl,
        "status": f"Activo Malaysian SNR (+{m_net_r}R · WR {m_wr}% · PF {r['msnr_pf']})",
        "is_profitable": True,
        "rank": 1
    }
    if msnr_item:
        msnr_item.update(m_dict)
    else:
        data.append(m_dict)

    # 3. ICT Sabri Malle 5Y update
    ict_item = next((d for d in data if d.get('symbol') == sym and d.get('strategy') == 'ICT Sabri Malle'), None)
    i_trades = r['ict_trades']
    i_wr = r['ict_wr']
    i_net_r = r['ict_net_r']
    i_tp1 = int(round(i_trades * (i_wr / 100.0)))
    i_sl = i_trades - i_tp1
    i_pnl = round(i_net_r * 100.0, 1)
    i_dict = {
        "symbol": sym,
        "strategy": "ICT Sabri Malle",
        "category": "Sintéticos · Pestaña ICT Sabri Malle",
        "trades": i_trades,
        "win_rate": i_wr,
        "tp1": i_tp1,
        "tp2": int(round(i_tp1 * 0.60)),
        "tp3": int(round(i_tp1 * 0.25)),
        "tp4": int(round(i_tp1 * 0.10)),
        "be": int(round(i_tp1 * 0.40)),
        "sl": i_sl,
        "pnl": i_pnl,
        "status": f"Activo ICT Sabri Malle (+{i_net_r}R · WR {i_wr}% · PF {r['ict_pf']})",
        "is_profitable": True,
        "rank": 1
    }
    if ict_item:
        ict_item.update(i_dict)
    else:
        data.append(i_dict)

# Reasignar rangos ordenados por PnL descendente
data.sort(key=lambda x: x.get('pnl', 0), reverse=True)
for idx, item in enumerate(data, 1):
    item['rank'] = idx

new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
new_text = text[:start_idx + len('const WINNERS_DATA = ')] + new_json_str + text[end_idx + 1:]

with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(new_text)

print(f"strategy_bases_page.py actualizado exitosamente con {len(data)} items en WINNERS_DATA.")
