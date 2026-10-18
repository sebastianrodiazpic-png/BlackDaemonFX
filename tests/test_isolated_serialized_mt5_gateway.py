"""
Suite de Pruebas Unitarias del Gateway Serializado Priorizado para MetaTrader 5
BlackDaemonFx - Entorno de Investigación Aislado (Mocks / Staging)

Verifica:
1. Concurrencia máxima estrictamente igual a 1 (Exclusión Mutua).
2. Prioridad: solicitudes críticas adelantan a peticiones de datos pendientes.
3. Preservación del orden FIFO estricto dentro de la misma prioridad.
4. Expiración (TTL): peticiones vencidas en cola no llegan al conector.
5. No interrupción: solicitudes prioritarias esperan a que la llamada en curso termine limpiamente.
6. Reintentos acotados: los fallos transitorios se reintentan hasta 'max_retries' y se detienen.
7. Resiliencia IPC: una desconexión simulada no cuelga el worker y permite la recuperación.
8. Aislamiento de fallos: un error en una petición no impide procesar las siguientes.
9. Política Anti-Starvation: garantiza atención de datos bajo ráfagas sostenidas de críticos.
10. Apagado limpio y cancelación cooperativa sin fugas ni deadlocks.
11. Análisis concurrente masivo sin concurrencia en MT5.
12. Coherencia de caché en memoria ante solicitudes repetidas.
"""

import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scratch.isolated_serialized_mt5_gateway import (
    MockMT5Connector,
    SerializedMT5Gateway,
    DecoupledAsyncMT5Provider,
    BrokerIPCError,
    MT5BusinessError,
    ExposureRejectionError,
    SimulatedExposureGuard,
    PRIORITY_CRITICAL,
    PRIORITY_DATA,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_connector():
    dates = pd.date_range("2026-10-15 12:00", periods=100, freq="1min", tz="UTC")
    df = pd.DataFrame({
        "time": dates,
        "open": [100.0 + i * 0.1 for i in range(100)],
        "high": [101.0 + i * 0.1 for i in range(100)],
        "low": [99.0 + i * 0.1 for i in range(100)],
        "close": [100.5 + i * 0.1 for i in range(100)],
        "tick_volume": [50] * 100,
    })
    return MockMT5Connector(cached_dfs={"Boom 500 Index": df, "Crash 300 Index": df}, io_delay_sec=0.01)


@pytest.fixture
def gateway(mock_connector):
    gw = SerializedMT5Gateway(mock_connector, max_consecutive_critical=3)
    yield gw
    gw.shutdown(wait=True, timeout=2.0)


@pytest.fixture
def provider(gateway):
    return DecoupledAsyncMT5Provider(gateway, cache_ttl_sec=1.0)


# ---------------------------------------------------------------------------
# 1. Test de Concurrencia Máxima = 1
# ---------------------------------------------------------------------------

def test_max_one_concurrent_mt5_call(gateway, mock_connector):
    """Verifica que bajo ráfaga de 20 hilos concurrentes, NUNCA haya más de 1 llamada activa en MT5."""
    num_requests = 20

    def task():
        fut = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 50)
        return fut.result(timeout=2.0)

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(task) for _ in range(num_requests)]
        results = [f.result() for f in futures]

    assert len(results) == num_requests
    assert mock_connector._max_observed_concurrency == 1
    assert len(mock_connector.call_log) == num_requests


# ---------------------------------------------------------------------------
# 2. Test de Prioridad: Crítico adelanta a Datos pendientes
# ---------------------------------------------------------------------------

