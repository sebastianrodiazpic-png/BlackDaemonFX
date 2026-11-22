"""Entry-only broker guard. A stop moved to BE is still an open position."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import os
import threading
import time
from strategy.execution.symbol_counterpart import (
    canonical_symbol_root,
    is_counterpart_pair,
    is_same_or_counterpart_symbol,
)

_THREAD_HELD_LOCKS: set[tuple[int, str]] = set()
_THREAD_HELD_MUTEX = threading.Lock()



def _field(record, name):
    return record.get(name) if isinstance(record, dict) else getattr(record, name, None)


def check_active_position_guard(symbol, mt5_positions, mt5_orders, allow_breakeven_positions: bool = False):
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
        matching = [row for row in rows if is_same_or_counterpart_symbol(symbol, _field(row, 'symbol'))]
        if matching:
            # Si allow_breakeven_positions está activo y todas las posiciones tienen SL en o por encima de Break-Even (riesgo cero), permitir análisis
            if allow_breakeven_positions and status == 'BLOCKED_ACTIVE_TRADE':
                all_at_be = True
                for row in matching:
                    pos_type = str(_field(row, 'type') or '').upper()
                    sl = float(_field(row, 'sl') or 0.0)
                    open_price = float(_field(row, 'price_open') or _field(row, 'open_price') or 0.0)
                    if sl <= 0 or open_price <= 0:
                        all_at_be = False
                        break
                    # Para BUY: SL >= open_price. Para SELL: SL <= open_price
                    if (('BUY' in pos_type or pos_type == '0') and sl < open_price) or (('SELL' in pos_type or pos_type == '1') and sl > open_price):
                        all_at_be = False
                        break
                if all_at_be:
                    continue  # Riesgo cero asegurado en BE: se permite nuevo setup
            tickets = [_field(row, 'ticket') for row in matching]
            matched_sym = _field(matching[0], 'symbol')
            if matched_sym != symbol and is_counterpart_pair(symbol, matched_sym):
                reason_str = (
                    f'Posicion activa en contraparte ({matched_sym}): esperando cierre TP/SL/BE. '
                    f'Simbolo candidato {symbol}; tickets {tickets}'
                    if status == 'BLOCKED_ACTIVE_TRADE'
                    else f'Orden pendiente en contraparte ({matched_sym}): esperando ejecucion o cancelacion. '
                    f'Simbolo candidato {symbol}; tickets {tickets}'
                )
                return dict(
                    can_analyze=False,
                    status=status,
                    diagnostic_tag=tag,
                    reason=reason_str,
                    ticket=tickets[0],
                    tickets=tickets,
                    counterpart_symbol=matched_sym,
                )
            return dict(can_analyze=False, status=status, diagnostic_tag=tag,
                reason=f'{message}. Simbolo {symbol}; tickets {tickets}', ticket=tickets[0], tickets=tickets)
    return dict(can_analyze=True, status='CLEAR_TO_ANALYZE', reason=None,
                diagnostic_tag='CLEAR', ticket=None, tickets=[])


def read_active_position_guard(symbol, broker, allow_breakeven_positions: bool = False):
    """Never turn a failed broker request into an empty account."""
    try:
        return check_active_position_guard(symbol, broker.get_open_positions(), broker.get_pending_orders(), allow_breakeven_positions=allow_breakeven_positions)
    except Exception as exc:
        return dict(check_active_position_guard(symbol, None, None), error=str(exc))


@contextmanager
def symbol_cycle_lock(symbol, directory=None):
    """Serialize same-symbol entry cycles across local workers; never lock management."""
    root = Path(directory) if directory else Path(__file__).resolve().parents[2]/'storage/runtime/position_guard'
    root.mkdir(parents=True, exist_ok=True)
    canonical = canonical_symbol_root(symbol) or str(symbol or "")
    target = root/(sha256(canonical.encode('utf-8')).hexdigest()+'.lock')
    thread_key = (threading.get_ident(), str(target.resolve()))
    with _THREAD_HELD_MUTEX:
        same_thread_reentry = thread_key in _THREAD_HELD_LOCKS
    wait_seconds = 0.0 if same_thread_reentry else float(os.getenv("DAEMONBLACKFX_SYMBOL_LOCK_WAIT_SECONDS", "3.5"))
    deadline = time.monotonic() + max(0.0, wait_seconds)
    with target.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        acquired = False
        try:
            while True:
                try:
                    handle.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    with _THREAD_HELD_MUTEX:
                        _THREAD_HELD_LOCKS.add(thread_key)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.05)
            yield acquired
        finally:
            if acquired:
                with _THREAD_HELD_MUTEX:
                    _THREAD_HELD_LOCKS.discard(thread_key)
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


_IN_FLIGHT_CACHE: dict[str, float] = {}
_IN_FLIGHT_MUTEX = threading.Lock()


def is_terminal_in_flight(symbol: str, cooldown_seconds: float | None = None, directory: str | None = None) -> bool:
    """Verifica si existe una orden en vuelo reciente para el símbolo o su contraparte."""
    if not symbol:
        return False
    cooldown = float(os.getenv("DAEMONBLACKFX_IN_FLIGHT_COOLDOWN_SECONDS", "4.0")) if cooldown_seconds is None else float(cooldown_seconds)
    canonical = canonical_symbol_root(symbol) or str(symbol)
    now = time.monotonic()

    with _IN_FLIGHT_MUTEX:
        last_t = _IN_FLIGHT_CACHE.get(canonical, 0.0)
        if (now - last_t) < cooldown:
            return True

    root = Path(directory) if directory else Path(__file__).resolve().parents[2] / 'storage/runtime/terminal_in_flight'
    target = root / (sha256(canonical.encode('utf-8')).hexdigest() + '.flight')
    if target.exists():
        try:
            mtime = target.stat().st_mtime
            if (time.time() - mtime) < cooldown:
                return True
        except OSError:
            pass
    return False


def record_terminal_in_flight(symbol: str, ticket: int | None = None, directory: str | None = None) -> None:
    """Registra una orden en vuelo para serializar MT5 y prevenir duplicados entre workers."""
    if not symbol:
        return
    canonical = canonical_symbol_root(symbol) or str(symbol)
    now_m = time.monotonic()
    with _IN_FLIGHT_MUTEX:
        _IN_FLIGHT_CACHE[canonical] = now_m

    root = Path(directory) if directory else Path(__file__).resolve().parents[2] / 'storage/runtime/terminal_in_flight'
    try:
        root.mkdir(parents=True, exist_ok=True)
        target = root / (sha256(canonical.encode('utf-8')).hexdigest() + '.flight')
        target.write_text(f"{time.time()}:{ticket or 0}", encoding='utf-8')
    except OSError:
        pass


@contextmanager
def terminal_execution_lock(symbol: str | None = None, directory: str | None = None, timeout_seconds: float | None = None):
    """Lock global a nivel terminal MT5: serializa order_send entre procesos y previene carreras.

    Configurable mediante DAEMONBLACKFX_TERMINAL_LOCK_ENABLED y DAEMONBLACKFX_TERMINAL_LOCK_WAIT_SECONDS.
    """
    enabled = os.getenv("DAEMONBLACKFX_TERMINAL_LOCK_ENABLED", "1").strip().lower() not in ("0", "false", "off", "no")
    if not enabled:
        yield True
        return

    root = Path(directory) if directory else Path(__file__).resolve().parents[2] / 'storage/runtime/terminal_execution'
    root.mkdir(parents=True, exist_ok=True)
    target = root / 'mt5_terminal_send.lock'
    thread_key = (threading.get_ident(), str(target.resolve()))
    with _THREAD_HELD_MUTEX:
        same_thread_reentry = thread_key in _THREAD_HELD_LOCKS
    wait_seconds = 0.0 if same_thread_reentry else (
        float(timeout_seconds) if timeout_seconds is not None else float(os.getenv("DAEMONBLACKFX_TERMINAL_LOCK_WAIT_SECONDS", "5.0"))
    )
    deadline = time.monotonic() + max(0.0, wait_seconds)

    with target.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            while True:
                try:
                    handle.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    with _THREAD_HELD_MUTEX:
                        _THREAD_HELD_LOCKS.add(thread_key)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.025)
            yield acquired
        finally:
            if acquired:
                with _THREAD_HELD_MUTEX:
                    _THREAD_HELD_LOCKS.discard(thread_key)
                handle.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass


