from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from regime_trade_desk.domain.series import ClosePrices, TimeSeries
from regime_trade_desk.indicators.base import Indicator
from regime_trade_desk.indicators.moving_average import EMA


class RSIWilder(Indicator):
    """Relative Strength Index using Wilder's smoothing (not a simple
    moving average of gains/losses)."""

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, prices: ClosePrices) -> TimeSeries:
        close = prices.as_list()
        n = len(close)
        out: list[Optional[float]] = [None] * n
        if n < self.period + 1:
            return TimeSeries(out)

        gains, losses = [], []
        for i in range(1, n):
            change = close[i] - close[i - 1]
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))

        avg_gain = sum(gains[: self.period]) / self.period
        avg_loss = sum(losses[: self.period]) / self.period
        out[self.period] = self._rsi(avg_gain, avg_loss)

        for i in range(self.period + 1, n):
            gain, loss = gains[i - 1], losses[i - 1]
            avg_gain = (avg_gain * (self.period - 1) + gain) / self.period
            avg_loss = (avg_loss * (self.period - 1) + loss) / self.period
            out[i] = self._rsi(avg_gain, avg_loss)
        return TimeSeries(out)

    @staticmethod
    def _rsi(avg_gain: float, avg_loss: float) -> float:
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)


@dataclass(frozen=True)
class MACDResult:
    line: TimeSeries
    signal: TimeSeries
    histogram: TimeSeries


class MACD:
    """Moving Average Convergence/Divergence. Multi-output, so it does not
    implement the single-series `Indicator` interface."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def compute(self, prices: ClosePrices) -> MACDResult:
        n = len(prices)
        ema_fast = EMA(self.fast).compute(prices)
        ema_slow = EMA(self.slow).compute(prices)
        line_values: list[Optional[float]] = [
            (ema_fast[i] - ema_slow[i])
            if (ema_fast[i] is not None and ema_slow[i] is not None)
            else None
            for i in range(n)
        ]
        line = TimeSeries(line_values)

        valid = line.valid_values()
        signal_valid = EMA(self.signal_period).compute_series(valid)
        signal_values: list[Optional[float]] = [None] * n
        first = line.first_valid_index()
        if first is not None:
            for offset in range(len(signal_valid)):
                signal_values[first + offset] = signal_valid[offset]
        signal = TimeSeries(signal_values)

        hist_values = [
            (line[i] - signal[i]) if (line[i] is not None and signal[i] is not None) else None
            for i in range(n)
        ]
        return MACDResult(line=line, signal=signal, histogram=TimeSeries(hist_values))


@dataclass(frozen=True)
class TRIXResult:
    trix: TimeSeries
    signal: TimeSeries


class TRIX:
    """Triple-smoothed EMA rate of change, with its own EMA signal line."""

    def __init__(self, period: int = 15, signal: int = 9) -> None:
        self.period = period
        self.signal_period = signal

    def compute(self, prices: ClosePrices) -> TRIXResult:
        close = prices.as_list()
        n = len(close)

        e1 = EMA(self.period).compute_series(close).valid_values()
        e2 = EMA(self.period).compute_series(e1).valid_values()
        e3 = EMA(self.period).compute_series(e2).valid_values()

        trix_valid: list[float] = []
        for i in range(1, len(e3)):
            prev = e3[i - 1]
            trix_valid.append((e3[i] - prev) / prev * 100.0 if prev != 0 else 0.0)

        signal_valid = EMA(self.signal_period).compute_series(trix_valid).valid_values()

        trix_out: list[Optional[float]] = [None] * n
        for offset, value in enumerate(trix_valid):
            idx = n - len(trix_valid) + offset
            if idx >= 0:
                trix_out[idx] = value

        signal_out: list[Optional[float]] = [None] * n
        for offset, value in enumerate(signal_valid):
            idx = n - len(signal_valid) + offset
            if idx >= 0:
                signal_out[idx] = value

        return TRIXResult(trix=TimeSeries(trix_out), signal=TimeSeries(signal_out))
