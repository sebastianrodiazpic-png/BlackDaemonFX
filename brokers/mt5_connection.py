"""Compatibilidad temporal.
La implementación oficial del conector vive en brokers.mt5_connector.
"""
from brokers.mt5_connector import MT5Connector

__all__ = ["MT5Connector"]
