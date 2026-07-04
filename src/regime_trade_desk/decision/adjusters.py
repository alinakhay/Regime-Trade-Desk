"""Post-cascade framing adjustments. These never change the chosen action —
only the human-readable framing text — so they are kept as separate,
independently testable decorator-style steps rather than folded into the
rule cascade itself."""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from regime_trade_desk.domain.enums import Action
from regime_trade_desk.domain.models import Decision
from regime_trade_desk.decision.context import DecisionContext

_ADVERSE_MACRO_NOTES = {
    Action.HOLD_RIDE_CYCLE: " ⚠ Adverse macro: lower the exit threshold (take profit earlier).",
    Action.TACTICAL_REBOUND: " ⚠ Adverse macro: reduce size further or skip this rebound.",
    Action.RE_ENTRY: " ⚠ Adverse macro: entry in reduced size.",
}


class MacroFramingAdjuster:
    """Adverse macro (score <= -1) tightens the framing for actions that
    add or hold exposure. Pillar scores themselves are never touched."""

    def adjust(self, decision: Decision, macro: Optional[int]) -> Decision:
        if macro is None or macro > -1:
            return decision
        note = _ADVERSE_MACRO_NOTES.get(decision.action)
        if note is None:
            return decision
        return replace(decision, framing=decision.framing + note)


class PositionContextAdjuster:
    """Appends context tied to whether the account actually holds a
    position, independent of which rule produced the decision."""

    def adjust(self, decision: Decision, ctx: DecisionContext) -> Decision:
        framing = decision.framing
        if ctx.in_position and ctx.rebound_count >= 2 and decision.action.value.startswith("HOLD"):
            framing += " (Rebound signals in progress reinforce holding.)"
        if ctx.holding is False and decision.action in (Action.EXIT_TRIM, Action.EXIT):
            framing += " (You are flat: the exit signal only confirms not entering long.)"
        if framing == decision.framing:
            return decision
        return replace(decision, framing=framing)
