"""Enumerations shared across pillars, decision rules and reporting."""
from __future__ import annotations

from enum import Enum


class Action(str, Enum):
    EXIT_TRIM = "EXIT / TRIM"
    EXIT = "EXIT"
    RE_ENTRY = "RE-ENTRY (new cycle)"
    TACTICAL_REBOUND = "TACTICAL REBOUND (counter-trend)"
    STAY_OUT = "STAY OUT / AVOID"
    HOLD_RIDE_CYCLE = "HOLD (ride the cycle)"
    WAIT = "WAIT (do not chase)"
    HOLD_UNDER_REVIEW = "HOLD (under review)"
    HOLD_OBSERVE = "HOLD / OBSERVE"
    OBSERVE = "OBSERVE"


class Regime(str, Enum):
    INFLATIONARY = "Inflationary"
    CONTRACTION = "Contraction"
    BROADENING = "Broadening"
    CONCENTRATION = "Concentration"
    TRANSITIONAL = "Transitional"
