from regime_trade_desk.decision.flags import FlagDetector
from tests.factories import make_snapshot


def test_exhaustion_flags_rsi_turning_and_macd_shrinking_and_upper_band():
    snapshot = make_snapshot(
        close=110, ema20=100,
        rsi14=72, rsi14_prev=78,
        macd_hist=0.5, macd_hist_prev=0.8,
        percent_b=1.02,
    )
    flags = FlagDetector().detect(snapshot)
    assert any("overbought" in f for f in flags.exhaustion)
    assert any("shrinking" in f for f in flags.exhaustion)
    assert any("upper Bollinger" in f for f in flags.exhaustion)
    assert any("stretched" in f for f in flags.exhaustion)


def test_bearish_flags_structural_and_momentum():
    snapshot = make_snapshot(
        close=90, ema50=95, ema200=100, ema200_slope=-1.0,
        macd_hist=-0.5, macd_hist_prev=-0.2,
        trix=-1.0, trix_signal=-0.5,
        rsi14=40, rsi14_prev=45,
    )
    flags = FlagDetector().detect(snapshot)
    assert any("EMA50<EMA200" in f for f in flags.bearish)
    assert any("deepening" in f for f in flags.bearish)
    assert any("TRIX<signal" in f for f in flags.bearish)
    assert any("weak and falling" in f for f in flags.bearish)


def test_death_cross_flag_requires_structure_and_price_below_ema50():
    snapshot = make_snapshot(close=90, ema50=95, ema200=100)
    assert FlagDetector().detect(snapshot).death_cross is True

    snapshot = make_snapshot(close=110, ema50=95, ema200=100)
    assert FlagDetector().detect(snapshot).death_cross is False


def test_rebound_flag_rsi_turning_from_oversold():
    snapshot = make_snapshot(rsi14=40, rsi14_prev=30)
    flags = FlagDetector().detect(snapshot)
    assert any("oversold" in f for f in flags.rebound)


def test_rebound_flag_ema20_reclaim_requires_recent_dip():
    snapshot = make_snapshot(
        close=105, ema20=100, ema20_slope=1.0, bars_since_below_ema20=3,
    )
    flags = FlagDetector().detect(snapshot)
    assert any("reclaims EMA20" in f for f in flags.rebound)

    # No recent dip (never closed below EMA20 recently) -> not a rebound.
    snapshot = make_snapshot(
        close=105, ema20=100, ema20_slope=1.0, bars_since_below_ema20=None,
    )
    flags = FlagDetector().detect(snapshot)
    assert not any("reclaims EMA20" in f for f in flags.rebound)


def test_rebound_flag_fresh_trix_cross_only_on_crossover_bar():
    snapshot = make_snapshot(trix=-0.1, trix_signal=-0.2, trix_prev=-0.3, trix_signal_prev=-0.2)
    flags = FlagDetector().detect(snapshot)
    assert any("fresh bullish TRIX cross" in f for f in flags.rebound)

    # Cross already happened earlier bar (trix_prev > signal_prev): not fresh.
    snapshot = make_snapshot(trix=-0.1, trix_signal=-0.2, trix_prev=-0.15, trix_signal_prev=-0.25)
    flags = FlagDetector().detect(snapshot)
    assert not any("fresh bullish TRIX cross" in f for f in flags.rebound)