def test_critical_request_overtakes_pending_data(gateway, mock_connector):
    """Verifica que una orden crítica adelantará a peticiones de datos que esperan en cola."""
    mock_connector.io_delay_sec = 0.05  # Retardo suficiente para encolar

    # 1. Encolar una llamada inicial lenta para ocupar el worker
    fut_first = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)
    time.sleep(0.01)  # Asegurar que el worker ya tomó la primera llamada

    # 2. Encolar 3 peticiones de datos
    fut_data1 = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)
    fut_data2 = gateway.submit(mock_connector.copy_rates_from_pos, "Crash 300 Index", "M5", 0, 10, priority=PRIORITY_DATA)
    fut_data3 = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)

    # 3. Encolar una orden crítica urgente
    fut_critical = gateway.submit(
        mock_connector.order_send,
        {"symbol": "Crash 300 Index", "action": "SELL", "volume": 0.10},
        priority=PRIORITY_CRITICAL,
    )

    # Esperar que terminen todas
    for f in [fut_first, fut_data1, fut_data2, fut_data3, fut_critical]:
        f.result(timeout=3.0)

    # El registro procesado debe mostrar que la orden crítica (req 5) se procesó ANTES
    # que las peticiones de datos pendientes (req 2, 3, 4), justo después de la req 1 que ya estaba corriendo.
    order_req_id = 5
    first_req_id = 1
    idx_first = gateway.processed_requests_log.index(first_req_id)
    idx_critical = gateway.processed_requests_log.index(order_req_id)

    assert idx_first == 0
    assert idx_critical == 1, f"La orden crítica (req {order_req_id}) no adelantó a los datos: log={gateway.processed_requests_log}"


# ---------------------------------------------------------------------------
# 3. Test de FIFO entre solicitudes de igual prioridad
# ---------------------------------------------------------------------------

def test_fifo_ordering_within_same_priority(gateway, mock_connector):
    """Verifica que peticiones con la misma prioridad respetan rigurosamente el orden FIFO."""
    num_requests = 6
    futures = []
    for _ in range(num_requests):
        fut = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)
        futures.append(fut)

    for f in futures:
        f.result(timeout=2.0)

    expected = list(range(1, num_requests + 1))
    assert gateway.processed_requests_log == expected


# ---------------------------------------------------------------------------
# 4. Test de Expiración (TTL): petición vencida no llega al conector
# ---------------------------------------------------------------------------

def test_expired_request_discarded_before_connector(gateway, mock_connector):
    """Verifica que una petición con TTL corto que vence en cola se descarte sin llamar a MT5."""
    mock_connector.io_delay_sec = 0.08

    # Ocupar el worker con una petición inicial
    fut_blocking = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)

    # Encolar una petición con TTL muy bajo (30 ms) que vencerá mientras corre la primera (80 ms)
    fut_expired = gateway.submit(
        mock_connector.copy_rates_from_pos,
        "Crash 300 Index",
        "M5",
        0,
        10,
        priority=PRIORITY_DATA,
        ttl_seconds=0.03,
    )

    # Encolar una petición normal sin TTL corto
    fut_normal = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)

    # fut_blocking debe tener éxito
    assert isinstance(fut_blocking.result(timeout=1.0), pd.DataFrame)

    # fut_expired debe fallar con TimeoutError y quedar registrada como expirada
    with pytest.raises(TimeoutError, match="expiró tras"):
        fut_expired.result(timeout=1.0)

    # fut_normal debe tener éxito
    assert isinstance(fut_normal.result(timeout=1.0), pd.DataFrame)

    # Verificación estricta: fut_expired (req_id=2) NO llegó al conector MT5
    assert 2 in gateway.expired_requests_log
    called_symbols = [c["symbol"] for c in mock_connector.call_log]
    assert "Crash 300 Index" not in called_symbols


# ---------------------------------------------------------------------------
# 5. Test de No Interrupción de Operación en Curso
# ---------------------------------------------------------------------------

def test_priority_does_not_interrupt_in_flight_operation(gateway, mock_connector):
    """Verifica que si una llamada ya está en ejecución, la orden crítica espera a que concluya."""
    mock_connector.io_delay_sec = 0.06

    t0 = time.perf_counter()
    fut_data = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)
    time.sleep(0.01)

    fut_order = gateway.submit(
        mock_connector.order_send,
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05},
        priority=PRIORITY_CRITICAL,
    )

    res_data = fut_data.result(timeout=1.0)
    res_order = fut_order.result(timeout=1.0)

    elapsed_data = time.perf_counter() - t0
    assert isinstance(res_data, pd.DataFrame)
    assert res_order["retcode"] == 10009
    assert elapsed_data >= 0.05, "La llamada de datos fue interrumpida prematuramente!"
    assert mock_connector._max_observed_concurrency == 1


