# No Persistent Edge: A Pre-Registered, Multi-Phase Study of Long-Only Retail Algorithmic Trading on Binance Spot (2017–2026)

**Author:** Cristhian Benitez
**Date:** May 2026 (rev. with robustness checks)
**Status:** Preprint / working paper
**Companion repository:** https://github.com/cbenitezpy/chocotrader-research — simulators, data fetchers, and full result logs.

---

## Abstract

We report the complete results of *Chocotrader*, a self-funded, pre-registered research program that asked a single question: **does any simple, retail-accessible algorithmic strategy have a persistent, exploitable edge on Binance Spot, net of realistic costs, that justifies committing real capital?** Over six research phases spanning ~50–80 hours of work and 9.25 years of historical data (2017–2026, 66,682 four-hour candles across five pairs), we evaluated trend-following (EMA crossover, Donchian breakout, SuperTrend), mean-reversion (Bollinger Bands), regime-aware filtering (ADX/ATR detectors), naive ensembles, multi-pair portfolios, and — in the final phase — non-technical alpha sources (the Fear & Greed index, perpetual-futures funding rate, and the US Dollar Index as a macro overlay).

**The answer was no.** No strategy passed our pre-registered out-of-sample (OOS) gate. The single naive ensemble that cleared in-sample gates collapsed to an OOS Sharpe of **+0.041** against a required ≥0.8. The strongest active strategy in the full-period audit (SuperTrend on BTC) achieved a risk-adjusted Sharpe of 0.977 — better than Buy-and-Hold (B&H) BTC's 0.809 — but returned **7× less absolute capital** ($2,190 vs. $15,958 on a $1,000 base). In the most recent and most relevant market regime (2023–2026), **every** strategy we tested, including all six external-signal variants, underperformed B&H BTC.

The contribution of this paper is twofold. First, it is an honest **negative result** in a domain dominated by survivorship bias and unpublished failures. Second, it is a **reproducible methodology** — pre-registration, physical OOS sealing, walk-forward validation, a realistic next-open fill model, and constitutional gates — that prevented us from deploying an illusory edge. We document one case where an apparently profitable mean-reversion signal (Sharpe +0.72 under an optimistic fill model) **completely vanished** (Sharpe −0.56) once a realistic fill model was applied. Total capital lost across the entire program: **$0**.

We then subjected the conclusion to a battery of adversarial robustness checks (Section 6), testing whether the result is an artifact of our cost model, our 4h timeframe, our start date, our large-cap universe, or our long-only constraint. The conclusion survives all five: lower costs (even zero) rescue no negative-Sharpe strategy; a daily timeframe does not beat 4h; the active edge over B&H is start-date dependent and never clears the gate; the Sharpe gate is unmet in all seven surviving mid-cap altcoins (an upper bound, since delisted pairs are absent); and adding short-selling via 1x perpetuals with real funding costs *worsens* the trend-following Sharpe rather than improving it. Notably, the long/short test first produced a too-good Sharpe of 2.7 that we traced to an accounting bug — a live demonstration of the very discipline the paper advocates.

**Scope note (important).** Our claim is deliberately narrow: *within the long-only, spot-only, retail-cost envelope*, no simple technical or sentiment strategy beat Buy-and-Hold BTC out-of-sample. We do **not** claim that no edge exists in crypto generally; leveraged perpetual carry, cross-exchange arbitrage, options, and ML approaches lie outside this envelope and are explicitly out of scope.

**Keywords:** algorithmic trading, cryptocurrency, backtesting, pre-registration, out-of-sample validation, negative results, reproducibility, market efficiency.

---

## 1. Introduction

### 1.1 Motivation

Retail interest in algorithmic cryptocurrency trading is enormous, and the public narrative is overwhelmingly positive: social media is saturated with screenshots of profitable bots and "strategies that print money." Almost none of this is accompanied by pre-registered methodology, realistic cost modeling, or out-of-sample validation. The base rate of *published failures* is close to zero, which is itself strong evidence of severe survivorship and publication bias.

Chocotrader began as an attempt to build such a bot for personal use, with a deliberately modest target: find any strategy good enough to justify risking $100–$500 of real capital on Binance Spot. The project imposed strict self-governance from day one — a written "constitution" of non-negotiable principles, sequential validation gates, and a rule that *"no edge"* was an acceptable and respectable outcome. This paper reports what happened.

### 1.2 Scope and constraints

The research operated under deliberate, self-imposed constraints that mirror the situation of a disciplined retail trader:

- **Spot only.** No futures, no margin, no leverage, no short-selling.
- **Long-only.** A direct consequence of spot-only.
- **Realistic costs.** 0.10% fee per side (0.20% round-trip, no exchange-token discount) plus 0.05% slippage per side on BTC/ETH — a 0.30% round-trip floor.
- **Low capital.** $100–$1,000, where minimum-notional and fee drag are material.
- **No machine learning.** By constitutional rule, to keep every result interpretable and to avoid the overfitting surface that ML introduces.

These constraints matter: they are precisely the conditions under which a typical retail participant operates, and several of our conclusions are *consequences* of these constraints rather than universal claims.

### 1.3 Contributions

