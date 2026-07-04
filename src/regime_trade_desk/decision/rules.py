"""Decision cascade as a Chain of Responsibility: each rule owns one
scenario from the Agentic-style playbook (short-term returns via capital
rotation — enter on rebound, ride, exit on exhaustion, wait for the next
trigger). `DecisionEngine` walks the chain in priority order and stops at
the first rule that matches.

Priority is split by position: a holder sees exit triggers first
(exhaustion, relentless bearish); flat sees fresh entry triggers first, so
a lagging structural bearish flag doesn't overshadow a tactical rebound.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from regime_trade_desk.domain.enums import Action
from regime_trade_desk.domain.models import Decision
from regime_trade_desk.decision.context import DecisionContext


class DecisionRule(ABC):
    @abstractmethod
    def matches(self, ctx: DecisionContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build(self, ctx: DecisionContext) -> Decision:
        raise NotImplementedError


class ExitOnExhaustionRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return ctx.in_position and ctx.exhaustion_count >= 2

    def build(self, ctx: DecisionContext) -> Decision:
        return Decision(
            action=Action.EXIT_TRIM,
            rationale="Bullish momentum EXHAUSTED.",
            framing=(
                "Partial or full exit: buying momentum is dying out. "
                "Rotate capital and flag for re-entry on the next rebound."
            ),
            flags=ctx.flags,
        )


class ExitOnRelentlessBearishRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return ctx.in_position and ctx.is_relentless_bearish

    def build(self, ctx: DecisionContext) -> Decision:
        framing = "Exit: selling pressure is sustained. Do not average down."
        if ctx.rebound_count >= 2:
            framing += (
                " Rebound in progress: use it to exit at a better price, "
                "not to justify holding."
            )
        return Decision(
            action=Action.EXIT,
            rationale="Bearish momentum RELENTLESS.",
            framing=framing,
            flags=ctx.flags,
        )


class ReEntryRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return not ctx.in_position and ctx.rebound_count >= 2 and not ctx.flags.death_cross

    def build(self, ctx: DecisionContext) -> Decision:
        return Decision(
            action=Action.RE_ENTRY,
            rationale="Rebound/reversal with healthy EMA structure: likely start of a new bullish cycle.",
            framing=(
                "Valid entry trigger. Confirm with candle/volume before entering "
                "full size; stop below the rebound pivot."
            ),
            flags=ctx.flags,
        )


class TacticalReboundRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return not ctx.in_position and ctx.rebound_count >= 2 and ctx.flags.death_cross

    def build(self, ctx: DecisionContext) -> Decision:
        framing = (
            "Short-term opportunity against the structure: reduced size, "
            "close target (EMA20/EMA50 or middle band), tight stop, and quick "
            "exit. Do not let it turn into a hold — the underlying trend remains bearish."
        )
        if ctx.bearish_count >= 2:
            framing += " Bearish flags still active: extra tight leash."
        return Decision(
            action=Action.TACTICAL_REBOUND,
            rationale="Rebound signals within a death-cross: tactical trade, NOT a new cycle.",
            framing=framing,
            flags=ctx.flags,
        )


class StayOutOnRelentlessBearishRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return not ctx.in_position and ctx.is_relentless_bearish

    def build(self, ctx: DecisionContext) -> Decision:
        return Decision(
            action=Action.STAY_OUT,
            rationale="Bearish momentum RELENTLESS, no fresh rebound trigger.",
            framing="Out. Watch for capitulation: the trigger would be a fresh RSI/MACD turn.",
            flags=ctx.flags,
        )


class TrendMomentumPositiveRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return ctx.trend >= 1 and ctx.momentum >= 1

    def build(self, ctx: DecisionContext) -> Decision:
        if ctx.in_position:
            return Decision(
                action=Action.HOLD_RIDE_CYCLE,
                rationale="Bullish cycle intact (Trend and Momentum positive).",
                framing=(
                    "Hold and watch for exhaustion: the next expected action is "
                    "EXIT with profit, not adding to position. Accumulating is not the "
                    "default (capital rotation > large position)."
                ),
                flags=ctx.flags,
            )
        return Decision(
            action=Action.WAIT,
            rationale="Healthy trend but no fresh entry trigger.",
            framing=(
                "Entering mid-trend is chasing: poor R/R for the short term. "
                "Wait for pullback to EMA20 and turn, or the next confirmed rebound."
            ),
            flags=ctx.flags,
        )


class TrendMomentumNegativeRule(DecisionRule):
    def matches(self, ctx: DecisionContext) -> bool:
        return ctx.trend <= -1 and ctx.momentum <= -1

    def build(self, ctx: DecisionContext) -> Decision:
        if ctx.in_position:
            return Decision(
                action=Action.HOLD_UNDER_REVIEW,
                rationale="Weak structure and momentum, but no full exit trigger.",
                framing=(
                    "Do not add. Prepare to exit: if more bearish flags appear or the "
                    "current rebound fizzles out, execute EXIT. If a rebound is active, "
                    "it can be used to exit at a better price."
                ),
                flags=ctx.flags,
            )
        return Decision(
            action=Action.STAY_OUT,
            rationale="Negative structure and momentum, no signs of turning.",
            framing="Out. The next trigger here would be a confirmed rebound (tactical trade).",
            flags=ctx.flags,
        )


class ObserveRule(DecisionRule):
    """Fallback: always matches. Must be last in the chain."""

    def matches(self, ctx: DecisionContext) -> bool:
        return True

    def build(self, ctx: DecisionContext) -> Decision:
        return Decision(
            action=Action.HOLD_OBSERVE if ctx.in_position else Action.OBSERVE,
            rationale="Mixed signals; no clear exhaustion or rebound trigger.",
            framing="No action. Watch the next close.",
            flags=ctx.flags,
        )


DEFAULT_RULE_CHAIN: list[DecisionRule] = [
    ExitOnExhaustionRule(),
    ExitOnRelentlessBearishRule(),
    ReEntryRule(),
    TacticalReboundRule(),
    StayOutOnRelentlessBearishRule(),
    TrendMomentumPositiveRule(),
    TrendMomentumNegativeRule(),
    ObserveRule(),
]
