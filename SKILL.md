---
name: regime-trade-desk
description: >-
  Deterministic three-pillar (Trend / Momentum / Macro-Sentiment) technical
  analysis for short-term equity/ETF position management. ALWAYS USE IT
  whenever the user asks to analyze a ticker, review positions, decide
  entries/exits/re-entries, calculate indicators (EMA/RSI/MACD/TRIX/Bollinger),
  score with the three-pillar framework, or read the macro regime — even if
  they don't explicitly name the skill. Compute every indicator via the
  `regime-trade-desk` CLI (never by reasoning over raw price bars), apply the
  exit-on-exhaustion / re-enter-on-rebound decision logic, and respect the
  guardrails below. Do not execute orders without explicit user confirmation.
---

# Regime Trade Desk

Operations manual for short-term technical analysis and (human-approved) execution.
**I (the agent) fetch market data and talk to the user; `regime-trade-desk` is my
deterministic calculator; the user decides.** I never estimate an indicator by
reasoning over price bars directly — I fetch the data and hand it to the CLI.

## Guardrails — Read First, Non-Negotiable

1. **Protected positions**: some tickers may be designated as protected (e.g.
   restricted stock grants). NEVER analyze them for selling or trimming, nor
   include them in exit suggestions. Mention them only as exposure context if relevant.
2. **Deterministic core, qualitative context stays separate**: news, analyst
   ratings, and other qualitative context may be presented alongside the
   scorecard, but they never alter a pillar score — only the human framing.
3. **Use a trusted source for macro/news context**: prefer a single,
   well-known financial data or news site over ones that mix user-submitted
   content (which carries prompt-injection risk).
4. **Mandatory confirmation**: every action this skill suggests is a
   *suggestion*. Never place, modify, or cancel an order without the user's
   explicit, real-time confirmation. If your tools expose a dry-run/simulation
   call, use it before any real execution call.

## Data-Fetching Recipe (Order of Calls)

Load whatever market-data tool/MCP you have available (broker API, data
provider, etc.) with `tool_search` if it's deferred.

**To analyze a ticker:**
1. Fetch ~290 daily closes (bars) for the ticker — enough for EMA200 (≥220 is
   the practical minimum; more is better).
2. Fetch the live/last price if you need current context beyond the last close.
3. If the user has an existing position, fetch it to determine `holding: true/false` for scoring.

**For the Macro-Sentiment pillar (once per session, shared across tickers):**
1. Fetch ~260 daily closes for 7 ETFs: `SPY, RSP, IWM, HYG, LQD, TLT, XLY, XLP`.
2. Fetch the 10Y-2Y treasury yield spread from a trusted source and inject it
   as `yield_spread`. If unavailable, the engine redistributes its weight
   automatically — don't block on it.

**For portfolio context:** fetch current holdings/positions and buying power
however your connected tools expose them.

## Computation Flow (via the `regime-trade-desk` CLI)

The package is pure stdlib; no internet access needed once you have the bars.

**Step 1 — Macro (once per session).** Assemble JSON with the 7 ETFs' closes
plus `yield_spread` and run:
```bash
regime-trade-desk macro macro_input.json --json
```
Save `pillar_score` (-2..+2). That is the Macro-Sentiment score for **every**
ticker analyzed in this session.

**Step 2 — Per ticker.** Assemble `{symbol, close:[...], macro_score, holding}` and run:
```bash
regime-trade-desk score ticker_input.json --json
```
This returns the three-pillar scorecard, the decision (`EXIT/TRIM`, `EXIT`,
`RE-ENTRY (new cycle)`, `TACTICAL REBOUND (counter-trend)`, `HOLD (ride the
cycle)`, `HOLD (under review)`, `WAIT (do not chase)`, `STAY OUT / AVOID`,
`OBSERVE`), and the exhaustion/bearish/rebound/death-cross flags behind it.
Passing the correct `holding` matters — the decision cascade is different for
a holder vs. flat.

If only raw indicators are needed: `regime-trade-desk indicators ticker_input.json`.

## Three-Pillar Framework (Standard Output Format)

Each pillar ranges **-2 to +2**:
- **Trend** — EMA 20/50/200 structure + price position vs. EMAs + EMA200 slope.
- **Momentum** — Wilder RSI-14 + MACD histogram + TRIX-15 vs. signal.
- **Macro-Sentiment** — from `regime-trade-desk macro` (cross-asset regime).

Report all three scores with detail, the total (-6..+6), and the decision.
**Ruling principle: short-term returns via capital rotation** — enter on
rebound → ride → exit on exhaustion → wait for the next trigger. Accumulating
positions is not the default (it keeps capital trapped):

- **EXIT / TRIM** when bullish momentum is EXHAUSTED (RSI turning from
  overbought, MACD histogram shrinking, price stretched / near upper Bollinger band).
- **EXIT** when bearish momentum is RELENTLESS (structural death-cross —
  EMA50<EMA200 and price<EMA50 —, MACD histogram deepening, TRIX below zero).
- **RE-ENTRY (new cycle)** when flat and a rebound arrives with healthy EMA
  structure: valid entry trigger, confirm with candle/volume.
- **TACTICAL REBOUND (counter-trend)** when flat and a rebound appears WITHIN
  a death-cross: a legitimate short-term opportunity, but reduced size, close
  target, tight stop, quick exit. Not a new cycle, does not become a hold.
- **HOLD (ride the cycle)** when holding with positive trend+momentum: the
  next expected action is exit with profit, not adding to the position.
- **WAIT (do not chase)** when flat with a healthy trend but no fresh trigger:
  entering mid-trend has poor R/R; wait for a pullback to EMA20 and a turn.
- **STAY OUT / AVOID**, **HOLD/OBSERVE** as appropriate.

## External Context (News + Analysts)

When you bring in information beyond the indicators:
1. Prefer one trusted financial news/data source for macro and company news.
2. Report analyst consensus, price targets, and recent rating changes if your
   tools expose them.
3. Present all of this as **qualitative context alongside the three-pillar
   scorecard** — it never modifies the scores. Highlight consensus, target vs.
   current price, and any very recent (<2 weeks) rating changes.

## Indicator Details (What `regime-trade-desk` Computes)

- **EMA** seed = SMA of the first N bars (TradingView convention, `adjust=False`).
- **RSI-14** with **Wilder's** smoothing (not a simple moving average).
- **MACD** 12/26/9; line, signal, histogram, and histogram slope.
- **TRIX-15** = % ROC of the triple EMA, with an EMA-9 signal.
- **Bollinger Bands** 20/2 with **population** standard deviation; %B reported.
- Slopes are measured against 5 bars ago by default (`--slope-lookback`).

See [`src/regime_trade_desk/indicators/`](src/regime_trade_desk/indicators/) and
[`src/regime_trade_desk/pillars/`](src/regime_trade_desk/pillars/) for exact
implementation. The math is covered by `pytest` (constant-series EMA,
monotonic-series RSI, MACD = EMA12-EMA26 identity, and more).

## What This Skill Does NOT Do

It is not an automated trading system, does not run on a schedule, and is not
a signal service. Every decision passes through the user. It does not average
down. It does not touch protected positions. It never places, modifies, or
cancels an order on its own.
