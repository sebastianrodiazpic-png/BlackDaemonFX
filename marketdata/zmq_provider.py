"""Cliente ZeroMQ para consumo de datos de mercado (ZMQMarketDataProvider).

Permite a los workers de DaemonBlackFx consumir velas históricas y cotizaciones
desde el proceso central `market_data_feeder.py` a través de sockets ZeroMQ locales.

Si el Feeder central no está disponible, realiza un fallback automático e
inmediato al proveedor nativo MT5 (`MT5DataProvider`), garantizando 100% de
resiliencia operativa.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict

import numpy as np
import pandas as pd
import zmq

from brokers.mt5_data import MT5DataProvider

logger = logging.getLogger("marketdata.zmq_provider")

DEFAULT_REP_URL = os.getenv("DAEMON_ZMQ_RPC_URL", "tcp://127.0.0.1:5556")
DEFAULT_PUB_URL = os.getenv("DAEMON_ZMQ_PUB_URL", "tcp://127.0.0.1:5555")


class ZMQMarketDataProvider:
    """Proveedor de datos que consulta el Feeder central vía ZeroMQ REQ/REP."""

    def __init__(
        self,
        fallback_provider: MT5DataProvider | None = None,
        rep_url: str = DEFAULT_REP_URL,
        pub_url: str = DEFAULT_PUB_URL,
        timeout_ms: int = 2000,
    ):
        self.rep_url = rep_url
        self.pub_url = pub_url
        self.timeout_ms = timeout_ms
        self.fallback_provider = fallback_provider or MT5DataProvider()

        self._context = zmq.Context()
        self._req_socket = None
        self._connected = False
        self._local_cache: Dict[str, tuple[float, pd.DataFrame]] = {}
        self._feeder_available = True

    def _get_socket(self) -> zmq.Socket:
        """Crea o reutiliza el socket REQ con timeouts seguros."""
        if self._req_socket is None or self._req_socket.closed:
            self._req_socket = self._context.socket(zmq.REQ)
            self._req_socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
            self._req_socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
            self._req_socket.setsockopt(zmq.LINGER, 0)
            self._req_socket.connect(self.rep_url)
        return self._req_socket

    def _reset_socket(self):
        """Reinicia el socket en caso de timeout."""
        if self._req_socket is not None:
            try:
                self._req_socket.close()
            except Exception:
                pass
            self._req_socket = None

    def _call_rpc(self, request: dict) -> dict | None:
        """Envía una llamada RPC al Feeder central con reconexión limpia si expira."""
        try:
            sock = self._get_socket()
            sock.send_string(json.dumps(request))
            reply_raw = sock.recv_string()
            return json.loads(reply_raw)
        except (zmq.error.Again, zmq.error.ZMQError, Exception) as exc:
            logger.debug("Fallo de comunicación con Feeder ZeroMQ: %s. Usando fallback MT5.", exc)
            self._reset_socket()
            self._feeder_available = False
            return None

    def is_feeder_alive(self) -> bool:
        """Comprueba si el Feeder central responde."""
        res = self._call_rpc({"action": "ping"})
        return res is not None and res.get("status") == "ok"

    def resolve_symbol(self, symbol: str) -> str:
        """Resuelve el nombre exacto del broker a través del feeder o fallback."""
        res = self._call_rpc({"action": "resolve_symbol", "symbol": symbol})
        if res and res.get("status") == "ok":
            return str(res["resolved"])
        return self.fallback_provider.resolve_symbol(symbol)

    def ensure_symbol(self, symbol: str) -> str:
        """Asegura que el símbolo esté disponible en Market Watch."""
        # Se apoya en resolve_symbol y el fallback MT5
        return self.fallback_provider.ensure_symbol(symbol)

    def prepare_symbols(self, symbols: list[str]) -> list[str]:
        return self.fallback_provider.prepare_symbols(symbols)

    def get_symbol_info(self, symbol: str) -> dict:
        """Consulta metadata del símbolo."""
        res = self._call_rpc({"action": "get_symbol_info", "symbol": symbol})
        if res and res.get("status") == "ok":
            return res["data"]
        return self.fallback_provider.get_symbol_info(symbol)

    def get_candles(self, symbol: str, timeframe: str = "M5", count: int = 1000) -> pd.DataFrame:
        """Obtiene velas como DataFrame a través del Feeder ZeroMQ con fallback MT5."""
        res = self._call_rpc({
            "action": "get_candles",
            "symbol": symbol,
            "timeframe": timeframe,
            "count": count,
        })
        if res and res.get("status") == "ok":
            raw_data = res["data"]
            times = pd.to_datetime(raw_data["time"], utc=True)
            df = pd.DataFrame({
                "time": times,
                "open": np.array(raw_data["open"], dtype=float),
                "high": np.array(raw_data["high"], dtype=float),
                "low": np.array(raw_data["low"], dtype=float),
                "close": np.array(raw_data["close"], dtype=float),
                "tick_volume": np.array(raw_data.get("tick_volume", []), dtype=float) if raw_data.get("tick_volume") else np.zeros(len(times)),
            })
            return df

        # Fallback transparente al proveedor MT5 directo
        return self.fallback_provider.get_candles(symbol, timeframe=timeframe, count=count)
