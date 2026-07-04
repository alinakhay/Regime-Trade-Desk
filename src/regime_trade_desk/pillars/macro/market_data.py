from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MacroMarketData:
    """Cross-asset closes needed for the Macro-Sentiment pillar, plus an
    optionally-injected yield-curve spread. `series` values are plain
    oldest-to-newest close lists (parsing/validation happens in `io`)."""

    as_of: str
    series: dict[str, list[float]]
    yield_spread: Optional[list[float]] = None

    def closes(self, symbol: str) -> Optional[list[float]]:
        return self.series.get(symbol) or None
