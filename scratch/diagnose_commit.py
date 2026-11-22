import ctypes
from ctypes import wintypes
import sys
import gc

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

def get_mem():
    pmc = PROCESS_MEMORY_COUNTERS_EX()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    h = kernel32.GetCurrentProcess()
    func = ctypes.windll.psapi.GetProcessMemoryInfo
    func.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    func(h, ctypes.byref(pmc), pmc.cb)
    return pmc.WorkingSetSize / 1024 / 1024, pmc.PagefileUsage / 1024 / 1024

print(f"Base Python: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

import numpy
print(f"After numpy: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

import pandas
print(f"After pandas: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

import scipy
print(f"After scipy: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

import MetaTrader5
print(f"After MT5: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

import sklearn
print(f"After sklearn: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
print(f"After LiveTradingEngine import: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")

from app.main import BOT_PROFILES
print(f"After app.main import: WS={get_mem()[0]:.1f}MB, Commit={get_mem()[1]:.1f}MB")
