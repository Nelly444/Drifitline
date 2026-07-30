"""
Synthetic ground-truth evaluation harness (PRD: "Honesty in evaluation" - no public
labeled dataset exists for "is this a forgotten subscription", so this fabricates one
with known labels). Runs entirely in-memory against the real merchant_matching +
clustering pipeline; never touches the actual `transactions` table.
"""

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

from app.services.clustering import EPS, MIN_GROUP_SIZE, MIN_SAMPLES, build_group_features
from app.services.merchant_matching import normalize_merchants
from app.services.noise import inject_noise

SUBSCRIPTION_MERCHANTS = [
    "Netflix Inc", "Spotify Inc", "Adobe Inc", "New York Times Inc", "Planet Fitness Inc", "Dropbox Inc",
]
ONE_OFF_MERCHANTS = ["Target", "Starbucks", "Amazon", "Uber", "Chipotle"]


@dataclass
class SyntheticTxn:
    posted_date: date
    amount: float
    raw_merchant_name: str
    true_subscription_id: int | None


def generate_dataset(rng: random.Random, n_subscriptions=6, occurrences_per_sub=10, n_noise=40) -> list[SyntheticTxn]:
    start = date(2023, 1, 1)
    txns: list[SyntheticTxn] = []
    horizon_days = 0

    for sub_id, merchant in enumerate(SUBSCRIPTION_MERCHANTS[:n_subscriptions]):
        base_amount = rng.choice([9.99, 12.99, 15.99, 19.99, 49.99])
        interval = rng.choice([28, 30, 31])
        horizon_days = max(horizon_days, interval * occurrences_per_sub)

        for i in range(occurrences_per_sub):
            jitter_days = rng.randint(-2, 2)
            txn_date = start + timedelta(days=interval * i + jitter_days)
            amount = base_amount
            if i == occurrences_per_sub - 1:
                amount = round(base_amount * 1.15, 2)  # late price hike, still the same subscription
            raw_name = inject_noise(merchant, rng=rng)
            txns.append(SyntheticTxn(txn_date, amount, raw_name, sub_id))

    for _ in range(n_noise):
        merchant = rng.choice(ONE_OFF_MERCHANTS)
        txn_date = start + timedelta(days=rng.randint(0, horizon_days))
        amount = round(rng.uniform(5, 200), 2)
        raw_name = inject_noise(merchant, rng=rng)
        txns.append(SyntheticTxn(txn_date, amount, raw_name, None))

    return txns


def run_pipeline(txns: list[SyntheticTxn]) -> dict[int, tuple | None]:
    mapping = normalize_merchants([t.raw_merchant_name for t in txns])

    groups: dict[str, list[SyntheticTxn]] = defaultdict(list)
    for t in txns:
        groups[mapping[t.raw_merchant_name]].append(t)

    eligible = {
        name: sorted(g, key=lambda t: t.posted_date)
        for name, g in groups.items()
        if len(g) >= MIN_GROUP_SIZE
    }
    features = {name: build_group_features(g) for name, g in eligible.items()}

    predicted: dict[int, tuple | None] = {id(t): None for t in txns}
    if features:
        scaler = StandardScaler().fit(np.vstack(list(features.values())))
        for name, sorted_txns in eligible.items():
            scaled = scaler.transform(features[name])
            labels = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES).fit_predict(scaled)
            for t, label in zip(sorted_txns, labels):
                predicted[id(t)] = None if label == -1 else (name, int(label))

    return predicted


def evaluate(txns: list[SyntheticTxn], predicted: dict[int, tuple | None]) -> dict:
    label_ids: dict[tuple, int] = {}

    def encode(key) -> int:
        return label_ids.setdefault(key, len(label_ids))

    true_labels = [encode(("true", t.true_subscription_id if t.true_subscription_id is not None else id(t))) for t in txns]
    pred_labels = [encode(("pred", predicted[id(t)] if predicted[id(t)] is not None else id(t))) for t in txns]
    ari = adjusted_rand_score(true_labels, pred_labels)

    true_groups: dict[int, list[SyntheticTxn]] = defaultdict(list)
    for t in txns:
        if t.true_subscription_id is not None:
            true_groups[t.true_subscription_id].append(t)

    correctly_identified = 0
    for members in true_groups.values():
        pred_keys = [predicted[id(t)] for t in members]
        top_key, top_count = Counter(pred_keys).most_common(1)[0]
        if top_key is not None and top_count / len(members) >= 0.8:
            correctly_identified += 1

    pred_to_true_ids: dict[tuple, set] = defaultdict(set)
    for t in txns:
        key = predicted[id(t)]
        if key is not None and t.true_subscription_id is not None:
            pred_to_true_ids[key].add(t.true_subscription_id)
    false_merges = sum(1 for true_ids in pred_to_true_ids.values() if len(true_ids) > 1)

    return {
        "adjusted_rand_index": ari,
        "true_subscriptions": len(true_groups),
        "correctly_identified": correctly_identified,
        "false_merges": false_merges,
    }


def main():
    rng = random.Random(7)
    txns = generate_dataset(rng)
    predicted = run_pipeline(txns)
    report = evaluate(txns, predicted)

    print("=== Synthetic ground-truth evaluation (NOT real-world validated - see PRD Known Limitations) ===")
    print(f"Adjusted Rand Index: {report['adjusted_rand_index']:.3f}")
    print(f"True subscriptions correctly identified as one cluster: {report['correctly_identified']} / {report['true_subscriptions']}")
    print(f"Predicted clusters that wrongly merged 2+ distinct true subscriptions: {report['false_merges']}")


if __name__ == "__main__":
    main()