# ---------------------------------------------------------------------------
# 6. Test de Reintentos Acotados (Bounded Retries)
# ---------------------------------------------------------------------------

def test_bounded_retries_on_ipc_error(gateway, mock_connector):
    """Verifica que los fallos IPC se reintentan hasta max_retries y se detienen sin bucle infinito."""
    # Configurar el conector para fallar las próximas 10 llamadas
    mock_connector.fail_next_n_calls = 10
    gateway.default_max_retries = 2
    gateway.retry_backoff_sec = 0.01

    fut = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)

    with pytest.raises(BrokerIPCError, match="Simulated MT5 IPC Pipe Broken"):
        fut.result(timeout=1.0)

    # Debe haberse reintentado exactamente 2 veces (3 intentos en total)
    assert gateway.retried_requests_count == 3
    assert gateway.failed_requests_count == 1


# ---------------------------------------------------------------------------
# 7. Test de Resiliencia y Recuperación tras Desconexión IPC
# ---------------------------------------------------------------------------

def test_reconnection_and_recovery_after_transient_failure(gateway, mock_connector):
    """Verifica que tras una desconexión transitoria (1 fallo), el conector se reconecta y la petición tiene éxito."""
    mock_connector.fail_next_n_calls = 1  # Falla la primera, pero se reconecta en el reintento
    gateway.default_max_retries = 2
    gateway.retry_backoff_sec = 0.01

    fut = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)
    res = fut.result(timeout=1.0)

    assert isinstance(res, pd.DataFrame)
    assert mock_connector.reconnect_count == 1
    assert gateway.retried_requests_count == 1
    assert gateway.failed_requests_count == 0


# ---------------------------------------------------------------------------
# 8. Test de Aislamiento de Fallos: La Cola Continúa
# ---------------------------------------------------------------------------

def test_failed_request_does_not_block_subsequent_requests(gateway, mock_connector):
    """Verifica que una petición fallida definitiva no impide procesar peticiones posteriores."""
    def fatal_failing_call():
        raise ValueError("Invalid parameters in request")

    fut1 = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)
    fut2 = gateway.submit(fatal_failing_call)
    fut3 = gateway.submit(mock_connector.copy_rates_from_pos, "Crash 300 Index", "M5", 0, 10)

    assert isinstance(fut1.result(timeout=1.0), pd.DataFrame)
    with pytest.raises(ValueError, match="Invalid parameters"):
        fut2.result(timeout=1.0)
    assert isinstance(fut3.result(timeout=1.0), pd.DataFrame)


# ---------------------------------------------------------------------------
# 9. Test de Política Anti-Starvation
# ---------------------------------------------------------------------------

def test_anti_starvation_policy(mock_connector):
    """Verifica que bajo un flujo continuo de peticiones críticas, se atiende una petición de datos cada N críticos."""
    mock_connector.io_delay_sec = 0.02
    gw = SerializedMT5Gateway(mock_connector, max_consecutive_critical=2)

    try:
        # Encolar 1 petición de datos (req 1)
        fut_data = gw.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_DATA)

        # Encolar ráfaga de 5 peticiones críticas (reqs 2..6)
        crit_futs = [
            gw.submit(mock_connector.order_send, {"symbol": "Sym", "i": i}, priority=PRIORITY_CRITICAL)
            for i in range(5)
        ]

        # Esperar todas
        fut_data.result(timeout=2.0)
        for f in crit_futs:
            f.result(timeout=2.0)

        # Como max_consecutive_critical=2:
        # Debería procesar máx 2 críticos antes de atender la de datos.
        # En processed_requests_log, el req_id 1 (datos) debe aparecer a más tardar en la posición 3 (tras máx 2 críticos)
        pos_data = gw.processed_requests_log.index(1)
        assert pos_data <= 2, f"Starvation detectada! Petición de datos atendida en posición {pos_data}: log={gw.processed_requests_log}"
    finally:
        gw.shutdown(wait=True)


# ---------------------------------------------------------------------------
# 10. Test de Cierre Limpio y Cancelación
# ---------------------------------------------------------------------------

