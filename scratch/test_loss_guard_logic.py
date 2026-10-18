import os
import sqlite3
from datetime import datetime, timezone, timedelta

db = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db)
c = conn.cursor()

def test_symbol_loss_status(symbol, now_utc=None, cooldown_minutes=60.0, max_daily_losses=2):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    elif now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
        
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    rows = c.execute('''
        SELECT id, instrument, status, result, exit_time, exit_reason, net_pnl
        FROM trades
        WHERE instrument = ? AND status = 'CLOSED'
        ORDER BY id DESC
    ''', (symbol,)).fetchall()
    
    losses = []
    for r in rows:
        _id, inst, status, result, ext_str, exit_reason, pnl = r
        if not ext_str:
            continue
        try:
            ext = datetime.fromisoformat(str(ext_str).replace('Z', '+00:00'))
        except Exception:
            continue
        if ext.tzinfo is None:
            ext = ext.replace(tzinfo=timezone.utc)
        if ext > now_utc:
            continue
        
        is_loss = (float(pnl or 0) < -0.01) or (str(result).upper() == 'LOSS') or ('sl' in str(exit_reason).lower())
        if is_loss:
            losses.append({
                'id': _id,
                'exit_time': ext,
                'exit_reason': exit_reason,
                'net_pnl': float(pnl or 0)
            })
            
    cooldown_active = False
    cooldown_remaining = 0
    cooldown_until = None
    last_loss = losses[0] if losses else None
    
    if last_loss:
        elapsed = (now_utc - last_loss['exit_time']).total_seconds()
        cooldown_sec = cooldown_minutes * 60.0
        if 0 <= elapsed < cooldown_sec:
            cooldown_active = True
            cooldown_remaining = cooldown_sec - elapsed
            cooldown_until = last_loss['exit_time'] + timedelta(minutes=cooldown_minutes)
            
    today_losses = [l for l in losses if l['exit_time'] >= start_of_day]
    daily_count = len(today_losses)
    daily_exceeded = daily_count >= max_daily_losses
    
    return {
        'symbol': symbol,
        'cooldown_active': cooldown_active,
        'cooldown_remaining_min': round(cooldown_remaining / 60.0, 1),
        'cooldown_until': cooldown_until.isoformat() if cooldown_until else None,
        'last_loss_exit_time': last_loss['exit_time'].isoformat() if last_loss else None,
        'last_loss_pnl': last_loss['net_pnl'] if last_loss else None,
        'daily_losses_count': daily_count,
        'daily_strikes_exceeded': daily_exceeded,
        'max_daily_losses': max_daily_losses
    }

print("Simulation at 2026-10-13 21:45 UTC (when trades 863-865 were opened, 18 min after 21:27 SL):")
sim_time = datetime(2026, 10, 13, 21, 45, 0, tzinfo=timezone.utc)
status_sim = test_symbol_loss_status('Step Index 500', now_utc=sim_time)
for k, v in status_sim.items():
    print(f"  {k}: {v}")
