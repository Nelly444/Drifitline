from datetime import date, timedelta

from app.services.scoring import MIN_HISTORY, score_subscription_history


class FakeTxn:
    def __init__(self, posted_date, amount):
        self.posted_date = posted_date
        self.amount = amount
        self.expected_amount = None
        self.deviation_pct = None
        self.is_drift = False


def test_first_min_history_transactions_stay_unscored():
    start = date(2024, 1, 1)
    txns = [FakeTxn(start + timedelta(days=30 * i), 15.99) for i in range(6)]

    score_subscription_history(txns)

    for txn in txns[:MIN_HISTORY]:
        assert txn.expected_amount is None
        assert txn.is_drift is False
    for txn in txns[MIN_HISTORY:]:
        assert txn.expected_amount is not None


def test_price_hike_gets_flagged_as_drift():
    start = date(2024, 1, 1)
    txns = [FakeTxn(start + timedelta(days=30 * i), 15.99) for i in range(6)]
    txns.append(FakeTxn(start + timedelta(days=30 * 6), 45.00))  # a clear price hike

    score_subscription_history(txns)

    assert txns[-1].is_drift is True
    assert txns[-1].deviation_pct > 0


def test_returns_sane_forward_forecast():
    start = date(2024, 1, 1)
    txns = [FakeTxn(start + timedelta(days=30 * i), 15.99) for i in range(6)]

    forecast_next_amount, forecast_date = score_subscription_history(txns)

    assert forecast_next_amount == 15.99
    assert forecast_date > txns[-1].posted_date
