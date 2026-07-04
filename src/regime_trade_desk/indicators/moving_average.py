from __future__ import annotations

from typing import Optional

from regime_trade_desk.domain.series import ClosePrices, TimeSeries
from regime_trade_desk.indicators.base import Indicator


class SMA(Indicator):
    """Simple moving average of the last `period` observations (last value only)."""

    def __init__(self, period: int) -> None:
        self.period = period

    def value(self, values: list[float]) -> Optional[float]:
        if len(values) < self.period:
            return None
        return sum(values[-self.period :]) / self.period

    def compute(self, prices: ClosePrices) -> TimeSeries:
        values = prices.as_list()
        out: list[Optional[float]] = [None] * len(values)
        for i in range(self.period - 1, len(values)):
            out[i] = sum(values[i - self.period + 1 : i + 1]) / self.period
        return TimeSeries(out)


class EMA(Indicator):
    """Exponential moving average, seeded with the SMA of the first `period`
    observations (TradingView / ta-lib `adjust=False` convention)."""

    def __init__(self, period: int) -> None:
        self.period = period

    def compute(self, prices: ClosePrices) -> TimeSeries:
        return self.compute_series(prices.as_list())

    def compute_series(self, values: list[float]) -> TimeSeries:
        n = len(values)
        out: list[Optional[float]] = [None] * n
        if n < self.period:
            return TimeSeries(out)
        k = 2.0 / (self.period + 1)
        seed = sum(values[: self.period]) / self.period
        out[self.period - 1] = seed
        prev = seed
        for i in range(self.period, n):
            prev = values[i] * k + prev * (1 - k)
            out[i] = prev
        return TimeSeries(out)