1. A complete, **pre-registered, six-phase empirical study** of retail-accessible strategies on 9.25 years of data, with all in-sample and out-of-sample results reported — including the failures.
2. A documented, reusable **methodological framework** (constitution → pre-registration → OOS sealing → walk-forward → realistic fill model → gates) that demonstrably prevented the deployment of an illusory edge.
3. A clear empirical demonstration of three recurring traps in retail backtesting: the **fill-model artifact**, the **regime-overfit illusion**, and the **risk-adjusted-vs-absolute-return paradox** relative to Buy-and-Hold.
4. An honest negative result: under the stated constraints, **we found no persistent, exploitable edge** — and we argue that for low capital, dollar-cost averaging (DCA) into BTC dominates an active bot on every dimension that matters.

### 1.4 What this paper is not

This is not a claim that *no* algorithmic edge exists in crypto markets. Edges plausibly exist in regimes we deliberately excluded — perpetual-futures carry/basis trading, cross-exchange arbitrage, market making, and machine-learning approaches with data and latency beyond a retail participant's reach. Our claim is narrower and, we believe, more useful: **within the spot-only, long-only, retail-cost envelope, simple technical and sentiment-based strategies do not beat Buy-and-Hold BTC out-of-sample.**

### 1.5 Related work and how this study differs

Our result sits inside three established literatures. First, **market efficiency in crypto.** The Efficient Market Hypothesis (Fama, 1970) would predict no exploitable edge; the Adaptive Market Hypothesis (Lo, 2004) refines this to *time-varying* efficiency, and empirical crypto studies confirm exactly that — markets are closer to efficient in bull regimes and less efficient in bear/early regimes (Khuntia & Pattanayak, 2018; Tran & Leirvik, 2020). This is precisely the pattern we observe: any apparent edge concentrates in specific (often early or trending) regimes and decays out-of-sample.

Second, **momentum and trend-following.** Cross-sectional momentum (Jegadeesh & Titman, 1993) and time-series momentum (Moskowitz, Ooi & Pedersen, 2012) are among the most robust anomalies in traditional assets, and a growing crypto literature reports time-series momentum returns exceeding 20% annualized (e.g., Liu & Tsyvinski, 2021; momentum surveys cited herein). Crucially, much of that literature attributes the effect to market immaturity and noise-trader dominance, and a large fraction reports gross or near-gross performance, optimistic fills, or in-sample results. Our contribution is to show that under a **realistic next-open fill and retail costs**, that reported edge does not survive out-of-sample for a retail long-only participant.

Third, **backtest overfitting.** Bailey, Borwein, López de Prado & Zhu (2014) on the *Probability of Backtest Overfitting*, and Bailey & López de Prado (2014) on the *Deflated Sharpe Ratio*, show that trying many strategy variants and keeping the best inflates the Sharpe even when all candidates are noise. This is the failure our pre-registration, sealed OOS, and (in this revision) bootstrap significance testing are designed to prevent. Our finding that the best active Sharpe is statistically indistinguishable from Buy-and-Hold (Section 6.6) is a direct empirical instance of their warning.

In short: where the optimistic crypto-momentum literature reports edge, we report that the edge does not clear a Buy-and-Hold benchmark out-of-sample once execution and selection bias are modeled honestly — a result fully consistent with the adaptive-efficiency and backtest-overfitting literatures.

---

## 2. Methodology and Framework

The methodological framework is, in our view, the more transferable contribution of this work. Each component exists to defend against a specific, well-documented failure mode of backtesting.

### 2.1 Constitution and sequential gates

Before any code was written, we authored a `constitution.md` of non-negotiable principles, the most important being *capital preservation over return* and *"no trade is better than a bad trade."* It defined three **sequential gates**, each of which had to be passed before the next:

1. **Backtest gate:** Sharpe ≥ 1.2 (train+validation), Sharpe ≥ 0.8 (out-of-sample), MaxDD ≤ 30%.
2. **Testnet gate:** operational validation only (uptime, reconciliation, idempotency) — explicitly *not* a profitability test.
3. **Mainnet gate:** small real capital, scaled only after sustained performance.

Critically, the gates were written down *before* results existed, so they could not be silently relaxed when a strategy "almost" passed.

### 2.2 Pre-registration

After Phase 1 (v1), we adopted **pre-registration**: every hypothesis, parameter, data split, and acceptance threshold was committed to version control *before* looking at the data. This directly attacks the multiple-testing / data-snooping problem. The contrast was stark: v1 ran 20+ experiments without pre-registration over 14 days; v2 ran a pre-registered set of ~6 experiments in roughly one day and reached an equally valid conclusion with far less data-snooping risk.

### 2.3 Out-of-sample sealing

A dedicated OOS dataset was reserved and **physically sealed** (`chmod 0444`, access logged with timestamp and reason). It was accessed exactly once, at the end of a phase, to confirm or refute the in-sample finding — never to iterate. When the v1 OOS dataset (2024–2025) was consumed, it was treated as *burned* and never reused, precisely because reusing it would constitute retroactive data-snooping. In the final phase (v6), the gate was never cleared, so the OOS dataset was **never accessed** and remains clean.

### 2.4 Walk-forward validation

