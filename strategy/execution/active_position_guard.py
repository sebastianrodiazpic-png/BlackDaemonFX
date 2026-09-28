"""Entry-only broker guard. A stop moved to BE is still an open position."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import os


def _field(record, name):
    return record.get(name) if isinstance(record, dict) else getattr(record, name, None)


def check_active_position_guard(symbol, mt5_positions, mt5_orders):
    unavailable = dict(can_analyze=False, status='BLOCKED_POSITION_STATE_UNAVAILABLE',
        reason='No se pudo confirmar el estado de posiciones y ordenes de MT5',
        diagnostic_tag='POSITION_STATE_UNAVAILABLE', ticket=None, tickets=[])
    if not isinstance(symbol, str) or not symbol or mt5_positions is None or mt5_orders is None:
        return unavailable
    try:
        positions, orders = list(mt5_positions), list(mt5_orders)
        if any(not isinstance(_field(row, 'symbol'), str) for row in positions + orders):
            return unavailable
    except TypeError:
        return unavailable
    for rows, status, tag, message in (
        (positions, 'BLOCKED_ACTIVE_TRADE', 'WAITING_TRADE_RESOLUTION', 'Posicion activa: esperando cierre TP/SL/BE'),
        (orders, 'BLOCKED_PENDING_ORDER', 'WAITING_PENDING_ORDER', 'Orden pendiente: esperando ejecucion o cancelacion')):
        matching = [row for row in rows if _field(row, 'symbol') == symbol]
        if matching:
            tickets = [_field(row, 'ticket') for row in matching]
            return dict(can_analyze=False, status=status, diagnostic_tag=tag,
                reason=f'{message}. Simbolo {symbol}; tickets {tickets}', ticket=tickets[0], tickets=tickets)
    return dict(can_analyze=True, status='CLEAR_TO_ANALYZE', reason=None,
                diagnostic_tag='CLEAR', ticket=None, tickets=[])


def read_active_position_guard(symbol, broker):
    """Never turn a failed broker request into an empty account."""
    try:
        return check_active_position_guard(symbol, broker.get_open_positions(), broker.get_pending_orders())
    except Exception as exc:
        return dict(check_active_position_guard(symbol, None, None), error=str(exc))


@contextmanager
def symbol_cycle_lock(symbol, directory=None):
    """Serialize same-symbol entry cycles across local workers; never lock management."""
    root = Path(directory) if directory else Path(__file__).resolve().parents[2]/'storage/runtime/position_guard'
    root.mkdir(parents=True, exist_ok=True)
    target = root/(sha256(symbol.encode('utf-8')).hexdigest()+'.lock')
    with target.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        acquired = False
        try:
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                pass
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
