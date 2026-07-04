from __future__ import annotations

from regime_trade_desk.domain.enums import Regime


class RegimeClassifier:
    """Cascading priority classification of the cross-asset regime, driven
    by the composite score plus a handful of individual component signals."""

    def classify(
        self, composite: float, concentration_signal: float,
        size_signal: float, credit_signal: float, inflationary: bool,
    ) -> Regime:
        if inflationary:
            return Regime.INFLATIONARY
        if composite <= -0.5 and credit_signal < 0:
            return Regime.CONTRACTION
        if composite >= 0.4 and size_signal > 0:
            return Regime.BROADENING
        if concentration_signal < 0 and size_signal < 0 and composite > -0.5:
            return Regime.CONCENTRATION
        return Regime.TRANSITIONAL
