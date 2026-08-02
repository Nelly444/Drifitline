from datetime import date, timedelta

from app.services.scoring import MIN_HISTORY, newly_flagged_since, score_subscription_history


class FakeTxn:
    def __init__(self, posted_date, amount, id=None):
        self.id = id
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


def test_newly_flagged_since_includes_false_to_true_transition():
    txns = [FakeTxn(date(2024, 1, 1), 45.00, id=1)]
    txns[0].is_drift = True

    result = newly_flagged_since({1: False}, txns)

    assert result == [txns[0]]


def test_newly_flagged_since_excludes_already_flagged():
    txns = [FakeTxn(date(2024, 1, 1), 45.00, id=1)]
    txns[0].is_drift = True

    result = newly_flagged_since({1: True}, txns)

    assert result == []


def test_newly_flagged_since_includes_transaction_absent_from_before_snapshot():
    txns = [FakeTxn(date(2024, 1, 1), 45.00, id=99)]
    txns[0].is_drift = True

    result = newly_flagged_since({}, txns)

    assert result == [txns[0]]


def test_newly_flagged_since_excludes_non_drift_transactions():
    txns = [FakeTxn(date(2024, 1, 1), 15.99, id=1)]
    txns[0].is_drift = False

    result = newly_flagged_since({1: False}, txns)

    assert result == []
