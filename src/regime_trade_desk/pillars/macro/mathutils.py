"""Small numeric helpers shared by macro components. No numpy: this keeps
the whole package stdlib-only, so it runs anywhere Python 3.9+ does."""
from __future__ import annotations

from typing import Optional


def sma(series: list[float], window: int) -> Optional[float]:
    if len(series) < window:
        return None
    return sum(series[-window:]) / window


def ratio_series(numerator: list[float], denominator: list[float]) -> list[float]:
    """Element-wise ratio, aligned by the end of both series."""
    n = min(len(numerator), len(denominator))
    numerator, denominator = numerator[-n:], denominator[-n:]
    return [a / b for a, b in zip(numerator, denominator) if b != 0]


def pct_returns(series: list[float]) -> list[float]:
    out = []
    for i in range(1, len(series)):
        if series[i - 1] != 0:
            out.append(series[i] / series[i - 1] - 1.0)
    return out


def pearson(xs: list[float], ys: list[float]) -> Optional[float]:
    n = min(len(xs), len(ys))
    if n < 5:
        return None
    xs, ys = xs[-n:], ys[-n:]
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return covariance / (var_x ** 0.5 * var_y ** 0.5)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def trend_signal(series: list[float], slow: int, slope_win: int) -> tuple[Optional[float], str]:
    """Directional signal in {-1, -0.5, 0, +0.5, +1}:
      base  = position of the last value vs its slow SMA
      trend = slope of the slow SMA over `slope_win`
    """
    slow_sma = sma(series, slow)
    if slow_sma is None or len(series) < slow + slope_win:
        return None, "insufficient data"
    base = 1.0 if series[-1] > slow_sma else -1.0
    slow_sma_then = sma(series[:-slope_win], slow)
    if slow_sma_then is None:
        return None, "insufficient data for slope"
    trend = 1.0 if slow_sma > slow_sma_then else -1.0
    signal = 0.5 * base + 0.5 * trend
    position = "above" if base > 0 else "below"
    slope_word = "rising" if trend > 0 else "falling"
    return signal, f"ratio {position} SMA{slow}, SMA{slow} {slope_word}"
