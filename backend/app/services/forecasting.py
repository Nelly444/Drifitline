from datetime import date, timedelta

import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

# A perfectly flat amount history (extremely common - e.g. Netflix always $15.99) gives
# statsmodels zero SSE, which trips numpy floating-point warnings in its own AIC/BIC
# bookkeeping. These are numpy FPE warnings (governed by np.seterr, not Python's
# `warnings` module, and a context-scoped np.errstate around just the .fit() call was
# unreliable here) and don't affect the point forecast itself.
np.seterr(divide="ignore", invalid="ignore")

# Roadmap's own sanctioned fallback: ETS is overkill below this many points, use the mean.
ETS_MIN_HISTORY = 5

# ~95% one-sided; revisited against synthetic_eval.py's precision/recall, not re-derisked
# from scratch the way DBSCAN's eps was, since z-score thresholds are a standard convention.
Z_THRESHOLD = 2.0

# Floors std at 2% of the expected amount so an identical-amount history (std=0) doesn't
# produce a divide-by-zero/infinite z-score the moment a real deviation shows up.
STD_FLOOR_PCT = 0.02


def forecast_amount(history: list[float]) -> tuple[float, float]:
    if len(history) >= ETS_MIN_HISTORY:
        model = SimpleExpSmoothing(np.array(history), initialization_method="estimated").fit()
        expected = float(model.forecast(1)[0])
    else:
        expected = float(np.mean(history))

    std = float(np.std(history, ddof=1)) if len(history) >= 2 else 0.0
    std_used = max(std, STD_FLOOR_PCT * abs(expected))
    return expected, std_used


def expected_next_date(history_dates: list[date]) -> date:
    intervals = [(history_dates[i] - history_dates[i - 1]).days for i in range(1, len(history_dates))]
    median_interval = np.median(intervals) if intervals else 0.0
    return history_dates[-1] + timedelta(days=float(median_interval))


def score(actual_amount: float, expected_amount: float, std_used: float) -> tuple[float, bool]:
    deviation_pct = (actual_amount - expected_amount) / expected_amount * 100
    z_score = (actual_amount - expected_amount) / std_used
    is_drift = abs(z_score) > Z_THRESHOLD
    return deviation_pct, is_drift
