"""Immutable result objects passed between engine, pillars and decision
layers. Keeping these as typed dataclasses (rather than raw dicts) lets
callers rely on attribute access and IDE/type-checker support end to end."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from regime_trade_desk.domain.enums import Action, Regime


def _round(value: Optional[float], ndigits: int = 4) -> Optional[float]:
    return round(value, ndigits) if isinstance(value, float) else value


@dataclass(frozen=True)
class IndicatorSnapshot:
    """Latest values + recent slopes for the full indicator stack, as of the
    most recent close in the input series."""

    n_bars: int
    warning: Optional[str]
    close: float
    ema20: Optional[float]
    ema50: Optional[float]
    ema200: Optional[float]
    ema20_slope: Optional[float]
    ema50_slope: Optional[float]
    ema200_slope: Optional[float]
    rsi14: Optional[float]
    rsi14_prev: Optional[float]
    macd_line: Optional[float]
    macd_signal: Optional[float]
    macd_hist: Optional[float]
    macd_hist_prev: Optional[float]
    trix: Optional[float]
    trix_prev: Optional[float]
    trix_signal: Optional[float]
    trix_signal_prev: Optional[float]
    bars_since_below_ema20: Optional[int]
    bb_mid: Optional[float]
    bb_upper: Optional[float]
    bb_lower: Optional[float]
    percent_b: Optional[float]

    def as_dict(self, ndigits: int = 4) -> dict:
        return {
            k: (_round(v, ndigits) if isinstance(v, float) else v)
            for k, v in self.__dict__.items()
        }


@dataclass(frozen=True)
class PillarScore:
    """A single pillar's grade, from -2 to +2, plus the human-readable
    breakdown of what drove it."""

    score: int
    detail: str


@dataclass(frozen=True)
class Flags:
    """Qualitative signal flags detected ahead of the decision cascade."""

    exhaustion: list[str] = field(default_factory=list)
    bearish: list[str] = field(default_factory=list)
    rebound: list[str] = field(default_factory=list)
    death_cross: bool = False
    stretch_pct: float = 0.0

    def as_dict(self) -> dict:
        return {
            "exhaustion": self.exhaustion,
            "bearish": self.bearish,
            "rebound": self.rebound,
            "death_cross": self.death_cross,
            "stretch_pct": self.stretch_pct,
        }


@dataclass(frozen=True)
class Decision:
    action: Action
    rationale: str
    framing: str
    flags: Flags

    def as_dict(self) -> dict:
        return {
            "action": self.action.value,
            "rationale": self.rationale,
            "framing": self.framing,
            "flags": self.flags.as_dict(),
        }


@dataclass(frozen=True)
class MacroComponentReading:
    name: str
    ratio: str
    weight: float
    signal: Optional[float]
    detail: str
    available: bool

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "ratio": self.ratio,
            "weight": self.weight,
            "signal": _round(self.signal, 2),
            "detail": self.detail,
            "available": self.available,
        }


@dataclass(frozen=True)
class MacroReading:
    as_of: str
    composite: float
    regime: Regime
    pillar_score: int
    pillar_label: str
    inflationary_flag: bool
    equity_bond_correlation: Optional[float]
    components: list[MacroComponentReading]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "as_of": self.as_of,
            "composite": self.composite,
            "regime": self.regime.value,
            "pillar_score": self.pillar_score,
            "pillar_label": self.pillar_label,
            "inflationary_flag": self.inflationary_flag,
            "equity_bond_correlation": self.equity_bond_correlation,
            "components": [c.as_dict() for c in self.components],
            "notes": self.notes,
        }
