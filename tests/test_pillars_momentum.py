from regime_trade_desk.pillars.momentum import MomentumPillar
from tests.factories import make_snapshot


def test_momentum_all_bullish_scores_plus2():
    snapshot = make_snapshot(rsi14=60, macd_hist=1.0, trix=1.0, trix_signal=0.5)
    score = MomentumPillar().score(snapshot)
    assert score.score == 2


def test_momentum_all_bearish_scores_minus2():
    snapshot = make_snapshot(rsi14=30, macd_hist=-1.0, trix=-1.0, trix_signal=-0.5)
    score = MomentumPillar().score(snapshot)
    assert score.score == -2


def test_momentum_neutral_rsi_with_no_other_data_scores_zero():
    snapshot = make_snapshot(rsi14=50)
    score = MomentumPillar().score(snapshot)
    assert score.score == 0
    assert "neutral" in score.detail


def test_momentum_mixed_trix_is_reported_as_mixed_not_scored():
    # TRIX above signal but negative -> neither branch triggers -> "TRIX mixed", 0 points from TRIX
    snapshot = make_snapshot(rsi14=50, trix=-0.2, trix_signal=-0.5)
    score = MomentumPillar().score(snapshot)
    assert "TRIX mixed" in score.detail
