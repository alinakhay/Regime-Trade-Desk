import pytest

from regime_trade_desk.domain.series import ClosePrices
from regime_trade_desk.indicators.engine import IndicatorEngine
from regime_trade_desk.indicators.moving_average import EMA
from regime_trade_desk.indicators.oscillators import MACD, RSIWilder
from regime_trade_desk.indicators.volatility import BollingerBands


def test_ema_of_constant_series_equals_the_constant():
    prices = ClosePrices([100.0] * 300)
    ema = EMA(20).compute(prices)
    assert ema.last() == pytest.approx(100.0)


def test_ema_returns_none_during_warmup():
    prices = ClosePrices([100.0] * 10)
    ema = EMA(20).compute(prices)
    assert ema.last() is None


def test_rsi_wilder_monotonic_increasing_approaches_100():
    prices = ClosePrices([100 + i for i in range(50)])
    rsi = RSIWilder(14).compute(prices)
    assert rsi.last() == pytest.approx(100.0)


def test_rsi_wilder_monotonic_decreasing_approaches_0():
    prices = ClosePrices([200 - i for i in range(50)])
    rsi = RSIWilder(14).compute(prices)
    assert rsi.last() == pytest.approx(0.0)


def test_macd_line_equals_ema_fast_minus_ema_slow(synthetic_close_prices):
    macd = MACD(12, 26, 9).compute(synthetic_close_prices)
    ema_fast = EMA(12).compute(synthetic_close_prices)
    ema_slow = EMA(26).compute(synthetic_close_prices)
    assert macd.line.last() == pytest.approx(ema_fast.last() - ema_slow.last())


def test_macd_histogram_equals_line_minus_signal(synthetic_close_prices):
    macd = MACD(12, 26, 9).compute(synthetic_close_prices)
    assert macd.histogram.last() == pytest.approx(macd.line.last() - macd.signal.last())


def test_bollinger_bands_constant_series_percent_b_is_half():
    prices = ClosePrices([50.0] * 25)
    bb = BollingerBands(20, 2.0).compute(prices)
    assert bb.mid == pytest.approx(50.0)
    assert bb.percent_b == pytest.approx(0.5)


def test_bollinger_bands_insufficient_length_returns_none():
    bb = BollingerBands(20, 2.0).compute(ClosePrices([1.0, 2.0, 3.0]))
    assert bb.mid is None and bb.percent_b is None


def test_indicator_engine_warns_on_short_series():
    snapshot = IndicatorEngine().compute(ClosePrices([100.0] * 50))
    assert snapshot.warning is not None
    assert snapshot.ema200 is None


def test_indicator_engine_snapshot_matches_known_good_values(synthetic_close_prices):
    """Pins the expected indicator values for this 290-bar synthetic series,
    so a future change can't silently alter the numeric core."""
    snapshot = IndicatorEngine().compute(synthetic_close_prices)
    assert snapshot.n_bars == 290
    assert snapshot.close == pytest.approx(127.05)
    assert round(snapshot.ema20, 4) == pytest.approx(119.4774)
    assert round(snapshot.ema50, 4) == pytest.approx(112.8521)
    assert round(snapshot.ema200, 4) == pytest.approx(108.703)
    assert round(snapshot.rsi14, 4) == pytest.approx(98.7798)
    assert round(snapshot.macd_hist, 4) == pytest.approx(0.3371)
    assert round(snapshot.trix, 4) == pytest.approx(0.6418)
    assert snapshot.bars_since_below_ema20 == 40
    assert round(snapshot.percent_b, 4) == pytest.approx(0.9005)
