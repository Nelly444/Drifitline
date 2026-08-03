from datetime import date

import pytest

from app.services.forecasting import (
    ETS_MIN_HISTORY,
    expected_next_date,
    forecast_amount,
    score,
)


def test_forecast_amount_uses_mean_below_ets_threshold():
    history = [10.0, 10.0, 10.0]
    assert len(history) < ETS_MIN_HISTORY
    expected, std = forecast_amount(history)
    assert expected == 10.0
    assert std > 0


def test_forecast_amount_uses_ets_above_threshold():
    history = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    assert len(history) >= ETS_MIN_HISTORY
    expected, std = forecast_amount(history)
    assert expected == pytest.approx(10.0, abs=0.5)


def test_score_flags_large_deviation_as_drift():
    deviation_pct, is_drift = score(actual_amount=19.99, expected_amount=15.99, std_used=0.1)
    assert is_drift is True
    assert deviation_pct > 0


def test_score_does_not_flag_small_deviation():
    deviation_pct, is_drift = score(actual_amount=16.10, expected_amount=15.99, std_used=1.0)
    assert is_drift is False


def test_score_zero_variance_history_does_not_explode():
    deviation_pct, is_drift = score(actual_amount=20.0, expected_amount=15.99, std_used=0.32)
    assert is_drift is True


def test_expected_next_date_uses_median_interval():
    dates = [date(2024, 1, 1), date(2024, 1, 31), date(2024, 3, 1)]
    next_date = expected_next_date(dates)
    assert next_date > dates[-1]
