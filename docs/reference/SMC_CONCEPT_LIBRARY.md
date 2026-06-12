# SMC Concept Library v1.0
**Project**: AG-auto-trade
**Purpose**: Centralized, version-controlled library of Smart Money Concepts (SMC) used by all alpha strategies.
**Philosophy**: Every concept must be precisely defined, testable, and validated through the gate before use in live trading.

---

## 1. Core SMC Concepts (Priority Order)

### 1.1 Order Block (OB)
**Definition**: Last opposing candle before a strong impulsive move that breaks structure.
- **Bullish OB**: Last bearish candle before bullish displacement that breaks previous high.
- **Bearish OB**: Last bullish candle before bearish displacement that breaks previous low.

**Detection Rules**:
- Identify displacement candle (body > 1.5× average ATR)
- Locate the last opposing candle within the swing
- Validate with volume or momentum confirmation (optional)

**Implementation Fields**:
```python
class OrderBlock:
    direction: Literal["bullish", "bearish"]
    high: float
    low: float
    timestamp: datetime
    strength: float          # 0-1 score based on displacement size + volume
    mitigated: bool = False
```

### 1.2 Fair Value Gap (FVG) / Imbalance
**Definition**: 3-candle pattern where candle 3's low is above candle 1's high (bullish) or candle 3's high is below candle 1's low (bearish).

**Types**:
- Bullish FVG
- Bearish FVG
- Premium/Discount zones (when FVG occurs in premium/discount array)

**Detection Rules**:
- Gap size must be ≥ 0.5× ATR(14)
- Prefer FVGs that align with higher-timeframe bias

### 1.3 Liquidity
**Types**:
- **Equal Highs/Lows** (liquidity pools)
- **Stop Hunts** above/below obvious highs/lows
- **Inducement** (fake breakout of structure before real move)

**Detection**:
- Cluster of swing highs/lows within 0.3× ATR
- Sudden wick beyond liquidity level followed by reversal

### 1.4 Break of Structure (BOS) & Change of Character (CHOCH)
- **BOS**: Price breaks previous swing high/low in the direction of the trend.
- **CHOCH**: First sign of potential trend reversal (break of structure in opposite direction).

**Usage**: Primary trend filter. Only take trades in direction of higher-timeframe BOS.

### 1.5 Displacement
Strong impulsive move (large candle body + momentum) that confirms institutional activity.

**Rule**: Displacement candle body must be ≥ 1.8× average ATR(14) of the last 20 candles.

---

## 2. Multi-Timeframe Confluence Matrix

| Timeframe | Role in Strategy                  | Required for Trade? |
|-----------|-----------------------------------|---------------------|
| Weekly    | Macro bias                        | Recommended         |
| Daily     | Major structure & key levels      | Yes                 |
| H4        | Intermediate structure            | Yes                 |
| H1        | Entry timeframe (primary)         | Yes                 |
| M15       | Precise entry & FVG/OB refinement | Yes                 |
| M5        | Scalping / confirmation           | Optional            |

**Rule**: Trade only when H4 + H1 + M15 are in confluence.

---

## 3. Library Structure (Recommended Folder Layout)

```
ag/alpha/a1_smc_momentum/
├── detectors/
│   ├── order_block.py
│   ├── fvg.py
│   ├── liquidity.py
│   └── bos_choch.py
├── filters/
│   ├── session_filter.py
│   ├── regime_filter.py
│   └── premium_discount.py
└── confluence/
    ├── mtf_confluence.py
    └── strength_scorer.py
tests/unit/smc/
    ├── test_order_block.py
    ├── test_fvg.py
    └── synthetic_scenarios/
```

Note: Production SMC code lives in `ag/alpha/a1_smc_momentum/`, NOT `research_archive/`.
Research archive is for validated-negative results only.

---

## 4. Implementation Guidelines

1. Every concept class must expose:
   - `detect()` method returning list of detected objects
   - `strength_score()` method (0–1)
   - `is_mitigated()` method

2. All detectors must be unit-tested with both real historical data and synthetic scenarios.

3. Concepts are **immutable** once created. Mitigation status is tracked separately.

4. Version every major change to detection logic (use semantic versioning).

---

## 5. Integration with Validation Gate

- Each new SMC concept or filter must pass the **SMC Concept Validation Checklist** before being added to any alpha strategy.
- The `smc-filter-builder` skill will be the primary tool for adding and reviewing new concepts.

---

## 6. Future Concepts (Backlog)

- Breaker Blocks
- Mitigation Blocks
- Supply & Demand Zones
- Turtle Soup (failed breakout reversal)
- Silver Bullet (specific time-based setups)

---

**Status**: v1.0 baseline — ready for implementation in Phase 1.

This library will become the single source of truth for all SMC logic in the project.
