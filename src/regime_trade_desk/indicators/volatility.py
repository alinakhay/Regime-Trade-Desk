from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Optional

from regime_trade_desk.domain.series import ClosePrices


@dataclass(frozen=True)
class BollingerReading:
    mid: Optional[float]
    upper: Optional[float]
    lower: Optional[float]
    percent_b: Optional[float]


class BollingerBands:
    """20-period, 2-sigma Bollinger Bands using population standard
    deviation (TradingView convention). Only the latest bar is reported:
    this is a supporting exhaustion signal, not a scored series."""

    def __init__(self, period: int = 20, multiplier: float = 2.0) -> None:
        self.period = period
        self.multiplier = multiplier

    def compute(self, prices: ClosePrices) -> BollingerReading:
        if not prices.has_min_length(self.period):
            return BollingerReading(None, None, None, None)
        window = prices.tail(self.period)
        mid = sum(window) / self.period
        sd = pstdev(window)
        upper = mid + self.multiplier * sd
        lower = mid - self.multiplier * sd
        band_range = upper - lower
        percent_b = (prices.latest - lower) / band_range if band_range != 0 else 0.5
        return BollingerReading(mid=mid, upper=upper, lower=lower, percent_b=percent_b)