We split the historical record into sequential windows (W1, W2, W3) and measured each strategy's behavior across them. The most recent window (W3) served as a *predictor* of out-of-sample performance. This proved remarkably accurate: in v1, the W3 walk-forward prediction matched the realized OOS Sharpe to within ±0.03 for individual components (Table 3). Walk-forward thus functioned as an early-warning system — we could anticipate OOS failure *without burning the OOS set*.

### 2.5 The fill model

The single most consequential methodological choice was the **fill model**. We use `next_open`: a signal computed at the close of bar *t* is filled at the open of bar *t+1*. The naive alternative — filling at the close of the signal bar (`same_close`) — silently grants the backtest information it could not have had in real time.

For trend-following this distinction is negligible (|ΔSharpe| < 0.01, because a one-bar delay is noise against a multi-week trend). For mean-reversion it is **catastrophic**, because the entire edge depends on capturing an immediate rebound from an extreme. We document this in detail in Section 4.2.

### 2.6 Cost model

All backtests apply 0.10% fee per side (0.20% round-trip, no BNB discount) and 0.05% slippage per side on BTC/ETH (0.10% on less liquid alts), for a 0.30% round-trip floor. We verified that fees are *not* the binding constraint: across strategies, total fees represented only 4–10% of gross PnL. When a strategy's Sharpe was poor, the cause was signal noise, not cost.

### 2.7 The benchmark: Buy-and-Hold BTC

Every result is reported against **Buy-and-Hold BTC** as the first row of every table. This was a lesson learned the hard way — v1 did not benchmark systematically against B&H until late, which inflated early expectations. Over 2017–2026, B&H BTC delivered a Sharpe of 0.809 with a +1,495.8% return (and a brutal −83.9% max drawdown). This is an extraordinarily high bar: any active strategy claiming to "beat the market" must clear a sustained Sharpe above 0.81 — very difficult for long-only retail spot with 0.30% round-trip costs.

### 2.8 Data

We assembled 66,682 four-hour candles covering 2017-08 to 2026-05, continuous and gap-free, for five USDT pairs (BTC, ETH, SOL, BNB, XRP), stored as Parquet. Daily resolution was also retained for longer-horizon analysis. For the final phase we added three external series: the Fear & Greed index (3,027 daily observations from 2018-02 via alternative.me), perpetual-futures funding rate (7,333 eight-hour observations for BTC from 2019-09 via Binance), and the US Dollar Index (DTWEXBGS, 5,107 daily observations via FRED).

---

## 3. Experimental Design

The program ran in six phases. Each phase was a self-contained attempt to find an edge, informed by the failures of the previous one.

| Phase | Focus | Headline result |
|---|---|---|
| **v1** | Trend-following + naive ensemble (20+ experiments, 14 days) | Best ensemble: OOS Sharpe **+0.041** (gate ≥0.8). FAIL. |
| **v2** | Regime-aware filtering (ADX/ATR detector) | Anti-edge in every variant. ABORT. |
| **v3** | Bollinger mean-reversion, pure (realistic fill) | Train+val Sharpe **−0.56** (gate ≥0.5). FAIL. |
| **Audit** | Full-period sweep: 144 combinations, 9.25 years | No conservative scenario reaches Sharpe ≥ 1.2. |
| **v5** | Multi-pair SuperTrend portfolio | In-sample Sharpe improves; OOS regime-dependent. |
| **v6** | External alpha (F&G, funding, DXY), pre-registered | No strategy passes walk-forward W3. CLOSE. |

### 3.1 Phase v1 — Trend-following and naive ensembles

We tested EMA crossover (multiple periods), Donchian breakout, SuperTrend, and SMA-filtered variants, on BTC and ETH at 4h. The best single strategies cleared a Sharpe near 1.0 in-sample but were carried almost entirely by BTC; ETH consistently bled. No pure trend-following variant cleared the in-sample gate alone. A naive 60/40 ensemble of a trend component and a Bollinger mean-reversion component *did* clear the in-sample gate (Sharpe 1.48) and passed a formal pre-OOS audit — then failed OOS.

### 3.2 Phase v2 — Regime-aware filtering

The hypothesis: classify the market into regimes (trending / ranging) using an ADX/ATR/Bollinger-width detector, then trade each strategy only in its favorable regime. The detector classified regimes reasonably in retrospect (~40% coherence with manual labels) but was **useless as a real-time trade filter**, for a structural reason elaborated in Section 5.3. Both the trend variant (E1) and the mean-reversion variant (E3) showed anti-edge and were aborted.

### 3.3 Phase v3 — Bollinger mean-reversion under a realistic fill

The mean-reversion component that survived v1 walk-forward was re-tested in isolation under the `next_open` fill model. It failed catastrophically (Section 4.2). This was the most important single result of the entire program.

### 3.4 Full-period audit — 144 combinations

To remove any doubt that a lucky parameter choice was being missed, we ran an exhaustive sweep: 8 strategy configurations × 2 active pairs × 4 capital scenarios × 3 risk profiles over the full 9.25-year record, all under `next_open`. This is the canonical reference (Section 4.1).

### 3.5 Phase v5 — Multi-pair portfolios

SuperTrend was evaluated across five pairs and as 2-to-5-pair portfolios. Portfolio Sharpe improved with diversification *in-sample* (the all-5 portfolio reached Sharpe 2.10 with low cross-pair correlation), but the walk-forward and the prior OOS verdict on the trend component (−0.55) showed this in-sample improvement did not translate forward.

