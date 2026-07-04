from __future__ import annotations

from typing import Optional

from regime_trade_desk.domain.models import Decision, IndicatorSnapshot
from regime_trade_desk.decision.adjusters import MacroFramingAdjuster, PositionContextAdjuster
from regime_trade_desk.decision.context import DecisionContext
from regime_trade_desk.decision.flags import FlagDetector
from regime_trade_desk.decision.rules import DEFAULT_RULE_CHAIN, DecisionRule


class DecisionEngine:
    """Ties `FlagDetector`, the rule cascade and the framing adjusters
    together into the single entry point: given a scored snapshot, decide
    what to do and why."""

    def __init__(
        self,
        rules: Optional[list[DecisionRule]] = None,
        flag_detector: Optional[FlagDetector] = None,
        macro_adjuster: Optional[MacroFramingAdjuster] = None,
        position_adjuster: Optional[PositionContextAdjuster] = None,
    ) -> None:
        self.rules = rules or DEFAULT_RULE_CHAIN
        self.flag_detector = flag_detector or FlagDetector()
        self.macro_adjuster = macro_adjuster or MacroFramingAdjuster()
        self.position_adjuster = position_adjuster or PositionContextAdjuster()

    def decide(
        self, snapshot: IndicatorSnapshot, trend: int, momentum: int,
        macro: Optional[int] = None, holding: Optional[bool] = None,
    ) -> Decision:
        flags = self.flag_detector.detect(snapshot)
        ctx = DecisionContext(
            snapshot=snapshot, trend=trend, momentum=momentum,
            macro=macro, holding=holding, flags=flags,
        )
        decision = self._select_rule(ctx).build(ctx)
        decision = self.macro_adjuster.adjust(decision, macro)
        decision = self.position_adjuster.adjust(decision, ctx)
        return decision

    def _select_rule(self, ctx: DecisionContext) -> DecisionRule:
        for rule in self.rules:
            if rule.matches(ctx):
                return rule
        raise RuntimeError("No decision rule matched; the fallback ObserveRule should always match.")
