import math

import pytest

from regime_trade_desk.domain.series import ClosePrices


@pytest.fixture
def synthetic_close_prices() -> ClosePrices:
    """Same generator as the CLI's `indicators` self-test: 290 bars."""
    return ClosePrices([round(100 + 18 * math.sin(i / 22) + i * 0.06, 2) for i in range(290)])


@pytest.fixture
def bullish_stretched_close_prices() -> ClosePrices:
    """Same generator as the CLI's `score` self-test: bullish run into a
    final spike, meant to trigger bullish-exhaustion flags."""
    close = [round(100 + i * 0.25 + 6 * math.sin(i / 12), 2) for i in range(260)]
    close += [close[-1] * 1.05, close[-1] * 1.10]
    return ClosePrices(close)