### 3.6 Phase v6 — External (non-technical) alpha sources

The final phase asked whether information *exogenous* to the traded pair's own price could add edge. Three hypotheses, each in two forms (a **filter** over SuperTrend and a **standalone** signal), pre-registered before any data was examined:

- **H1 — Fear & Greed:** extreme fear (index ≤ 25) as a contrarian buy signal.
- **H3 — Funding rate:** extreme perpetual funding as a sentiment proxy for spot.
- **H5 — DXY overlay:** suppress long entries while the US dollar is in an uptrend.

(A fourth hypothesis, BTC dominance, was dropped pre-registration for look-ahead risk; a fifth, exchange net-flows, was excluded for requiring premium data.)

---

## 4. Results

### 4.1 The canonical table: full-period audit (2017–2026, $1,000 compound, conservative profile)

| Strategy | Final equity | Return | Sharpe | MaxDD | Trades | Win rate | PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Buy & Hold BTC** | **$15,958** | **+1,495.8%** | **0.809** | −83.9% | 1 | 100% | ∞ |
| Buy & Hold ETH | $6,942 | +594.2% | 0.694 | −94.1% | 1 | 100% | ∞ |
| DCA monthly BTC | $4,867 | +386.7% | 0.650 | −69.5% | — | — | — |
| SuperTrend(10,3) BTC | $2,190 | +119.0% | 0.977 | −13.7% | 225 | 37.8% | 1.59 |
| SuperTrend(10,3) ETH | $2,372 | +137.2% | 0.840 | −17.6% | 222 | 37.4% | 1.51 |
| EMA(12/26) BTC | $2,203 | +120.3% | 0.903 | −21.6% | 315 | 27.9% | 1.47 |
| EMA(12/26) ETH | $1,914 | +91.4% | 0.635 | −18.4% | 336 | 26.2% | 1.29 |
| Donchian(20/10) BTC | $1,746 | +74.6% | 0.780 | −19.0% | 249 | 38.6% | 1.44 |
| Donchian(20/10) ETH | $1,750 | +75.0% | 0.592 | −20.2% | 265 | 31.7% | 1.30 |
| BB(20,2.75) BTC | $836 | −16.4% | −0.358 | −20.6% | 145 | 58.6% | 0.70 |
| BB(20,2.75) ETH | $796 | −20.4% | −0.529 | −24.0% | 20 | 35.0% | 0.20 |

**Findings.** B&H BTC returns 16× on $1,000; no active strategy exceeds ~2.4×. The best active *Sharpe* in any scenario was EMA BTC on an aggressive profile (1.045), but that required 40% equity per position and optimistic 7.5 bps fees; **no conservative-profile strategy reached Sharpe 1.0, and none reached the constitutional gate of 1.2.** Bollinger mean-reversion lost money systematically; its ETH variant would have been liquidated by the minimum-equity rule in 12 of 12 scenarios.

### 4.2 The fill-model artifact (the single most important result)

The Bollinger Bands mean-reversion signal, BB(20, 2.75), appeared to be the one genuinely profitable idea to emerge from v1:

| Fill model | OOS Sharpe | Interpretation |
|---|---:|---|
| `same_close` (optimistic) | **+0.72** | Looks like a deployable edge |
| `next_open` (realistic) | **−0.56** | No edge; loses money |
| **Delta** | **−1.28** | The "edge" was an artifact |

The entire apparent edge of mean-reversion depended on filling at the close of the *same* bar that generated the signal — capturing a rebound that, with a realistic one-bar (4h) delay, has already partially occurred. **Had we deployed on the optimistic backtest, we would have committed real capital to a strategy with no edge.** This single check is the clearest justification for the entire methodological apparatus.

### 4.3 Walk-forward predicted out-of-sample with high fidelity

| Component | W3 walk-forward (predicted) | OOS (realized) | Error |
|---|---:|---:|---:|
| Trend only | −0.54 | −0.55 | 0.01 |
| Mean-reversion only | +0.70 | +0.72 | 0.02 |
| Ensemble 60/40 | −0.22 | +0.04 | 0.26 |

For individual components, walk-forward predicted the realized OOS Sharpe to within ±0.03. This validates walk-forward as a genuine regime-capturing instrument, not noise — and it let us anticipate failure without consuming the OOS set.

### 4.4 The v1 ensemble: the closest we came, and why it failed

The 60/40 ensemble cleared every in-sample gate (Sharpe 1.48 train+val, MaxDD −14.1%, 223 trades, formal audit pass). Its OOS Sharpe was **+0.041** ($100 → $99.81, breakeven). Decomposed: the trend component returned −0.55 (it lost money in the post-rally consolidation regime), the mean-reversion component returned +0.72 (real but below the 0.8 gate), and the 60% weight on the failing trend component dragged the ensemble to breakeven. **Combining a strategy that has negative edge in the evaluation regime does not produce diversification — it produces dilution.**

### 4.5 Phase v6: external signals add nothing out-of-sample

In-sample (train+val 2018–2026), measured as Sharpe delta versus B&H BTC:

