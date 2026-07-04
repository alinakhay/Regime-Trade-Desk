import json

from regime_trade_desk.cli import main


def test_cli_indicators_self_test_runs_clean(capsys):
    exit_code = main(["indicators"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert json.loads(out)["n_bars"] == 290


def test_cli_macro_self_test_json(capsys):
    exit_code = main(["macro", "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["regime"] == "Broadening"


def test_cli_score_self_test_json(capsys):
    exit_code = main(["score", "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["symbol"] == "SELFTEST"
    assert payload["decision"]["action"] == "HOLD (ride the cycle)"
