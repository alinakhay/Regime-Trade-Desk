from regime_trade_desk.domain.enums import Action
from regime_trade_desk.domain.models import Flags
from regime_trade_desk.decision.engine import DecisionEngine
from tests.factories import make_snapshot


class _StubFlagDetector:
    """Lets tests hand the decision engine an exact `Flags` value, instead
    of having to construct a snapshot that would organically produce it."""

    def __init__(self, flags: Flags) -> None:
        self._flags = flags

    def detect(self, snapshot) -> Flags:
        return self._flags


def _decide(flags: Flags, trend: int = 0, momentum: int = 0, macro=None, holding=None):
    engine = DecisionEngine(flag_detector=_StubFlagDetector(flags))
    return engine.decide(make_snapshot(), trend, momentum, macro, holding)


def test_exit_on_exhaustion_beats_bullish_trend_and_momentum():
    decision = _decide(Flags(exhaustion=["a", "b"]), trend=2, momentum=2, holding=True)
    assert decision.action == Action.EXIT_TRIM


def test_exit_on_relentless_bearish_when_holding():
    decision = _decide(Flags(bearish=["a", "b", "c"]), holding=True)
    assert decision.action == Action.EXIT
    assert "Do not average down" in decision.framing


def test_exit_on_relentless_bearish_mentions_active_rebound():
    decision = _decide(Flags(bearish=["a", "b", "c"], rebound=["x", "y"]), holding=True)
    assert decision.action == Action.EXIT
    assert "better price" in decision.framing


def test_re_entry_when_flat_with_rebound_and_no_death_cross():
    decision = _decide(Flags(rebound=["a", "b"], death_cross=False), holding=False)
    assert decision.action == Action.RE_ENTRY


def test_tactical_rebound_when_flat_with_rebound_inside_death_cross():
    decision = _decide(Flags(rebound=["a", "b"], death_cross=True), holding=False)
    assert decision.action == Action.TACTICAL_REBOUND


def test_tactical_rebound_flags_active_bearish_signals():
    decision = _decide(
        Flags(rebound=["a", "b"], bearish=["c", "d"], death_cross=True), holding=False,
    )
    assert decision.action == Action.TACTICAL_REBOUND
    assert "extra tight leash" in decision.framing


def test_stay_out_when_flat_and_relentlessly_bearish():
    decision = _decide(Flags(bearish=["a", "b", "c"]), holding=False)
    assert decision.action == Action.STAY_OUT


def test_hold_ride_cycle_when_holding_with_positive_trend_and_momentum():
    decision = _decide(Flags(), trend=1, momentum=1, holding=True)
    assert decision.action == Action.HOLD_RIDE_CYCLE


def test_wait_when_flat_with_positive_trend_and_momentum():
    decision = _decide(Flags(), trend=2, momentum=1, holding=False)
    assert decision.action == Action.WAIT


def test_hold_under_review_when_holding_with_negative_trend_and_momentum():
    decision = _decide(Flags(), trend=-1, momentum=-2, holding=True)
    assert decision.action == Action.HOLD_UNDER_REVIEW


def test_stay_out_when_flat_with_negative_trend_and_momentum():
    decision = _decide(Flags(), trend=-2, momentum=-1, holding=False)
    assert decision.action == Action.STAY_OUT


def test_fallback_observe_when_holding():
    decision = _decide(Flags(), trend=0, momentum=0, holding=True)
    assert decision.action == Action.HOLD_OBSERVE


def test_fallback_observe_when_flat():
    decision = _decide(Flags(), trend=0, momentum=0, holding=False)
    assert decision.action == Action.OBSERVE


def test_adverse_macro_adjusts_hold_ride_cycle_framing():
    decision = _decide(Flags(), trend=1, momentum=1, macro=-1, holding=True)
    assert "Adverse macro" in decision.framing


def test_neutral_macro_does_not_adjust_framing():
    decision = _decide(Flags(), trend=1, momentum=1, macro=0, holding=True)
    assert "Adverse macro" not in decision.framing


def test_flat_exit_signal_notes_no_position_was_held():
    # Flat + relentless bearish resolves to STAY_OUT, not EXIT, so the
    # "you are flat" note only applies when a rule *does* pick EXIT/EXIT_TRIM
    # while holding=False — which the rule cascade itself never produces.
    # Verified directly against the adjuster instead:
    from regime_trade_desk.decision.adjusters import PositionContextAdjuster
    from regime_trade_desk.decision.context import DecisionContext
    from regime_trade_desk.domain.models import Decision

    ctx = DecisionContext(
        snapshot=make_snapshot(), trend=-2, momentum=-2, macro=None,
        holding=False, flags=Flags(),
    )
    base = Decision(action=Action.EXIT, rationale="r", framing="f", flags=Flags())
    adjusted = PositionContextAdjuster().adjust(base, ctx)
    assert "You are flat" in adjusted.framing
