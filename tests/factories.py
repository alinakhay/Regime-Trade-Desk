"""Test-only helpers for constructing domain objects without repeating all
of IndicatorSnapshot's fields in every test."""
from regime_trade_desk.domain.models import IndicatorSnapshot

_SNAPSHOT_DEFAULTS = dict(
    n_bars=300, warning=None, close=100.0,
    ema20=None, ema50=None, ema200=None,
    ema20_slope=None, ema50_slope=None, ema200_slope=None,
    rsi14=None, rsi14_prev=None,
    macd_line=None, macd_signal=None, macd_hist=None, macd_hist_prev=None,
    trix=None, trix_prev=None, trix_signal=None, trix_signal_prev=None,
    bars_since_below_ema20=None,
    bb_mid=None, bb_upper=None, bb_lower=None, percent_b=None,
)


def make_snapshot(**overrides) -> IndicatorSnapshot:
    fields = {**_SNAPSHOT_DEFAULTS, **overrides}
    return IndicatorSnapshot(**fields)
