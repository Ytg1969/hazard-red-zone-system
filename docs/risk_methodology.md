# Risk Methodology

## Default score

All factors are normalized to 0–100.

`Risk = 0.35 × Hazard + 0.25 × Exposure + 0.25 × Vulnerability + 0.15 × AccessibilityDifficulty`

## Classes

- 0–29: LOW
- 30–49: MODERATE
- 50–69: HIGH
- 70–100: CRITICAL

## Scenario weights

Scenario Studio may change weights only when:
- the four weights sum to 1.0;
- the default recommended weights remain available;
- the UI reports how classifications and affected population change;
- the app labels results as scenario analysis, not official orders.

## ML

ML is an optional validation layer. Do not report ML accuracy unless labels come from credible historical observations and the train/test split avoids leakage.
