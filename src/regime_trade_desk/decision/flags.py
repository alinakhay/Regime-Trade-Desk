from __future__ import annotations

from regime_trade_desk.domain.models import Flags, IndicatorSnapshot


class FlagDetector:
    """Detects the qualitative signal patterns the decision cascade acts on:
    bullish exhaustion, relentless bearish pressure, and rebound/reversal
    triggers — plus the structural death-cross flag."""

    def detect(self, snapshot: IndicatorSnapshot) -> Flags:
        close = snapshot.close
        ema20, ema50, ema200 = snapshot.ema20, snapshot.ema50, snapshot.ema200
        ema200_slope = snapshot.ema200_slope
        rsi, rsi_prev = snapshot.rsi14, snapshot.rsi14_prev
        hist, hist_prev = snapshot.macd_hist, snapshot.macd_hist_prev
        trix, trix_signal = snapshot.trix, snapshot.trix_signal
        percent_b = snapshot.percent_b
        stretch = (close / ema20 - 1.0) if ema20 else 0.0

        exhaustion = self._exhaustion_flags(rsi, rsi_prev, hist, hist_prev, percent_b, stretch)
        bearish = self._bearish_flags(close, ema50, ema200, ema200_slope, hist, hist_prev, trix, trix_signal, rsi, rsi_prev)
        rebound = self._rebound_flags(snapshot, rsi, rsi_prev, hist, hist_prev, ema20, close, trix, trix_signal)
        death_cross = bool(ema50 and ema200 and ema50 < ema200 and close < ema50)

        return Flags(
            exhaustion=exhaustion, bearish=bearish, rebound=rebound,
            death_cross=death_cross, stretch_pct=round(stretch * 100, 1),
        )

    @staticmethod
    def _exhaustion_flags(rsi, rsi_prev, hist, hist_prev, percent_b, stretch) -> list[str]:
        flags = []
        if rsi is not None and rsi_prev is not None and rsi >= 70 and rsi < rsi_prev:
            flags.append(f"RSI turning from overbought ({rsi_prev:.0f}→{rsi:.0f})")
        if hist is not None and hist_prev is not None and hist > 0 and hist < hist_prev:
            flags.append("MACD histogram shrinking in positive territory")
        if percent_b is not None and percent_b >= 1.0:
            flags.append("price at/above upper Bollinger Band (%B≥1)")
        if stretch >= 0.10:
            flags.append(f"price stretched {stretch * 100:.0f}% above EMA20")
        return flags

    @staticmethod
    def _bearish_flags(close, ema50, ema200, ema200_slope, hist, hist_prev, trix, trix_signal, rsi, rsi_prev) -> list[str]:
        flags = []
        if ema50 and ema200 and ema200_slope is not None and close < ema50 and ema50 < ema200 and ema200_slope < 0:
            flags.append("price<EMA50<EMA200 with EMA200 falling")
        if hist is not None and hist_prev is not None and hist < 0 and hist < hist_prev:
            flags.append("MACD histogram deepening in negative territory")
        if trix is not None and trix_signal is not None and trix < trix_signal and trix < 0:
            flags.append("TRIX<signal below zero")
        if rsi is not None and rsi_prev is not None and rsi < 45 and rsi < rsi_prev:
            flags.append(f"RSI weak and falling ({rsi:.0f})")
        return flags

    @staticmethod
    def _rebound_flags(snapshot, rsi, rsi_prev, hist, hist_prev, ema20, close, trix, trix_signal) -> list[str]:
        flags = []
        if rsi is not None and rsi_prev is not None and rsi_prev < 35 and rsi > rsi_prev:
            flags.append(f"RSI turning from oversold ({rsi_prev:.0f}→{rsi:.0f})")
        if hist is not None and hist_prev is not None and hist > hist_prev and hist_prev < 0:
            flags.append("MACD histogram crossing bullishly")

        # Genuine recovery of EMA20: currently above it, but closed below it
        # within the last 5 bars. Without a recent dip this is just a normal
        # uptrend, not a rebound.
        bars_since_below = snapshot.bars_since_below_ema20
        if (
            ema20 and close > ema20 and snapshot.ema20_slope is not None
            and snapshot.ema20_slope > 0 and bars_since_below is not None
            and 1 <= bars_since_below <= 5
        ):
            plural = "s" if bars_since_below > 1 else ""
            flags.append(f"price reclaims EMA20 (closed below {bars_since_below} bar{plural} ago)")

        # Fresh TRIX cross detected on the crossover bar only, not while it persists.
        trix_prev, signal_prev = snapshot.trix_prev, snapshot.trix_signal_prev
        if (
            trix is not None and trix_signal is not None and trix_prev is not None
            and signal_prev is not None and trix > trix_signal and trix_prev <= signal_prev
            and trix <= 0
        ):
            flags.append("fresh bullish TRIX cross below zero")
        return flags
