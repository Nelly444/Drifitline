from collections import Counter
from datetime import date, timedelta

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from app.services.clustering import EPS, MIN_SAMPLES, build_group_features, resolve_group_links


class FakeTxn:
    def __init__(self, posted_date, amount, subscription_id=None):
        self.posted_date = posted_date
        self.amount = amount
        self.subscription_id = subscription_id


def test_recurring_pattern_forms_one_cluster_separate_from_noise():
    # Mirrors backend/scripts/derisk_dbscan.py's empirically-validated toy set: a
    # single interleaved one-off charge contaminates its immediate neighbor's computed
    # interval (a known limitation of "interval since previous txn"), so a handful of
    # recurring points near the noise point can end up unclustered too - that's expected,
    # not a bug. The bar here is: the big outlier is noise, and most of the recurring
    # pattern still lands in one shared cluster.
    start = date(2024, 1, 1)
    recurring = [FakeTxn(start + timedelta(days=30 * i), 15.99) for i in range(20)]
    noise = [FakeTxn(start + timedelta(days=15), 250.00)]
    txns = sorted(recurring + noise, key=lambda t: t.posted_date)

    features = build_group_features(txns)
    scaled = StandardScaler().fit_transform(features)
    labels = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES).fit_predict(scaled)

    noise_index = txns.index(noise[0])
    assert labels[noise_index] == -1

    recurring_labels = [labels[i] for i in range(len(txns)) if i != noise_index]
    (main_cluster, main_count), *_ = Counter(recurring_labels).most_common(1)
    assert main_cluster != -1
    assert main_count >= len(recurring) * 0.8


def test_first_transaction_imputes_median_interval_not_zero():
    txns = [
        FakeTxn(date(2024, 1, 1), 10.0),
        FakeTxn(date(2024, 1, 31), 10.0),
        FakeTxn(date(2024, 3, 1), 10.0),
    ]
    features = build_group_features(txns)
    assert features[0][1] == features[1][1]  # first point imputes the median gap
    assert features[0][1] > 0


def test_resolve_group_links_returns_none_when_no_existing_subscription():
    txns = [FakeTxn(date(2024, 1, 1), 15.99)]

    resolved_id, unlinked = resolve_group_links(txns, existing_subscription_id=None)

    assert resolved_id is None
    assert unlinked == []


def test_resolve_group_links_reuses_existing_subscription_for_unlinked_txns():
    already_linked = FakeTxn(date(2024, 1, 1), 15.99, subscription_id=7)
    new_txn = FakeTxn(date(2024, 2, 1), 45.00, subscription_id=None)
    txns = [already_linked, new_txn]

    resolved_id, unlinked = resolve_group_links(txns, existing_subscription_id=7)

    assert resolved_id == 7
    assert unlinked == [new_txn]
