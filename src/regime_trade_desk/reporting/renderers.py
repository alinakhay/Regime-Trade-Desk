"""Output formatting is a pure presentation concern, kept fully separate
from scoring: swapping `TextRenderer` for `JSONRenderer` (or adding a new
one) never touches the numeric core."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

from regime_trade_desk.domain.models import MacroReading
from regime_trade_desk.scoring.scorecard import Scorecard


class ScorecardRenderer(ABC):
    @abstractmethod
    def render(self, scorecard: Scorecard) -> str:
        raise NotImplementedError


class TextRenderer(ScorecardRenderer):
    def render(self, scorecard: Scorecard) -> str:
        lines = []
        lines.append("═" * 54)
        lines.append(f" {scorecard.symbol or 'SYMBOL'}   ·   {scorecard.n_bars} bars")
        lines.append("═" * 54)
        lines.append(self._pillar_line("Trend", scorecard.trend.score, scorecard.trend.detail))
        lines.append(self._pillar_line("Momentum", scorecard.momentum.score, scorecard.momentum.detail))
        macro_detail = "injected from the Macro-Sentiment engine" if scorecard.macro_score is not None else "(not injected)"
        lines.append(self._pillar_line("Macro-Sentiment", scorecard.macro_score, macro_detail))
        lines.append(f"  {'─' * 50}")
        lines.append(f"  TOTAL (-6..+6): {scorecard.pillar_total:+d}")
        lines.append("─" * 54)

        decision = scorecard.decision
        lines.append(f"  ► {decision.action.value}  —  {decision.rationale}")
        lines.append(f"    {decision.framing}")
        flags = decision.flags
        if flags.exhaustion:
            lines.append(f"    exhaustion: {'; '.join(flags.exhaustion)}")
        if flags.bearish:
            lines.append(f"    bearish: {'; '.join(flags.bearish)}")
        if flags.rebound:
            lines.append(f"    rebound: {'; '.join(flags.rebound)}")
        if flags.death_cross:
            lines.append("    structure: active death-cross (EMA50<EMA200, price<EMA50)")
        if scorecard.warning:
            lines.append(f"    ⚠ {scorecard.warning}")
        return "\n".join(lines)

    @staticmethod
    def _pillar_line(name: str, score, detail: str) -> str:
        rendered_score = f"{score:+d}" if score is not None else " ?"
        return f"  {name:<16} {rendered_score:>3}   {detail}"


class JSONRenderer(ScorecardRenderer):
    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def render(self, scorecard: Scorecard) -> str:
        return json.dumps(scorecard.as_dict(), indent=self.indent, ensure_ascii=False)


class MacroTextRenderer:
    def render(self, reading: MacroReading) -> str:
        lines = []
        lines.append(f"MACRO-SENTIMENT  ·  {reading.as_of or 'n/a'}")
        lines.append("=" * 52)
        lines.append(f"Regime         : {reading.regime.value}")
        lines.append(f"Composite      : {reading.composite:+.3f}  (scale -1..+1)")
        lines.append(f"PILLAR (-2..+2): {reading.pillar_score:+d}  · {reading.pillar_label}")
        if reading.equity_bond_correlation is not None:
            flag = "  ⚠ inflationary flag" if reading.inflationary_flag else ""
            lines.append(f"Equity/Bond Corr: {reading.equity_bond_correlation:+.3f}{flag}")
        lines.append("-" * 52)
        lines.append("Components:")
        for component in reading.components:
            if component.available and component.signal is not None:
                arrow = "▲" if component.signal > 0 else ("▼" if component.signal < 0 else "─")
                lines.append(
                    f"  {arrow} {component.ratio:<9} w={component.weight:.2f}  "
                    f"sig={component.signal:+.2f}  {component.detail}"
                )
            else:
                lines.append(f"  · {component.ratio:<9} w={component.weight:.2f}  (no data)")
        if reading.notes:
            lines.append("-" * 52)
            for note in reading.notes:
                lines.append(f"  note: {note}")
        return "\n".join(lines)


class MacroJSONRenderer:
    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def render(self, reading: MacroReading) -> str:
        return json.dumps(reading.as_dict(), indent=self.indent, ensure_ascii=False)