| Experiment | Sharpe | Δ vs B&H | MaxDD | Trades | Verdict |
|---|---:|---:|---:|---:|---|
| SuperTrend baseline (reference) | +0.972 | +0.282 | −25.6% | 213 | Passes train gate, *not a v6 hypothesis* |
| H3 funding (filter) | +0.724 | +0.034 | −23.8% | 167 | FAIL |
| H3 funding (standalone) | +0.723 | +0.033 | −30.8% | 6 | FAIL (tiny sample) |
| H5 DXY (filter) | +0.441 | −0.250 | −31.7% | 122 | FAIL |
| H5 DXY (standalone) | +0.207 | −0.483 | −41.4% | 144 | FAIL |
| H1 Fear&Greed (standalone) | +0.048 | −0.642 | −37.7% | 8 | FAIL |
| H1 Fear&Greed (filter) | −0.215 | −0.905 | −30.2% | 65 | FAIL (worse than B&H) |

Walk-forward (Sharpe delta vs B&H BTC per window):

| Strategy | Δ W1 (2018–20) | Δ W2 (2020–23) | Δ W3 (2023–26) | Passes W3 (≥+0.15)? |
|---|---:|---:|---:|:---:|
| H5 DXY (filter) | +0.633 | +0.047 | −1.198 | No |
| H3 funding (standalone) | +0.572 | −0.476 | −0.877 | No |
| SuperTrend baseline | +0.500 | +0.555 | −0.457 | No |
| H3 funding (filter) | −0.123 | +0.296 | −0.353 | No |
| H1 F&G (standalone) | −0.400 | −1.043 | −0.742 | No |
| H5 DXY (standalone) | −0.305 | −0.706 | −0.720 | No |
| H1 F&G (filter) | −0.119 | −1.396 | −1.625 | No |

**No strategy passed the W3 gate.** Per the pre-registration, the OOS set was therefore never accessed. The pattern is diagnostic: several strategies show positive delta in W1/W2 (bull regimes) and collapse in W3 (the 2023–2026 consolidation) — the textbook signature of regime overfitting rather than persistent edge.

Notably, the "buy fear" hypothesis (H1) was the **worst** performer of all: buying at Fear & Greed ≤ 25 over a 1–4-week horizon repeatedly meant buying into bear markets with further to fall. The popular retail intuition is not merely weak here — it is *anti-predictive*.

---

## 5. Discussion: What We Learned

### 5.1 Validate the fill model before anything else

The most expensive lesson, learned mid-program, was that an apparent edge can be entirely an artifact of an optimistic execution assumption. Mean-reversion's Sharpe fell by 1.28 (from +0.72 to −0.56) when we moved from `same_close` to `next_open`. The corollary is a rule we now apply universally: **a backtest engine should default to `next_open`; `same_close` should require explicit justification.** Validating the fill model first would have saved roughly two weeks of work spent optimizing a signal that the realistic fill model immediately invalidated.

### 5.2 Buy-and-Hold BTC is an extraordinarily high bar

BTC's secular appreciation (Sharpe 0.81 over nine years) sets a benchmark that long-only retail strategies struggle to beat. The active strategies we tested were *better risk managers* (SuperTrend BTC: MaxDD −13.7% vs B&H's −83.9%) but *far worse return generators* (7× less absolute return). This is the **risk-adjusted-vs-absolute paradox**: for a participant with $100, a −84% drawdown is psychologically frightening but financially trivial ($84), while the return difference ($1,497 vs $366) is the thing that actually matters. For low capital, the active bot loses on the dimension that counts.

### 5.3 Lagging indicators classify regime but cannot filter trades

ADX is, by Wilder's construction, a lagging indicator (~28-bar warm-up). It can label a regime in hindsight but cannot filter trades in real time without timing damage: for trend-following, by the time ADX confirms a trend the move is already captured by faster indicators (the entry is late and gives back gains); for mean-reversion, regime-transition boundaries forced premature exits (58.9% of trades closed on a regime flag rather than a strategy signal). **Correct classification does not imply profitable filtering.**

### 5.4 Long-only mean-reversion has a structural negative bias in crypto

Buying the lower Bollinger band in a long-only spot account is "catching a falling knife" during bear markets. Without short-selling (a constitutional exclusion), mean-reversion is structurally asymmetric: it earns little in ranging markets and loses heavily in downtrends. BB-ETH would have been liquidated in 12 of 12 audit scenarios.

### 5.5 Edge concentrated in a single regime is not edge

Repeatedly, strategies with attractive aggregate Sharpe owed that performance to one bull window. v1's flagship E3b-5p showed W1 +1.62 / W2 +3.72 / **W3 −0.52**; v6's DXY filter showed W1 +0.633 / W2 +0.047 / **W3 −1.198**. Aggregate metrics *hide* regime concentration. Walk-forward exposes it. A strategy that only works in bull markets is a leveraged bet on the regime, not an edge.

### 5.6 Sample size discipline matters