def test_clean_shutdown_and_cancellation(mock_connector):
    gw = SerializedMT5Gateway(mock_connector)
    fut_ok = gw.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)
    res = fut_ok.result(timeout=1.0)
    assert isinstance(res, pd.DataFrame)

    gw.shutdown(wait=True, timeout=1.0)
    assert not gw._worker_thread.is_alive()

    fut_after = gw.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)
    with pytest.raises(RuntimeError, match="El Gateway MT5 está apagado"):
        fut_after.result()


# ---------------------------------------------------------------------------
# 11. Test de Análisis Concurrente con MT5 Serializado
# ---------------------------------------------------------------------------

def test_concurrent_analysis_with_serialized_mt5(provider, mock_connector):
    symbols = ["Boom 500 Index", "Crash 300 Index"] * 4

    def analyze_strategy(sym):
        df = provider.get_candles_cached(sym, "M5", count=50)
        highs = df["high"].values
        fractals = sum(1 for i in range(2, len(df)-2) if highs[i] > highs[i-1] and highs[i] > highs[i+1])
        order_res = None
        if fractals >= 0:
            order_res = provider.place_order_priority({
                "symbol": sym, "action": "BUY", "volume": 0.05, "price": highs[-1]
            })
        return {"symbol": sym, "fractals": fractals, "order": order_res}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(analyze_strategy, s) for s in symbols]
        results = [f.result() for f in futures]

    assert len(results) == 8
    assert mock_connector._max_observed_concurrency == 1


# ---------------------------------------------------------------------------
# 12. Test de Coherencia de Caché
# ---------------------------------------------------------------------------

def test_cache_coherence(provider, mock_connector):
    initial_calls = len(mock_connector.call_log)
    df1 = provider.get_candles_cached("Boom 500 Index", "M5", count=50)
    assert len(mock_connector.call_log) == initial_calls + 1

    df2 = provider.get_candles_cached("Boom 500 Index", "M5", count=50)
    assert len(mock_connector.call_log) == initial_calls + 1
    pd.testing.assert_frame_equal(df1, df2)

    df3 = provider.get_candles_cached("Boom 500 Index", "M5", count=50, force_refresh=True)
    assert len(mock_connector.call_log) == initial_calls + 2


# ---------------------------------------------------------------------------
# 13. Test de Clasificación de Errores: Error 10027 (Trade Disabled) No Reintentado
# ---------------------------------------------------------------------------

def test_business_error_10027_trade_disabled_not_retried(gateway, mock_connector):
    """Verifica que un error de negocio como 10027 no dispare reintentos ni reconexiones."""
    gateway.default_max_retries = 3
    gateway.retry_backoff_sec = 0.01

    fut_business = gateway.submit(
        mock_connector.order_send,
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05, "mock_retcode": 10027},
        priority=PRIORITY_CRITICAL,
    )
    fut_next = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)

    res = fut_business.result(timeout=1.0)
    assert res["retcode"] == 10027
    assert mock_connector.reconnect_count == 0, "No debe reconectar ante error de negocio 10027!"
    assert gateway.retried_requests_count == 0, "No debe reintentar error de negocio 10027!"

    # La siguiente petición se procesa normalmente
    res_next = fut_next.result(timeout=1.0)
    assert isinstance(res_next, pd.DataFrame)


# ---------------------------------------------------------------------------
# 14. Test de Clasificación de Errores: Excepción 10018 (Market Closed) No Reintentada
# ---------------------------------------------------------------------------

def test_business_error_10018_market_closed_exception_not_retried(gateway, mock_connector):
    """Verifica que una excepción explícita MT5BusinessError no dispare reconexión ni reintentos."""
    gateway.default_max_retries = 3
    fut_business = gateway.submit(
        mock_connector.order_send,
        {"symbol": "Crash 300 Index", "action": "SELL", "volume": 0.10, "mock_retcode": 10018, "raise_business_error": True},
        priority=PRIORITY_CRITICAL,
    )
    fut_next = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)

    with pytest.raises(MT5BusinessError, match="10018"):
        fut_business.result(timeout=1.0)

    assert mock_connector.reconnect_count == 0
    assert gateway.retried_requests_count == 0

    res_next = fut_next.result(timeout=1.0)
    assert isinstance(res_next, pd.DataFrame)


# ---------------------------------------------------------------------------
# 15. Test de Clasificación de Errores: Error Desconocido se Propaga sin Bloqueo
# ---------------------------------------------------------------------------

