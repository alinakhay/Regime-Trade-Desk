from __future__ import annotations

from regime_trade_desk.domain.models import IndicatorSnapshot, PillarScore
from regime_trade_desk.pillars.base import Pillar


class TrendPillar(Pillar):
    """Structural trend: price vs EMA20, EMA20/50/200 stacking order, and
    the long-term slope of EMA200."""

    def score(self, snapshot: IndicatorSnapshot) -> PillarScore:
        points = 0
        bits: list[str] = []

        if snapshot.ema20 is not None:
            if snapshot.close > snapshot.ema20:
                points += 1
                bits.append("price>EMA20")
            else:
                points -= 1
                bits.append("price<EMA20")

        if snapshot.ema20 is not None and snapshot.ema50 is not None:
            if snapshot.ema20 > snapshot.ema50:
                points += 1
                bits.append("EMA20>EMA50")
            else:
                points -= 1
                bits.append("EMA20<EMA50")

        if snapshot.ema50 is not None and snapshot.ema200 is not None:
            if snapshot.ema50 > snapshot.ema200:
                points += 1
                bits.append("EMA50>EMA200")
            else:
                points -= 1
                bits.append("EMA50<EMA200")

        if snapshot.ema200_slope is not None:
            if snapshot.ema200_slope > 0:
                points += 1
                bits.append("EMA200 rising")
            else:
                points -= 1
                bits.append("EMA200 falling")

        score = 2 if points >= 3 else 1 if points >= 1 else 0 if points == 0 else -1 if points >= -2 else -2
        return PillarScore(score=score, detail=", ".join(bits))
