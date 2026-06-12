# SMC Implementation Skeletons

This folder contains production-ready starter code for the core SMC concepts defined in `SMC_CONCEPT_LIBRARY.md`.

## Files

| File                        | Concept                  | Status     |
|----------------------------|--------------------------|------------|
| `order_block_detector.py`  | Order Block              | Ready      |
| `fvg_detector.py`          | Fair Value Gap           | Ready      |
| `liquidity_detector.py`    | Liquidity Pools          | Ready      |
| `bos_choch_detector.py`    | BOS / CHOCH              | Ready      |

## Usage Pattern

All detectors follow the same interface:

```python
detector = SomeDetector(...)
results = detector.detect(df)   # returns List[Concept]
```

Each result object contains:
- `direction`
- price levels
- `timestamp`
- `strength` or `size_atr`
- `mitigated` flag

## Actual Implementation Location

Per the v4 architecture, production SMC detector code lives in:
`ag/alpha/a1_smc_momentum/detectors/`

NOT in research_archive/ — that folder is for validated-negative results only.

## Next Steps

1. Add unit tests in `tests/unit/smc/`
2. Create synthetic scenario generators
3. Integrate with `smc-filter-builder` skill
4. Run through Validation Gate Checklist

**Version**: 1.0 — Baseline skeletons for Phase 1 development.