def test_unknown_error_propagated_without_retries_and_unblocks_queue(gateway, mock_connector):
    """Verifica que un error inesperado (ej. KeyError) se propague al Future sin reintentar y libere el worker."""
    def broken_call():
        raise KeyError("unexpected_tag_missing")

    fut_bad = gateway.submit(broken_call)
    fut_good = gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10)

    with pytest.raises(KeyError, match="unexpected_tag_missing"):
        fut_bad.result(timeout=1.0)

    assert mock_connector.reconnect_count == 0
    assert gateway.retried_requests_count == 0

    res_good = fut_good.result(timeout=1.0)
    assert isinstance(res_good, pd.DataFrame)


# ---------------------------------------------------------------------------
# 16. Test de Exposición: Órdenes Duplicadas en Misma Dirección Bloqueadas
# ---------------------------------------------------------------------------

def test_exposure_guard_blocks_duplicate_same_direction(gateway, mock_connector):
    """Verifica que dos órdenes simultáneas en la misma dirección para el mismo símbolo sean bloqueadas."""
    mock_connector.io_delay_sec = 0.05
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    # 1. Primera orden en vuelo
    fut1 = ThreadPoolExecutor(max_workers=2).submit(
        guarded_prov.place_order_priority,
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05}
    )
    time.sleep(0.01)  # Asegurar que entra en vuelo

    # 2. Segunda orden idéntica llega mientras la primera está en vuelo
    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority(
            {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05}
        )

    assert "BLOCKED_IN_FLIGHT_ORDER" in str(exc_info.value)
    assert "Orden duplicada BUY en vuelo" in str(exc_info.value)

    res1 = fut1.result(timeout=1.0)
    assert res1["retcode"] == 10009


# ---------------------------------------------------------------------------
# 17. Test de Exposición: Órdenes Opuestas en Conflicto (Hedging) Bloqueadas
# ---------------------------------------------------------------------------

def test_exposure_guard_blocks_conflicting_opposite_direction(gateway, mock_connector):
    """Verifica que una orden opuesta (SELL mientras hay BUY en vuelo) sea bloqueada por conflicto."""
    mock_connector.io_delay_sec = 0.05
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    fut1 = ThreadPoolExecutor(max_workers=2).submit(
        guarded_prov.place_order_priority,
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05}
    )
    time.sleep(0.01)

    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority(
            {"symbol": "Crash 300 Index", "action": "SELL", "volume": 0.05}
        )

    assert "BLOCKED_CONFLICTING_ORDER" in str(exc_info.value)
    assert "Orden opuesta SELL en conflicto" in str(exc_info.value)

    fut1.result(timeout=1.0)


# ---------------------------------------------------------------------------
# 18. Test de Exposición: Activos Distintos Concedidos Concurrentemente
# ---------------------------------------------------------------------------

def test_exposure_guard_allows_concurrent_different_symbols(gateway, mock_connector):
    """Verifica que órdenes concurrentes para símbolos distintos sean ambas permitidas y serializadas en MT5."""
    mock_connector.io_delay_sec = 0.02
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(guarded_prov.place_order_priority, {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})
        f2 = pool.submit(guarded_prov.place_order_priority, {"symbol": "Boom 500 Index", "action": "BUY", "volume": 0.05})
        res1 = f1.result(timeout=1.0)
        res2 = f2.result(timeout=1.0)

    assert res1["retcode"] == 10009
    assert res2["retcode"] == 10009
    assert mock_connector._max_observed_concurrency == 1


# ---------------------------------------------------------------------------
# 19. Test de Exposición: Bloqueo si ya Existe Posición Abierta en Broker
# ---------------------------------------------------------------------------

def test_exposure_guard_blocks_when_position_already_active_in_broker(gateway, mock_connector):
    """Verifica que si ya hay una posición abierta en el broker, se rechace con BLOCKED_ACTIVE_TRADE."""
    mock_connector.add_open_position({"symbol": "Crash 300 Index", "ticket": 777})
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})

    assert "BLOCKED_ACTIVE_TRADE" in str(exc_info.value)
    assert "Posicion activa existente en MT5" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 20. Test de Exposición: Liberación de Reserva tras Fallo de Orden
