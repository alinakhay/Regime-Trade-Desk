"""Each macro component looks at one cross-asset ratio (or the injected
yield curve) and produces a -1..+1 risk-on/risk-off signal. Sign convention
is fixed across every component: +1 = risk-on / broadening, -1 = risk-off /
concentration or contraction. `MacroEngine` weights and combines them."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from regime_trade_desk.domain.models import MacroComponentReading
from regime_trade_desk.pillars.macro.market_data import MacroMarketData
from regime_trade_desk.pillars.macro.mathutils import ratio_series, trend_signal


@dataclass(frozen=True)
class ComponentContext:
    market: MacroMarketData
    slow: int
    slope_win: int


class MacroComponent(ABC):
    key: str
    name: str
    ratio_label: str
    weight: float

    def __init__(self, key: str, name: str, ratio_label: str, weight: float) -> None:
        self.key = key
        self.name = name
        self.ratio_label = ratio_label
        self.weight = weight
        self.pending_note: Optional[str] = None

    @abstractmethod
    def evaluate(self, ctx: ComponentContext) -> MacroComponentReading:
        raise NotImplementedError

    def _reading(self, signal: Optional[float], detail: str) -> MacroComponentReading:
        return MacroComponentReading(
            name=self.name,
            ratio=self.ratio_label,
            weight=self.weight,
            signal=signal,
            detail=detail,
            available=signal is not None,
        )


class RatioTrendComponent(MacroComponent):
    """Generic cross-asset ratio component: numerator/denominator closes are
    reduced to a ratio series and scored via `trend_signal`. Covers
    Concentration, Credit, Size, Equity-vs-Bond and Sector Rotation."""

    def __init__(
        self, key: str, name: str, ratio_label: str, weight: float,
        numerator: str, denominator: str,
    ) -> None:
        super().__init__(key, name, ratio_label, weight)
        self.numerator = numerator
        self.denominator = denominator

    def evaluate(self, ctx: ComponentContext) -> MacroComponentReading:
        num = ctx.market.closes(self.numerator)
        den = ctx.market.closes(self.denominator)
        if not num or not den:
            return self._reading(None, "insufficient data")
        signal, detail = trend_signal(ratio_series(num, den), ctx.slow, ctx.slope_win)
        return self._reading(signal, detail)


class YieldCurveComponent(MacroComponent):
    """10Y-2Y treasury spread. Not proxied by ETFs (a fragile approximation);
    the caller injects the actual spread series (or a single latest value)
    from whatever external source they trust."""

    def __init__(self, key: str, name: str, ratio_label: str, weight: float) -> None:
        super().__init__(key, name, ratio_label, weight)

    def evaluate(self, ctx: ComponentContext) -> MacroComponentReading:
        spread = ctx.market.yield_spread
        if not spread:
            self.pending_note = (
                f"No yield_spread: redistributing the {self.weight:.0%} weight "
                "of the curve among other components."
            )
            return self._reading(None, "insufficient data")

        if len(spread) >= ctx.slope_win + 1:
            now, then = spread[-1], spread[-1 - ctx.slope_win]
            base = 1.0 if now > 0 else -1.0
            trend = 1.0 if now > then else -1.0
            signal = 0.5 * base + 0.5 * trend
            sign = "+" if now >= 0 else ""
            trend_word = "steepening" if trend > 0 else "flattening"
            detail = f"spread {sign}{now:.2f}, {trend_word}"
            return self._reading(signal, detail)

        # Typical session case: only the current value is available.
        # Medium-intensity level-only signal, no slope component.
        now = spread[-1]
        signal = 0.5 if now > 0 else -0.5
        sign = "+" if now >= 0 else ""
        self.pending_note = (
            "yield_spread with <21 observations: using level only (+/-0.5), no slope."
        )
        return self._reading(signal, f"spread {sign}{now:.2f} (level only; no series for slope)")
