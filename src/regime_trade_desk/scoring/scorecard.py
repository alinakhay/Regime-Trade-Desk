"""Facade that composes the indicator engine, the Trend/Momentum pillars and
the decision engine into the single call an agent needs: hand over closes
(plus an optionally injected Macro-Sentiment score and position status),
get back a full scorecard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from regime_trade_desk.decision.engine import DecisionEngine
from regime_trade_desk.domain.models import Decision, IndicatorSnapshot, PillarScore
from regime_trade_desk.domain.series import ClosePrices
from regime_trade_desk.indicators.engine import IndicatorEngine
from regime_trade_desk.pillars.momentum import MomentumPillar
from regime_trade_desk.pillars.trend import TrendPillar


@dataclass(frozen=True)
class Scorecard:
    symbol: Optional[str]
    n_bars: int
    warning: Optional[str]
    trend: PillarScore
    momentum: PillarScore
    macro_score: Optional[int]
    pillar_total: int
    decision: Decision
    indicators: IndicatorSnapshot

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "n_bars": self.n_bars,
            "warning": self.warning,
            "pillars": {
                "trend": {"score": self.trend.score, "detail": self.trend.detail},
                "momentum": {"score": self.momentum.score, "detail": self.momentum.detail},
                "macro_sentiment": {
                    "score": self.macro_score,
                    "detail": "injected from the Macro-Sentiment engine" if self.macro_score is not None else None,
                },
            },
            "pillar_total": self.pillar_total,
            "decision": self.decision.as_dict(),
            "indicators": self.indicators.as_dict(),
        }


class AssetScorer:
    """Public entry point of the package: `AssetScorer().score(...)`."""

    def __init__(
        self,
        indicator_engine: Optional[IndicatorEngine] = None,
        trend_pillar: Optional[TrendPillar] = None,
        momentum_pillar: Optional[MomentumPillar] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ) -> None:
        self.indicator_engine = indicator_engine or IndicatorEngine()
        self.trend_pillar = trend_pillar or TrendPillar()
        self.momentum_pillar = momentum_pillar or MomentumPillar()
        self.decision_engine = decision_engine or DecisionEngine()

    def score(
        self,
        prices: ClosePrices,
        symbol: Optional[str] = None,
        macro_score: Optional[int] = None,
        holding: Optional[bool] = None,
        slope_lookback: Optional[int] = None,
    ) -> Scorecard:
        snapshot = self.indicator_engine.compute(prices, slope_lookback)
        trend = self.trend_pillar.score(snapshot)
        momentum = self.momentum_pillar.score(snapshot)
        decision = self.decision_engine.decide(
            snapshot, trend.score, momentum.score, macro_score, holding,
        )
        pillar_total = trend.score + momentum.score + (macro_score or 0)
        return Scorecard(
            symbol=symbol,
            n_bars=snapshot.n_bars,
            warning=snapshot.warning,
            trend=trend,
            momentum=momentum,
            macro_score=macro_score,
            pillar_total=pillar_total,
            decision=decision,
            indicators=snapshot,
        )