# ---------------------------------------------------------------------------

def test_exposure_guard_releases_reservation_on_failure(gateway, mock_connector):
    """Verifica que si una orden falla, su reserva en vuelo se libera y no bloquea órdenes posteriores."""
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    # Orden que falla con error de negocio
    with pytest.raises(MT5BusinessError):
        guarded_prov.place_order_priority({
            "symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05,
            "mock_retcode": 10027, "raise_business_error": True
        })

    # La reserva debe haberse liberado, permitiendo un nuevo intento
    res_retry = guarded_prov.place_order_priority({
        "symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05, "mock_retcode": 10009
    })
    assert res_retry["retcode"] == 10009


# ---------------------------------------------------------------------------
# 21. Test de Ciclo de Vida: Operación Aceptada y Completada Exitosamente
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_accepted_and_completed(gateway, mock_connector):
    """Verifica el ciclo de vida completo: reserva en vuelo -> ejecución 10009 -> posición activa en broker -> bloqueo posterior."""
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    res = guarded_prov.place_order_priority({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05, "mock_retcode": 10009})
    assert res["retcode"] == 10009

    # 1. No debe quedar reserva en vuelo
    assert not exposure_guard.is_in_flight("Crash 300 Index")
    assert exposure_guard.get_in_flight_count() == 0

    # 2. Debe figurar como posición activa en MT5
    positions = mock_connector.get_open_positions()
    assert any(p["symbol"] == "Crash 300 Index" for p in positions)

    # 3. Intentos posteriores deben ser bloqueados por posición activa
    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})
    assert "BLOCKED_ACTIVE_TRADE" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 22. Test de Ciclo de Vida: Rechazo Previo sin Entrar a la Cola (Terminal Desconectado)
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_pre_queue_rejection_leaves_clean_state(gateway, mock_connector):
    """Verifica que un rechazo previo (estado no disponible) no contamina la cola ni deja reservas atascadas."""
    mock_connector.is_connected = False
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})

    assert "BLOCKED_POSITION_STATE_UNAVAILABLE" in str(exc_info.value)
    assert exposure_guard.get_in_flight_count() == 0
    assert len(gateway.processed_requests_log) == 0


# ---------------------------------------------------------------------------
# 23. Test de Ciclo de Vida: Timeout Sincrónico Libera la Reserva
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_timeout_releases_reservation(gateway, mock_connector):
    """Verifica que un timeout en la espera sincrónica del cliente libere la reserva y no deje el activo congelado."""
    mock_connector.io_delay_sec = 0.15
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    with pytest.raises(TimeoutError):
        guarded_prov.place_order_priority(
            {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05},
            timeout=0.03,
        )

    time.sleep(0.20)
    assert not exposure_guard.is_in_flight("Crash 300 Index")
    assert exposure_guard.get_in_flight_count() == 0


# ---------------------------------------------------------------------------
# 24. Test de Ciclo de Vida: Cancelación de Orden Libera la Reserva
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_cancellation_releases_reservation(gateway, mock_connector):
    """Verifica que cancelar un Future pendiente libere inmediatamente la reserva en vuelo."""
    mock_connector.io_delay_sec = 0.10
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    # Encolar primero una tarea de datos para mantener ocupado al worker
    gateway.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_CRITICAL)

    # Despachar orden asíncrona
    fut = guarded_prov.place_order_async({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})
    assert exposure_guard.is_in_flight("Crash 300 Index")

    # Cancelar la orden antes de que el worker la tome
    cancelled = fut.cancel()
    assert cancelled is True
    time.sleep(0.02)

    assert not exposure_guard.is_in_flight("Crash 300 Index")
    assert exposure_guard.get_in_flight_count() == 0


