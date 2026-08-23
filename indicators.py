"""
Indicadores técnicos con Wilder smoothing y validaciones
"""

import numpy as np

def wilder_rma(data: np.ndarray, period: int) -> np.ndarray:
    """Wilder's RMA (smoothing)"""
    if len(data) == 0:
        return np.array([])
    rma = np.zeros_like(data)
    rma[0] = data[0]
    alpha = 1.0 / period
    for i in range(1, len(data)):
        rma[i] = data[i] * alpha + rma[i-1] * (1 - alpha)
    return rma

def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    """ATR con Wilder smoothing"""
    if len(close) < period + 1:
        return 0.0
    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr_series = wilder_rma(tr, period)
    return float(atr_series[-1]) if len(atr_series) > 0 else 0.0

def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    """ADX correcto con Wilder smoothing"""
    if len(close) < 2 * period:
        return 0.0
    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr_series = wilder_rma(tr, period)
    atr = atr_series[-1]

    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.maximum(0, up_move)
    minus_dm = np.maximum(0, down_move)

    plus_dm_smooth = wilder_rma(plus_dm, period)
    minus_dm_smooth = wilder_rma(minus_dm, period)

    plus_di = 100 * plus_dm_smooth[-1] / atr if atr > 0 else 0
    minus_di = 100 * minus_dm_smooth[-1] / atr if atr > 0 else 0

    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    dx_series = np.full_like(close, dx)
    adx_series = wilder_rma(dx_series, period)
    return float(min(adx_series[-1], 100))

def calculate_ker(close: np.ndarray, period: int = 10) -> float:
    """Kaufman Efficiency Ratio"""
    if len(close) < period + 1:
        return 0.0
    change = abs(close[-1] - close[-period])
    volatility = np.sum(np.abs(np.diff(close[-period-1:])))
    return change / (volatility + 1e-9)

def calculate_ema(close: np.ndarray, period: int) -> float:
    """EMA (último valor)"""
    if len(close) < period:
        return float(close[-1]) if len(close) > 0 else 0.0
    alpha = 2 / (period + 1)
    ema = close[0]
    for price in close[1:]:
        ema = price * alpha + ema * (1 - alpha)
    return float(ema)

def calculate_rsi(close: np.ndarray, period: int = 14) -> float:
    """RSI"""
    if len(close) < period + 1:
        return 50.0
    deltas = np.diff(close)
    gains = np.maximum(0, deltas)
    losses = np.maximum(0, -deltas)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)
