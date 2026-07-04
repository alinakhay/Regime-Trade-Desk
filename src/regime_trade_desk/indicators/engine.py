"""Composition root for the indicator stack: EMA 20/50/200, RSI-14 (Wilder),
MACD 12/26/9, TRIX-15 (signal 9), Bollinger 20/2.

An AI agent should never estimate these values by reasoning over raw bars.
The intended flow is: agent fetches closes from a market-data source, hands
them to `IndicatorEngine.compute(...)`, and gets back numbers, not guesses.
"""
from __future__ import annotations

from regime_trade_desk.domain.models import IndicatorSnapshot
from regime_trade_desk.domain.series import ClosePrices
from regime_trade_desk.indicators.moving_average import EMA
from regime_trade_desk.indicators.oscillators import MACD, RSIWilder, TRIX
from regime_trade_desk.indicators.volatility import BollingerBands

MIN_RECOMMENDED_BARS = 210


class IndicatorEngine:
    def __init__(
        self,
        ema_periods: tuple[int, int, int] = (20, 50, 200),
        rsi_period: int = 14,
        macd_periods: tuple[int, int, int] = (12, 26, 9),
        trix_periods: tuple[int, int] = (15, 9),
        bollinger: tuple[int, float] = (20, 2.0),
        slope_lookback: int = 5,
    ) -> None:
        fast, mid, slow = ema_periods
        self._ema_fast = EMA(fast)
        self._ema_mid = EMA(mid)
        self._ema_slow = EMA(slow)
        self._rsi = RSIWilder(rsi_period)
        macd_fast, macd_slow, macd_signal = macd_periods
        self._macd = MACD(macd_fast, macd_slow, macd_signal)
        trix_period, trix_signal = trix_periods
        self._trix = TRIX(trix_period, trix_signal)
        bb_period, bb_mult = bollinger
        self._bollinger = BollingerBands(bb_period, bb_mult)
        self.slope_lookback = slope_lookback

    def compute(self, prices: ClosePrices, slope_lookback: int | None = None) -> IndicatorSnapshot:
        lookback = slope_lookback if slope_lookback is not None else self.slope_lookback
        warning = None
        if not prices.has_min_length(MIN_RECOMMENDED_BARS):
            warning = (
                f"Only {len(prices)} bars; EMA200/some indicators may be "
                f"None. Ideal >={MIN_RECOMMENDED_BARS + 10}."
            )

        ema20 = self._ema_fast.compute(prices)
        ema50 = self._ema_mid.compute(prices)
        ema200 = self._ema_slow.compute(prices)
        rsi = self._rsi.compute(prices)
        macd_result = self._macd.compute(prices)
        trix_result = self._trix.compute(prices)
        bb = self._bollinger.compute(prices)

        bars_since_below_ema20 = ema20.bars_since(
            lambda i, ema_value: prices[i] < ema_value
        )

        return IndicatorSnapshot(
            n_bars=len(prices),
            warning=warning,
            close=prices.latest,
            ema20=ema20.last(),
            ema50=ema50.last(),
            ema200=ema200.last(),
            ema20_slope=ema20.slope(lookback),
            ema50_slope=ema50.slope(lookback),
            ema200_slope=ema200.slope(lookback),
            rsi14=rsi.last(),
            rsi14_prev=rsi.last(1),
            macd_line=macd_result.line.last(),
            macd_signal=macd_result.signal.last(),
            macd_hist=macd_result.histogram.last(),
            macd_hist_prev=macd_result.histogram.last(1),
            trix=trix_result.trix.last(),
            trix_prev=trix_result.trix.last(1),
            trix_signal=trix_result.signal.last(),
            trix_signal_prev=trix_result.signal.last(1),
            bars_since_below_ema20=bars_since_below_ema20,
            bb_mid=bb.mid,
            bb_upper=bb.upper,
            bb_lower=bb.lower,
            percent_b=bb.percent_b,
        )
