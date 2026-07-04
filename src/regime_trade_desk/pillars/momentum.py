from __future__ import annotations

from regime_trade_desk.domain.models import IndicatorSnapshot, PillarScore
from regime_trade_desk.pillars.base import Pillar


class MomentumPillar(Pillar):
    """Directional momentum: Wilder RSI-14, MACD histogram sign, and TRIX-15
    vs its signal line. Bollinger %B is deliberately excluded here — it only
    feeds the exhaustion flags in the decision layer, never the numeric score."""

    RSI_UPPER_NEUTRAL = 55
    RSI_LOWER_NEUTRAL = 45

    def score(self, snapshot: IndicatorSnapshot) -> PillarScore:
        points = 0
        bits: list[str] = []

        rsi = snapshot.rsi14
        if rsi is not None:
            if rsi >= self.RSI_UPPER_NEUTRAL:
                points += 1
                bits.append(f"RSI {rsi:.0f}>={self.RSI_UPPER_NEUTRAL}")
            elif rsi <= self.RSI_LOWER_NEUTRAL:
                points -= 1
                bits.append(f"RSI {rsi:.0f}<={self.RSI_LOWER_NEUTRAL}")
            else:
                bits.append(f"RSI {rsi:.0f} neutral")

        if snapshot.macd_hist is not None:
            if snapshot.macd_hist > 0:
                points += 1
                bits.append("MACD hist>0")
            else:
                points -= 1
                bits.append("MACD hist<0")

        trix, trix_signal = snapshot.trix, snapshot.trix_signal
        if trix is not None and trix_signal is not None:
            if trix > trix_signal and trix > 0:
                points += 1
                bits.append("TRIX>signal>0")
            elif trix < trix_signal and trix < 0:
                points -= 1
                bits.append("TRIX<signal<0")
            else:
                bits.append("TRIX mixed")

        score = 2 if points >= 2 else 1 if points == 1 else 0 if points == 0 else -1 if points == -1 else -2
        return PillarScore(score=score, detail=", ".join(bits))
