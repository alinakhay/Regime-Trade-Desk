"""Value objects wrapping raw price data and computed indicator series.

Centralizing "last valid value", "value N bars ago" and "slope over a
lookback" here means every indicator and pillar shares one tested
implementation instead of each script re-deriving it ad hoc.
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence


class ClosePrices:
    """Immutable, validated sequence of closing prices, oldest to newest."""

    __slots__ = ("_values",)

    def __init__(self, values: Iterable[float]) -> None:
        values = tuple(float(v) for v in values)
        if not values:
            raise ValueError("ClosePrices requires at least one observation.")
        self._values = values

    @classmethod
    def from_raw(cls, raw) -> "ClosePrices":
        """Accepts a bare list, or a dict with a 'close' key (both common
        shapes for JSON payloads produced by market-data APIs)."""
        if isinstance(raw, dict):
            raw = raw["close"]
        return cls(raw)

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, index):
        return self._values[index]

    @property
    def latest(self) -> float:
        return self._values[-1]

    def as_list(self) -> list[float]:
        return list(self._values)

    def tail(self, n: int) -> list[float]:
        return list(self._values[-n:])

    def has_min_length(self, n: int) -> bool:
        return len(self._values) >= n


class TimeSeries:
    """A None-padded computed series (e.g. an EMA) aligned to the source
    ClosePrices it was derived from."""

    __slots__ = ("_values",)

    def __init__(self, values: Sequence[Optional[float]]) -> None:
        self._values = tuple(values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def valid_values(self) -> list[float]:
        return [v for v in self._values if v is not None]

    def last(self, back: int = 0) -> Optional[float]:
        """Most recent non-None value, or `back` valid observations before
        it (back=0 -> latest, back=1 -> previous, ...)."""
        valid = self.valid_values()
        if len(valid) <= back:
            return None
        return valid[-1 - back]

    def slope(self, lookback: int) -> Optional[float]:
        """Change in value versus `lookback` valid observations ago."""
        valid_idx = [i for i, v in enumerate(self._values) if v is not None]
        if len(valid_idx) <= lookback:
            return None
        last_i = valid_idx[-1]
        prev_i = valid_idx[-1 - lookback]
        return self._values[last_i] - self._values[prev_i]

    def first_valid_index(self) -> Optional[int]:
        return next((i for i, v in enumerate(self._values) if v is not None), None)

    def bars_since(self, predicate) -> Optional[int]:
        """Bars since the most recent (from the end) observation for which
        `predicate(index, value)` holds. None if it never held."""
        for back in range(len(self._values)):
            i = len(self._values) - 1 - back
            v = self._values[i]
            if v is not None and predicate(i, v):
                return back
        return None
