# Stats 237 — Course Story (v0.5 scaffold)

This document is meant to become the **narrative spine** of the course, where each concept is anchored by:

1. **Lectures** (slides; optionally handwritten notes)
2. **Worked problems** (HW and finals)
3. **Code artifacts** (quantlib functions + tests)

## 1. Probability primitives for pricing

- Random variables, distributions, expectation
- Conditional expectation (tower property; iterated conditioning)
- Martingales (where applicable)

**Key functions**
- `stats237_quantlib.probability.conditional.condexp_discrete`
- `stats237_quantlib.probability.conditional.tower_property_check`

**Problems**
- See `problem_bank/problems.json` tagged `conditional_expectation`

## 2. No-arbitrage, replication, and pricing

- Payoff engineering: spreads, straddles/strangles
- Bounds and monotonicity / convexity arguments
- Put-call parity

**Key functions**
- `stats237_quantlib.pricing.no_arb.bounds_european_call_put`
- `stats237_quantlib.pricing.no_arb.put_call_parity_residual`

## 3. Binomial model (CRR) and American exercise

- Replicating portfolio (delta/bond)
- Risk-neutral probability
- Pricing European and American claims

**Key functions**
- `stats237_quantlib.pricing.binomial.crr_european`
- `stats237_quantlib.pricing.binomial.crr_american`
- `stats237_quantlib.pricing.binomial.one_step_replication`

## 4. Black–Scholes and Greeks

- Lognormal model
- Closed-form prices
- Greeks and hedging

**Key functions**
- `stats237_quantlib.pricing.black_scholes.bs_call`, `bs_put`
- `stats237_quantlib.pricing.black_scholes.greeks_call_put`
- `stats237_quantlib.pricing.black_scholes.implied_vol`

## 5. Monte Carlo for exotics (basket / Asian)

- Estimator, standard error and confidence intervals
- Variance reduction (v0.6)
- Control variates (v0.6)

**Key functions**
- `stats237_quantlib.mc.basket.basket_call_mc`

---

## Appendix: Coverage

See `coverage/coverage_report.md`.
