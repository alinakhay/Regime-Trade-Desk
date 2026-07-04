from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from regime_trade_desk.domain.models import Flags, IndicatorSnapshot


@dataclass(frozen=True)
class DecisionContext:
    """Everything a decision rule needs to decide whether it applies and
    what to say. `holding=None` is treated as flat (entry framing)."""

    snapshot: IndicatorSnapshot
    trend: int
    momentum: int
    macro: Optional[int]
    holding: Optional[bool]
    flags: Flags

    @property
    def in_position(self) -> bool:
        return self.holding is True

    @property
    def exhaustion_count(self) -> int:
        return len(self.flags.exhaustion)

    @property
    def bearish_count(self) -> int:
        return len(self.flags.bearish)

    @property
    def rebound_count(self) -> int:
        return len(self.flags.rebound)

    @property
    def is_relentless_bearish(self) -> bool:
        return self.bearish_count >= 3 or (self.flags.death_cross and self.bearish_count >= 2)
