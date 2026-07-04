from regime_trade_desk.domain.enums import Action
from regime_trade_desk.reporting.renderers import JSONRenderer, TextRenderer
from regime_trade_desk.scoring.scorecard import AssetScorer


def test_asset_scorer_end_to_end_matches_known_good_decision(bullish_stretched_close_prices):
    """Pins the expected pillar scores and decision for the bullish-spike
    synthetic series, so a future change can't silently alter the cascade."""
    scorecard = AssetScorer().score(
        bullish_stretched_close_prices, symbol="SELFTEST", macro_score=1, holding=True,
    )
    assert scorecard.trend.score == 2
    assert scorecard.momentum.score == 2
    assert scorecard.pillar_total == 5
    assert scorecard.decision.action == Action.HOLD_RIDE_CYCLE


def test_asset_scorer_without_macro_score_leaves_macro_pillar_none(bullish_stretched_close_prices):
    scorecard = AssetScorer().score(bullish_stretched_close_prices, symbol="X")
    assert scorecard.macro_score is None
    as_dict = scorecard.as_dict()
    assert as_dict["pillars"]["macro_sentiment"]["score"] is None
    assert as_dict["pillars"]["macro_sentiment"]["detail"] is None


def test_text_renderer_includes_symbol_and_decision(bullish_stretched_close_prices):
    scorecard = AssetScorer().score(bullish_stretched_close_prices, symbol="SELFTEST", macro_score=1, holding=True)
    text = TextRenderer().render(scorecard)
    assert "SELFTEST" in text
    assert scorecard.decision.action.value in text


def test_json_renderer_round_trips_through_json(bullish_stretched_close_prices):
    import json

    scorecard = AssetScorer().score(bullish_stretched_close_prices, symbol="SELFTEST", macro_score=1, holding=True)
    payload = json.loads(JSONRenderer().render(scorecard))
    assert payload["symbol"] == "SELFTEST"
    assert payload["decision"]["action"] == scorecard.decision.action.value
