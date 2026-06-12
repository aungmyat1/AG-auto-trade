# SMC Concept Validation Checklist

Use this checklist before adding any new SMC concept or filter to the library or any alpha strategy.

## 1. Definition Clarity
- [ ] Precise textual definition written
- [ ] Visual examples (charts) attached
- [ ] Edge cases documented

## 2. Detection Logic
- [ ] Deterministic rules defined (no ambiguity)
- [ ] Parameters exposed (ATR multiplier, lookback, etc.)
- [ ] Strength scoring function implemented

## 3. Test Coverage
- [ ] Unit tests written (`test_<concept>.py`)
- [ ] Synthetic scenario tests created
- [ ] Historical data backtest on ≥ 3 instruments

## 4. Integration
- [ ] Compatible with existing concepts (no conflicts)
- [ ] Multi-timeframe support verified
- [ ] Mitigation tracking implemented

## 5. Gate Readiness
- [ ] Passes `strategy-validator` skill review
- [ ] Documented in `SMC_CONCEPTS_REFERENCE.md`
- [ ] Version bumped in library

Only concepts that pass **all** items above may be merged into the main library.
