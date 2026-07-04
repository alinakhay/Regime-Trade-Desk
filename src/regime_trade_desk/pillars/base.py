from __future__ import annotations

from abc import ABC, abstractmethod

from regime_trade_desk.domain.models import IndicatorSnapshot, PillarScore


class Pillar(ABC):
    """A pillar turns an `IndicatorSnapshot` into a -2..+2 grade plus the
    breakdown of what drove it. Each pillar is scored independently; the
    only thing tying them together is the decision layer."""

    @abstractmethod
    def score(self, snapshot: IndicatorSnapshot) -> PillarScore:
        raise NotImplementedError