# ---------------------------------------------------------------------------
# 25. Test de Ciclo de Vida: Reserva se Mantiene Durante Reintentos Transitorios
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_transient_retry_holds_reservation_until_resolved(gateway, mock_connector):
    """Verifica que durante reintentos por fallo IPC, la reserva siga activa bloqueando solicitudes duplicadas."""
    mock_connector.fail_next_n_calls = 1
    mock_connector.io_delay_sec = 0.03
    gateway.default_max_retries = 2
    gateway.retry_backoff_sec = 0.05

    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    pool = ThreadPoolExecutor(max_workers=2)
    fut1 = pool.submit(
        guarded_prov.place_order_priority,
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05, "mock_retcode": 10009},
        timeout=2.0,
    )
    time.sleep(0.02)

    # Intentar enviar una orden duplicada mientras está reintentando: DEBE SER BLOQUEADA
    with pytest.raises(ExposureRejectionError) as exc_info:
        guarded_prov.place_order_priority(
            {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05},
        )
    assert "BLOCKED_IN_FLIGHT_ORDER" in str(exc_info.value)

    res1 = fut1.result(timeout=2.0)
    assert res1["retcode"] == 10009
    assert mock_connector.reconnect_count == 1
    assert not exposure_guard.is_in_flight("Crash 300 Index")
    pool.shutdown(wait=False)


# ---------------------------------------------------------------------------
# 26. Test de Ciclo de Vida: Agotamiento de Reintentos Libera la Reserva
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_exhausted_retries_releases_reservation(gateway, mock_connector):
    """Verifica que si los reintentos transitorios se agotan, la reserva se libere y el símbolo no quede bloqueado."""
    mock_connector.fail_next_n_calls = 5
    gateway.default_max_retries = 2
    gateway.retry_backoff_sec = 0.01

    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gateway, exposure_guard=exposure_guard)

    with pytest.raises(BrokerIPCError):
        guarded_prov.place_order_priority(
            {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05},
            timeout=2.0,
        )

    assert not exposure_guard.is_in_flight("Crash 300 Index")
    assert exposure_guard.get_in_flight_count() == 0

    mock_connector.fail_next_n_calls = 0
    mock_connector.is_connected = True
    res_retry = guarded_prov.place_order_priority(
        {"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05, "mock_retcode": 10009},
        timeout=2.0,
    )
    assert res_retry["retcode"] == 10009


# ---------------------------------------------------------------------------
# 27. Test de Ciclo de Vida: Apagado Limpio (Shutdown) Cancela y Libera Reservas
# ---------------------------------------------------------------------------

def test_exposure_lifecycle_gateway_shutdown_cleans_reservations(mock_connector):
    """Verifica que un shutdown del gateway con órdenes en cola cancele los futures y libere las reservas."""
    mock_connector.io_delay_sec = 0.10
    gw = SerializedMT5Gateway(mock_connector)
    exposure_guard = SimulatedExposureGuard(mock_connector)
    guarded_prov = DecoupledAsyncMT5Provider(gw, exposure_guard=exposure_guard)

    gw.submit(mock_connector.copy_rates_from_pos, "Boom 500 Index", "M5", 0, 10, priority=PRIORITY_CRITICAL)

    fut = guarded_prov.place_order_async({"symbol": "Crash 300 Index", "action": "BUY", "volume": 0.05})
    assert exposure_guard.is_in_flight("Crash 300 Index")

    gw.shutdown(wait=True, timeout=1.0, cancel_pending=True)
    time.sleep(0.05)

    assert fut.cancelled() is True
    assert not exposure_guard.is_in_flight("Crash 300 Index")
    assert exposure_guard.get_in_flight_count() == 0


# ---------------------------------------------------------------------------
# 28. Test de Clasificación de Errores: Retcode Transitorio 10031 se Reintenta
# ---------------------------------------------------------------------------

def test_error_classification_transient_retcode_10031_retried_and_recovers(gateway, mock_connector):
    """Verifica que el retcode 10031 (TRADE_RETCODE_CONNECTION) se trate como transitorio con reintento y reconexión."""
    gateway.default_max_retries = 2
    gateway.retry_backoff_sec = 0.01

    call_count = 0
    def mock_order_call(req):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"retcode": 10031, "comment": "No connection to trade server"}
        return {"retcode": 10009, "comment": "Done"}

    fut = gateway.submit(mock_order_call, {"symbol": "Crash 300 Index"}, priority=PRIORITY_CRITICAL)
    res = fut.result(timeout=1.0)

    assert res["retcode"] == 10009
    assert call_count == 2
    assert gateway.retried_requests_count == 1
    assert mock_connector.reconnect_count == 1

