"""Translate raw JSON payloads (as an agent would assemble them from a
market-data API) into the package's typed domain objects. Keeping parsing
here means the domain/engine layers never see a raw dict."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from regime_trade_desk.domain.series import ClosePrices
from regime_trade_desk.pillars.macro.market_data import MacroMarketData


@dataclass(frozen=True)
class ScoreRequest:
    symbol: Optional[str]
    prices: ClosePrices
    macro_score: Optional[int]
    holding: Optional[bool]


def load_score_request(raw: dict) -> ScoreRequest:
    return ScoreRequest(
        symbol=raw.get("symbol"),
        prices=ClosePrices.from_raw(raw["close"]),
        macro_score=raw.get("macro_score"),
        holding=raw.get("holding"),
    )


def _closes_from_raw(values: list) -> list[float]:
    """Accepts [close, ...] or [{"close": x}, ...] — both common shapes for
    OHLCV bars returned by market-data APIs."""
    if isinstance(values[0], dict):
        return [float(item["close"]) for item in values]
    return [float(item) for item in values]


def load_macro_market_data(raw: dict) -> MacroMarketData:
    series = {}
    for symbol, values in raw.get("series", {}).items():
        if values:
            series[symbol] = _closes_from_raw(values)

    spread = raw.get("yield_spread")
    if spread is not None:
        spread = [float(spread)] if not isinstance(spread, list) else [float(v) for v in spread]

    return MacroMarketData(as_of=raw.get("as_of", ""), series=series, yield_spread=spread)
