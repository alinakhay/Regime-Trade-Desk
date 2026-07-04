import math

import pytest

from regime_trade_desk.domain.enums import Regime
from regime_trade_desk.pillars.macro.engine import MacroEngine
from regime_trade_desk.pillars.macro.market_data import MacroMarketData
from regime_trade_desk.pillars.macro.regime import RegimeClassifier


def _broadening_series(n: int = 260) -> dict[str, list[float]]:
    def gen(start: float, drift: float, noise_seed: int) -> list[float]:
        out, value = [], start
        for i in range(n):
            value *= 1 + drift + 0.004 * math.sin(i / 9 + noise_seed)
            out.append(round(value, 2))
        return out

    return {
        "SPY": gen(400, 0.0006, 1),
        "RSP": gen(150, 0.0009, 2),
        "IWM": gen(180, 0.0011, 3),
        "HYG": gen(75, 0.0004, 4),
        "LQD": gen(105, 0.0001, 5),
        "TLT": gen(95, -0.0003, 6),
        "XLY": gen(190, 0.0008, 7),
        "XLP": gen(78, 0.0002, 8),
    }


def test_regime_classifier_priority_order():
    rc = RegimeClassifier()
    assert rc.classify(0.1, 0, 0, 0, inflationary=True) == Regime.INFLATIONARY
    assert rc.classify(-0.6, 0, 0, -1, inflationary=False) == Regime.CONTRACTION
    assert rc.classify(0.5, 0, 1, 0, inflationary=False) == Regime.BROADENING
    assert rc.classify(-0.1, -1, -1, 0, inflationary=False) == Regime.CONCENTRATION
    assert rc.classify(0.0, 0, 0, 0, inflationary=False) == Regime.TRANSITIONAL


def test_macro_engine_end_to_end_broadening_regime():
    """Pins the expected composite, regime and pillar score for this
    synthetic broadening dataset, so a future change can't silently alter them."""
    market = MacroMarketData(
        as_of="self-test",
        series=_broadening_series(),
        yield_spread=[round(-0.3 + 0.004 * i, 3) for i in range(60)],
    )
    reading = MacroEngine().score(market)
    assert reading.composite == pytest.approx(0.65)
    assert reading.regime == Regime.BROADENING
    assert reading.pillar_score == 2
    assert reading.inflationary_flag is False


def test_macro_engine_without_yield_spread_redistributes_weight_and_notes():
    market = MacroMarketData(as_of="t", series=_broadening_series(), yield_spread=None)
    reading = MacroEngine().score(market)
    yield_curve = next(c for c in reading.components if c.ratio == "10Y-2Y")
    assert yield_curve.available is False
    assert any("redistributing" in note for note in reading.notes)


def test_inflationary_regime_caps_an_otherwise_favorable_pillar():
    """Exercises the branch `test_contraction_regime_...` explicitly does
    NOT hit: a regime cap that actually changes the outcome. Injects a stub
    classifier so the pillar-capping logic can be verified independent of
    engineering a real inflationary dataset."""

    class _AlwaysInflationary(RegimeClassifier):
        def classify(self, *args, **kwargs) -> Regime:
            return Regime.INFLATIONARY

    market = MacroMarketData(
        as_of="t",
        series=_broadening_series(),
        yield_spread=[round(-0.3 + 0.004 * i, 3) for i in range(60)],
    )
    reading = MacroEngine(regime_classifier=_AlwaysInflationary()).score(market)
    assert reading.regime == Regime.INFLATIONARY
    assert reading.pillar_score == -1
    assert any("capped at -1" in note for note in reading.notes)


def test_macro_engine_raises_when_no_component_has_data():
    market = MacroMarketData(as_of="t", series={}, yield_spread=None)
    with pytest.raises(ValueError):
        MacroEngine().score(market)


def test_contraction_regime_composite_already_implies_strongly_adverse_pillar():
    # Contraction requires composite <= -0.5, which the -2..+2 mapping
    # already grades "Strongly adverse" (-2) on its own. The regime-based
    # cap in `MacroEngine.score` only ever raises a *less* severe pillar
    # (0, 1, 2) up to -1 for a risk-off regime — it is a no-op here, and
    # this test pins that down so a future change can't silently alter it.
    n = 260

    def decline(start: float, drift: float) -> list[float]:
        out, value = [], start
        for _ in range(n):
            value *= 1 + drift
            out.append(round(value, 2))
        return out

    market = MacroMarketData(
        as_of="t",
        series={
            "SPY": decline(400, -0.0005),
            "RSP": decline(150, -0.0006),
            "IWM": decline(180, -0.0008),
            "HYG": decline(75, -0.0007),
            "LQD": decline(105, -0.0001),
            "TLT": decline(95, 0.0002),
            "XLY": decline(190, -0.0006),
            "XLP": decline(78, -0.0002),
        },
        yield_spread=[round(-0.1 - 0.002 * i, 3) for i in range(60)],
    )
    reading = MacroEngine().score(market)
    assert reading.regime == Regime.CONTRACTION
    assert reading.pillar_score == -2
