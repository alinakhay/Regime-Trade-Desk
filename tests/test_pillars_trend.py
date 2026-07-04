from regime_trade_desk.pillars.trend import TrendPillar
from tests.factories import make_snapshot


def test_trend_fully_bullish_structure_scores_plus2():
    snapshot = make_snapshot(close=110, ema20=105, ema50=100, ema200=95, ema200_slope=1.0)
    score = TrendPillar().score(snapshot)
    assert score.score == 2


def test_trend_fully_bearish_structure_scores_minus2():
    snapshot = make_snapshot(close=90, ema20=95, ema50=100, ema200=105, ema200_slope=-1.0)
    score = TrendPillar().score(snapshot)
    assert score.score == -2


def test_trend_with_no_ema_data_scores_zero():
    snapshot = make_snapshot()
    score = TrendPillar().score(snapshot)
    assert score.score == 0
    assert score.detail == ""


def test_trend_mixed_signals_score_between_extremes():
    # price>EMA20 (+1), EMA20<EMA50 (-1), EMA50>EMA200 (+1), EMA200 rising (+1) => 2 points -> +1
    snapshot = make_snapshot(close=110, ema20=100, ema50=105, ema200=95, ema200_slope=1.0)
    score = TrendPillar().score(snapshot)
    assert score.score == 1
