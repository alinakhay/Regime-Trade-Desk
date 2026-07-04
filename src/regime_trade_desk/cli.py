"""Command-line entry point. Each subcommand mirrors one layer of the
package so an agent (or a human) can call exactly the calculator it needs:

    regime-trade-desk indicators ticker.json
    regime-trade-desk macro macro_input.json --json
    regime-trade-desk score ticker_input.json --json

Every subcommand also runs a deterministic self-test on synthetic data when
no input file is given, so the package can be sanity-checked with zero setup.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

from regime_trade_desk.domain.series import ClosePrices
from regime_trade_desk.indicators.engine import IndicatorEngine
from regime_trade_desk.io.loaders import ScoreRequest, load_macro_market_data, load_score_request
from regime_trade_desk.pillars.macro.engine import MacroEngine
from regime_trade_desk.pillars.macro.market_data import MacroMarketData
from regime_trade_desk.reporting.renderers import (
    JSONRenderer,
    MacroJSONRenderer,
    MacroTextRenderer,
    TextRenderer,
)
from regime_trade_desk.scoring.scorecard import AssetScorer


def _indicators_self_test_prices() -> ClosePrices:
    closes = [round(100 + 18 * math.sin(i / 22) + i * 0.06, 2) for i in range(290)]
    return ClosePrices(closes)


def _macro_self_test_market_data() -> MacroMarketData:
    n = 260

    def gen(start: float, drift: float, noise_seed: int) -> list[float]:
        out, value = [], start
        for i in range(n):
            value *= 1 + drift + 0.004 * math.sin(i / 9 + noise_seed)
            out.append(round(value, 2))
        return out

    return MacroMarketData(
        as_of="self-test",
        series={
            "SPY": gen(400, 0.0006, 1),
            "RSP": gen(150, 0.0009, 2),   # equal-weight gains -> broadening
            "IWM": gen(180, 0.0011, 3),   # small-cap wins
            "HYG": gen(75, 0.0004, 4),
            "LQD": gen(105, 0.0001, 5),
            "TLT": gen(95, -0.0003, 6),
            "XLY": gen(190, 0.0008, 7),
            "XLP": gen(78, 0.0002, 8),
        },
        yield_spread=[round(-0.3 + 0.004 * i, 3) for i in range(60)],  # re-steepening
    )


def _score_self_test_request() -> ScoreRequest:
    # Bullish series stretching toward a ceiling, should trigger exhaustion.
    close = [round(100 + i * 0.25 + 6 * math.sin(i / 12), 2) for i in range(260)]
    close += [close[-1] * 1.05, close[-1] * 1.10]
    return ScoreRequest(symbol="SELFTEST", prices=ClosePrices(close), macro_score=1, holding=True)


def cmd_indicators(args: argparse.Namespace) -> int:
    if args.input:
        with open(args.input) as f:
            prices = ClosePrices.from_raw(json.load(f))
    else:
        prices = _indicators_self_test_prices()
        print("[self-test: synthetic series of 290 bars]\n", file=sys.stderr)

    snapshot = IndicatorEngine().compute(prices, args.slope_lookback)
    print(json.dumps(snapshot.as_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_macro(args: argparse.Namespace) -> int:
    if args.input:
        with open(args.input) as f:
            market = load_macro_market_data(json.load(f))
    else:
        market = _macro_self_test_market_data()
        print("[self-test with synthetic data — no input file]\n", file=sys.stderr)

    engine = MacroEngine(slow=args.slow, slope_win=args.slope_win, corr_win=args.corr_win)
    reading = engine.score(market)
    renderer = MacroJSONRenderer() if args.json else MacroTextRenderer()
    print(renderer.render(reading))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    if args.input:
        with open(args.input) as f:
            request = load_score_request(json.load(f))
    else:
        request = _score_self_test_request()
        print("[synthetic self-test]\n", file=sys.stderr)

    scorecard = AssetScorer().score(
        request.prices, symbol=request.symbol,
        macro_score=request.macro_score, holding=request.holding,
    )
    renderer = JSONRenderer() if args.json else TextRenderer()
    print(renderer.render(scorecard))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="regime-trade-desk",
        description="Deterministic three-pillar (Trend / Momentum / Macro-Sentiment) technical analysis engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    indicators_parser = subparsers.add_parser("indicators", help="Compute the raw indicator stack for one asset.")
    indicators_parser.add_argument("input", nargs="?", help="JSON file: {'close': [...]} or [...]. Omit for a self-test.")
    indicators_parser.add_argument("--slope-lookback", type=int, default=5)
    indicators_parser.set_defaults(func=cmd_indicators)

    macro_parser = subparsers.add_parser("macro", help="Score the cross-asset Macro-Sentiment pillar.")
    macro_parser.add_argument("input", nargs="?", help="JSON file with cross-asset close series. Omit for a self-test.")
    macro_parser.add_argument("--json", action="store_true", help="Machine-readable output instead of a text report.")
    macro_parser.add_argument("--slow", type=int, default=200)
    macro_parser.add_argument("--slope-win", type=int, default=20)
    macro_parser.add_argument("--corr-win", type=int, default=40)
    macro_parser.set_defaults(func=cmd_macro)

    score_parser = subparsers.add_parser("score", help="Full three-pillar scorecard and decision for one asset.")
    score_parser.add_argument("input", nargs="?", help="JSON file: {symbol, close:[...], macro_score?, holding?}. Omit for a self-test.")
    score_parser.add_argument("--json", action="store_true", help="Machine-readable output instead of a text report.")
    score_parser.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
