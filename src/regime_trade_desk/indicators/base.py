"""Indicator contract. Each indicator is a small, independently testable
object with a single job: turn a `ClosePrices` series into a `TimeSeries`
(or, for compound indicators, a small dataclass of related TimeSeries).

Only the standard library is used anywhere in this package: the numeric
core must run with zero network/runtime dependencies, so an agent's
"calculator" call is always fast and reproducible.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from regime_trade_desk.domain.series import ClosePrices, TimeSeries


class Indicator(ABC):
    """A single-output indicator (EMA, SMA, RSI, ...)."""

    @abstractmethod
    def compute(self, prices: ClosePrices) -> TimeSeries:
        raise NotImplementedError
