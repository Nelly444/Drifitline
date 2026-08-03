from datetime import date, timedelta

import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

np.seterr(divide="ignore", invalid="ignore")

ETS_MIN_HISTORY = 5
Z_THRESHOLD = 2.0
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
