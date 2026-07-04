"""Regime Trade Desk: a deterministic, broker-agnostic three-pillar technical
analysis engine meant to be used as an AI agent's calculator, not a black box.

The agent fetches market data and talks to the user; this package performs
every numeric computation; the user approves any resulting action.
"""
from regime_trade_desk.scoring.scorecard import AssetScorer, Scorecard

__all__ = ["AssetScorer", "Scorecard"]
__version__ = "0.1.0"