Several attractive-looking variants rested on too few trades (e.g., an EMA 50/200 4h variant with Sharpe 1.00 on only 21 trades; v6's funding-standalone with 6 trades over eight years, and **zero** trades in the W3 window). A strategy that "does not fail" because it rarely trades provides no evidence. We held a ≥50-trade floor for statistical relevance and refused to promote anything below it.

### 5.7 Spot-only, long-only is a structural handicap for active return

The clearest meta-lesson: if the objective is *active return*, the spot-only, long-only constraint is a structural handicap, because it removes the tools (shorting, leverage, derivatives carry) that make many documented crypto edges work. If the objective is *capital preservation*, then B&H plus DCA is simpler and more effective than any bot we built. For our actual goal — modest return on low capital — DCA into BTC dominated every active strategy on cost, simplicity, operational risk, and (for $100) effective return.

### 5.8 The methodology paid for itself

Across six phases we lost **$0** of capital. The framework's value is concentrated in moments of refusal: refusing to deploy the fill-model artifact, refusing to relax a gate when a strategy "almost" passed, refusing to reuse a burned OOS set, refusing to access the v6 OOS set after the walk-forward gate failed. An honest research process that concludes "no edge" is worth more than an overfitted backtest that claims "Sharpe 2.0" and loses money live. Paying that lesson in backtest time rather than real capital is the entire point.

---

## 6. Robustness Checks (Response to Red-Team Critiques)

A skeptical reviewer can argue the negative result is an artifact of our design choices rather than a property of the market. We took five such critiques seriously and tested each directly. All experiments use a $1,000 base and the realistic `next_open` fill model; code is in `src/robustness/`.

### 6.1 Is it the cost model? (No.)

Critique: a 0.30% round-trip is pessimistic; BNB discounts and maker-only fills would rescue marginal strategies. We re-ran the key strategies under three cost regimes — baseline (0.30% round-trip), BNB-reduced (0.25%), and a deliberately unrealistic zero-cost upper bound.

| Strategy | Δ Sharpe vs B&H @ 0.30% | @ 0.25% | @ 0% (upper bound) |
|---|---:|---:|---:|
| SuperTrend baseline | +0.282 | +0.311 | +0.457 |
| h3 funding (filter) | +0.034 | +0.064 | +0.213 |
| h3 funding (standalone) | +0.033 | +0.034 | +0.040 |
| h5 DXY (filter) | −0.250 | −0.226 | −0.109 |
| h1 Fear&Greed (filter) | −0.905 | −0.889 | −0.807 |

No negative-Sharpe strategy crosses into positive edge even at **zero cost**. The funding-filter rises toward the in-sample gate at zero cost but still fails walk-forward W3 (its decisive test). Conclusion: the binding constraint is **signal quality, not transaction cost**. The reviewer's point holds only for high-frequency strategies we did not pursue — and even there, a maker-only backtest without modeling fill uncertainty (Section 4.5) would itself be a new fill artifact.

### 6.2 Is it the 4h timeframe? (No.)

Critique: 4h is "no man's land" — too slow for microstructure, too fast for macro-trend. We resampled to daily and re-ran SuperTrend.

| Variant | Sharpe | Δ vs B&H | MaxDD | Final ($1k) | Trades |
|---|---:|---:|---:|---:|---:|
| B&H BTC | +0.690 | — | −77.0% | $6,734 | 1 |
| SuperTrend 4h | +0.972 | +0.282 | −25.6% | $3,663 | 213 |
| SuperTrend 1d | +0.911 | +0.221 | −25.4% | $4,130 | 39 |

Daily does not beat 4h on Sharpe, and neither clears the 1.2 gate. (Daily is more capital-efficient — fewer trades, similar Sharpe — but that does not change the verdict.) The sub-minute microstructure regime the reviewer alludes to is the domain of HFT, where a retail participant does not compete; pursuing it would contradict the reviewer's own critique 6.4.

### 6.3 Is it the start date? (Partly — and it cuts against the reviewer.)

Critique: B&H's 2017 start captures BTC's institutional-adoption beta; starting in a bear-heavy year would make active strategies look great. We ran B&H and SuperTrend from five start dates.

| Start | B&H Sharpe | B&H MaxDD | SuperTrend Sharpe | ST MaxDD | Δ Sharpe |
|---|---:|---:|---:|---:|---:|
| 2017-08 | +0.809 | −83.9% | +0.980 | −25.6% | +0.170 |
| 2018-01 | +0.632 | −81.4% | +0.893 | −25.6% | +0.261 |
| 2020-01 | +0.901 | −77.0% | +0.999 | −25.6% | +0.098 |
| 2021-11 | +0.320 | −77.0% | +0.274 | −23.8% | **−0.046** |
| 2022-01 | +0.435 | −67.2% | +0.323 | −20.9% | **−0.112** |

The reviewer's prediction is **empirically wrong** on a risk-adjusted basis: starting from the 2021 top or 2022, SuperTrend *underperforms* B&H on Sharpe, because a long-only trend-follower misses the recovery it cannot anticipate. The active strategies win consistently only on **drawdown** (avg −24% vs −77%), never enough to clear the 1.2 gate in any window. The benchmark is start-date sensitive, but not in the direction the critique assumed.

### 6.4 Is it the large-cap universe? (No — survivorship makes this the strongest test.)

Critique: edge lives in inefficient mid-cap altcoins, not hyper-arbitraged majors. We ran SuperTrend on seven liquid mid-caps (ADA, AVAX, LINK, DOT, ATOM, LTC, DOGE), with widened slippage (0.10%/side) for thinner books.

| Pair | B&H Sharpe | SuperTrend Sharpe | ST MaxDD | Δ vs B&H | Gate (≥1.2) |
|---|---:|---:|---:|---:|:---:|
| ADA | +0.491 | +0.554 | −45.9% | +0.064 | fail |
| AVAX | +0.684 | +0.960 | −41.2% | +0.276 | fail |
| LINK | +0.912 | +0.683 | −50.4% | −0.230 | fail |
| DOT | +0.356 | +0.187 | −59.1% | −0.170 | fail |
| ATOM | +0.454 | +0.291 | −57.1% | −0.163 | fail |
| LTC | +0.265 | +0.266 | −45.4% | +0.001 | fail |
| DOGE | +0.959 | +0.726 | −61.1% | −0.233 | fail |

SuperTrend clears the 1.2 gate in **0 of 7** pairs (mean Sharpe +0.524, worse than the majors). Crucially, this is a **survivorship-biased upper bound**: every pair here is still listed in 2026; the hundreds of delisted/dead mid-caps are absent (Binance's public API does not serve them). Since even the best-case survivor universe fails the gate, the conclusion is *robust* — a bias-free universe would only lower these numbers. A positive result here would have demanded a point-in-time universe with delisted pairs; a negative result does not.

### 6.5 Is it the long-only constraint? (No — and this was the sharpest critique.)

Critique: prohibiting short-selling in a market with 80% bear markets ties one hand behind your back; modern retail uses perpetual futures. We built a 1x long/short perpetual engine charging the **real historical 8h funding rate**, and ran SuperTrend (its SELL signals now open shorts) over the funding-available window (2019-09 onward).

| Strategy | Sharpe | Δ vs B&H | MaxDD | Final ($1k) |
|---|---:|---:|---:|---:|
| B&H BTC | +0.784 | — | −77.0% | $6,722 |
| SuperTrend long-only (spot) | +0.908 | +0.125 | −25.6% | $2,545 |
| SuperTrend long/short (perp 1x) | +0.524 | −0.259 | −23.6% | $1,876 |

Adding the ability to short **lowers** SuperTrend's Sharpe (0.908 → 0.524 on BTC; 0.957 → 0.535 on ETH). Two forces explain it: the short side of a trend-following signal loses money in a secular bull (it shorts dips that recover), and the funding cost (longs paid ≈+11.9% annualized over the sample) is a persistent drag. The long-only constraint was **not** the binding limitation for this strategy family.

*Methodological note:* this experiment first reported a Sharpe of **2.7** — physically inconsistent with a −66% drawdown and a final equity *below* the long-only variant. We treated the too-good number as a bug (per our own red-flag rule), found a double-counting error in the perpetual mark-to-market, fixed it, and re-ran. The corrected result is above. This is the discipline of Section 5.1 operating in real time.

### 6.6 Is the active edge statistically significant? (No.)

A reviewer rightly asked whether SuperTrend's Sharpe advantage over Buy-and-Hold (0.972 vs 0.690 on the full BTC sample) is distinguishable from noise, or just sampling luck. We answer with a **moving-block bootstrap** (block size 30 bars, 5,000 resamples, paired so cross-strategy correlation is preserved), which respects the autocorrelation and volatility clustering that an i.i.d. bootstrap would ignore.

<pre style="white-space:pre-wrap">
                 Sharpe   95% bootstrap CI
B&H BTC          +0.690   [+0.012, +1.391]
SuperTrend       +0.972   [+0.239, +1.671]
Difference       +0.282   [-0.298, +0.778]   <- includes 0
one-sided p-value  P(diff <= 0) = 0.189
</pre>

The 95% confidence interval for the difference **includes zero** (p = 0.19). With 9.25 years of 4h data, the sampling error of the Sharpe ratio is wide enough that SuperTrend's apparent edge over Buy-and-Hold is **not statistically significant**. Even the single best active strategy in the entire program cannot be said, with confidence, to beat passive holding. This strengthens rather than weakens the paper's conclusion — and it is a concrete instance of the Deflated-Sharpe warning (Section 1.5): a positive point estimate is not an edge.

### 6.7 What the robustness checks do and do not establish

They establish that the negative result is **not** an artifact of cost, timeframe, start date, asset universe, or directionality, for the *strategy families tested*. They do **not** establish that no long/short strategy can work — only that mechanically shorting a long-only trend signal does not. Nor do they cover leveraged carry, options, or ML. The envelope is wider after Section 6, but it is still an envelope.

---

## 7. Threats to Validity

We hold ourselves to the same scrutiny we applied to the strategies.

- **Single-market generality.** Our conclusions are specific to Binance Spot, long-only, retail costs, 2017–2026. They do not generalize to futures, other venues, or shorter horizons.
- **Strategy-space coverage.** We tested a finite (if broad) set of classical signals plus three external sources. The absence of edge in this set does not prove its absence everywhere; it constrains where one should look (Section 7).
- **Parameter-space coverage.** Although we ran a 144-combination sweep and ±20% sensitivity checks, the parameter space is effectively infinite. We mitigate this with pre-registration (limiting post-hoc fishing) but cannot eliminate it.
- **Survivorship in the data.** Our five pairs are survivors. Including delisted/dead pairs would, if anything, *weaken* active-strategy results, not strengthen them, so this bias is conservative with respect to our negative conclusion.
- **Multiple testing in v1.** v1's 20+ unregistered experiments inflate false-positive risk; this is exactly why the eventual winner failed OOS, and exactly why we adopted pre-registration thereafter.
- **External-signal lag assumptions (v6).** We modeled conservative publication lags (e.g., 4h for F&G, 2 days for DXY). More aggressive (less realistic) lags would *improve* backtest results, so our assumptions are conservative.
- **Regime sample.** The 2017–2026 record contains only a handful of full bull/bear cycles. Out-of-sample regime risk remains, by definition, unquantifiable until it arrives.

---

## 8. Conclusion and Future Directions

Under a spot-only, long-only, realistic-cost, retail-capital envelope, and across six pre-registered phases on 9.25 years of data, **we found no simple algorithmic strategy with a persistent, exploitable edge that beats Buy-and-Hold BTC out-of-sample.** The single apparent edge dissolved under a realistic fill model; the single in-sample ensemble winner collapsed out-of-sample; and a final battery of non-technical signals (sentiment, funding, macro) failed walk-forward validation entirely.

For the stated goal — growing modest capital — the evidence points to **dollar-cost averaging into BTC** as the dominant choice: comparable or better effective return at low capital, with none of the operational risk, infrastructure cost, or behavioral burden of an active bot.

This is not a counsel of despair. It delimits where edge is *not* and, by implication, where it might be. Plausible directions, each requiring a different constraint envelope and its own pre-registered study, include: **perpetual-futures funding/basis carry** (which has documented structural drivers — note that BTC perpetual funding averaged +11.86% annualized over our sample, a real and persistent asymmetry); **cross-exchange or triangular arbitrage**; **volatility strategies via options**; and **machine-learning approaches** with data and latency beyond a typical retail participant. Each of these violates one or more of our self-imposed constraints and would constitute a *different project*, not a continuation of this one.

The most durable output of Chocotrader is not a strategy — it is a **method**. Pre-registration, OOS sealing, walk-forward as an early-warning system, a realistic fill model by default, and gates written before results existed, together prevented the single most expensive error in retail trading: deploying real capital on an illusory edge. We commend this framework, more than any individual result, to others.

---

## 9. Reproducibility and Artifacts

In the spirit of the result, we intend to publish the full apparatus so others can reproduce, criticize, and extend it:

- **Data fetchers** for all external series (Fear & Greed, Binance funding rate, FRED DXY), producing the exact Parquet datasets used here.
- **Signal generators** as pure, unit-tested functions, including the alignment layer that merges daily/8h external series into 4h bars *without look-ahead* (a common and silent source of leakage).
- **Backtest engine** with the `next_open` fill model, explicit cost model, and standardized metrics (Sharpe, Sortino, MaxDD, profit factor, Calmar).
- **Walk-forward runner** with automated gate enforcement.
- **Full result logs** (`run_log.jsonl`), per-experiment reports, and the sealed pre-registration documents with their commit hashes.
- **Governance artifacts**: the constitution, the architecture-decision records (ADRs), and the pre-registration templates.

All backtests in this paper are reproducible from the committed code and the regenerable datasets. The out-of-sample dataset reserved for the final phase remains sealed and unused. The bootstrap significance test of Section 6.6 is in `src/robustness/significance.py`.

---

## References

- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). *Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance.* Notices of the AMS.
- Bailey, D. H., & López de Prado, M. (2014). *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality.* Journal of Portfolio Management. SSRN 2460551.
- Fama, E. F. (1970). *Efficient Capital Markets: A Review of Theory and Empirical Work.* Journal of Finance, 25(2).
- Jegadeesh, N., & Titman, S. (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1).
- Khuntia, S., & Pattanayak, J. K. (2018). *Adaptive Market Hypothesis and Evolving Predictability of Bitcoin.* Economics Letters, 167.
- Liu, Y., & Tsyvinski, A. (2021). *Risks and Returns of Cryptocurrency.* Review of Financial Studies, 34(6).
- Lo, A. W. (2004). *The Adaptive Markets Hypothesis.* Journal of Portfolio Management, 30(5).
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). *Time Series Momentum.* Journal of Financial Economics, 104(2).
- Politis, D. N., & Romano, J. P. (1994). *The Stationary Bootstrap.* Journal of the American Statistical Association, 89(428).
- Tran, V. L., & Leirvik, T. (2020). *Efficiency in the Markets of Crypto-currencies.* Finance Research Letters, 35.

*(Citations are provided for scholarly context. This is a working paper; quantitative claims rest on the reproducible code and data, not on the cited works.)*

---

## Acknowledgments

This was a self-funded, single-author research program. No external capital was at risk at any point. The author thanks the discipline of writing things down before looking at the data — it is the only reason the conclusions can be trusted.

## Data and Code Availability

A public repository containing the simulators, data fetchers, generated datasets, and result logs is planned as a companion to this paper. Until then, all numerical results are documented in the project's internal research reports, from which every table above is drawn.

## A Note on Interpretation

No table in this paper should be read as financial advice. Past performance — including the Buy-and-Hold figures — does not predict future returns; BTC's 2017–2026 appreciation may not recur. The central message is methodological: **test honestly, benchmark ruthlessly, and treat "no edge" as a valid and valuable result.**
