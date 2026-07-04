"""Cross-asset Macro-Sentiment scorer. Consumes daily closes for a handful
of ETF proxies (already fetched by the calling agent) plus an injected
10Y-2Y yield spread, and maps the weighted composite onto the -2..+2
Macro-Sentiment pillar used by `AssetScorer`."""
from __future__ import annotations

from regime_trade_desk.domain.enums import Regime
from regime_trade_desk.domain.models import MacroReading
from regime_trade_desk.pillars.macro.components import (
    ComponentContext,
    MacroComponent,
    RatioTrendComponent,
    YieldCurveComponent,
)
from regime_trade_desk.pillars.macro.market_data import MacroMarketData
from regime_trade_desk.pillars.macro.mathutils import clamp, pct_returns, pearson
from regime_trade_desk.pillars.macro.regime import RegimeClassifier


class MacroEngine:
    def __init__(
        self,
        slow: int = 200,
        slope_win: int = 20,
        corr_win: int = 40,
        components: list[MacroComponent] | None = None,
        regime_classifier: RegimeClassifier | None = None,
    ) -> None:
        self.slow = slow
        self.slope_win = slope_win
        self.corr_win = corr_win
        self.components = components or self.default_components()
        self.regime_classifier = regime_classifier or RegimeClassifier()

    @staticmethod
    def default_components() -> list[MacroComponent]:
        return [
            RatioTrendComponent(
                "concentration", "Concentration (equal vs cap-weight)", "RSP/SPY",
                0.25, numerator="RSP", denominator="SPY",
            ),
            YieldCurveComponent("yield_curve", "Yield Curve 10Y-2Y", "10Y-2Y", 0.20),
            RatioTrendComponent(
                "credit", "Credit (high-yield vs IG)", "HYG/LQD",
                0.15, numerator="HYG", denominator="LQD",
            ),
            RatioTrendComponent(
                "size", "Size factor (small vs large)", "IWM/SPY",
                0.15, numerator="IWM", denominator="SPY",
            ),
            RatioTrendComponent(
                "equity_bond", "Equity vs Bond (SPY/TLT)", "SPY/TLT",
                0.15, numerator="SPY", denominator="TLT",
            ),
            RatioTrendComponent(
                "sector", "Sector rotation (cyclical vs defensive)", "XLY/XLP",
                0.10, numerator="XLY", denominator="XLP",
            ),
        ]

    def score(self, market: MacroMarketData) -> MacroReading:
        ctx = ComponentContext(market=market, slow=self.slow, slope_win=self.slope_win)
        notes: list[str] = []
        readings = {}
        for component in self.components:
            reading = component.evaluate(ctx)
            readings[component.key] = reading
            if component.pending_note:
                notes.append(component.pending_note)

        available = [r for r in readings.values() if r.available and r.signal is not None]
        if not available:
            raise ValueError("No macro components with sufficient data. Check input series.")
        weight_sum = sum(r.weight for r in available)
        composite = clamp(sum(r.signal * r.weight for r in available) / weight_sum, -1.0, 1.0)

        equity_bond_corr = self._equity_bond_correlation(market)
        equity_bond = readings["equity_bond"]
        inflationary = bool(
            equity_bond_corr is not None and equity_bond_corr > 0.25
            and equity_bond.available and equity_bond.signal is not None and equity_bond.signal <= 0
        )

        regime = self.regime_classifier.classify(
            composite=composite,
            concentration_signal=readings["concentration"].signal or 0,
            size_signal=readings["size"].signal or 0,
            credit_signal=readings["credit"].signal or 0,
            inflationary=inflationary,
        )

        pillar_score, pillar_label = self._pillar_from_composite(composite)
        if regime in (Regime.CONTRACTION, Regime.INFLATIONARY) and pillar_score > -1:
            pillar_score = -1
            pillar_label = f"Adverse macro (cap due to {regime.value} regime)"
            notes.append(f"Pillar capped at -1 due to {regime.value} regime.")

        return MacroReading(
            as_of=market.as_of,
            composite=round(composite, 3),
            regime=regime,
            pillar_score=pillar_score,
            pillar_label=pillar_label,
            inflationary_flag=inflationary,
            equity_bond_correlation=round(equity_bond_corr, 3) if equity_bond_corr is not None else None,
            components=list(readings.values()),
            notes=notes,
        )

    def _equity_bond_correlation(self, market: MacroMarketData):
        spy, tlt = market.closes("SPY"), market.closes("TLT")
        if not spy or not tlt:
            return None
        window = self.corr_win + 1
        return pearson(pct_returns(spy[-window:]), pct_returns(tlt[-window:]))

    @staticmethod
    def _pillar_from_composite(composite: float) -> tuple[int, str]:
        if composite >= 0.5:
            return 2, "Strongly favorable macro"
        if composite >= 0.2:
            return 1, "Favorable macro"
        if composite > -0.2:
            return 0, "Neutral macro"
        if composite > -0.5:
            return -1, "Adverse macro"
        return -2, "Strongly adverse macro"
