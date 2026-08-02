from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.services.pipeline import run_pipeline


class FakeMerchant:
    def __init__(self, id, normalized_name):
        self.id = id
        self.normalized_name = normalized_name


class FakePlaidItem:
    def __init__(self, id):
        self.id = id


class FakeTxn:
    def __init__(self, id, merchant_id, amount, posted_date, is_drift=True):
        self.id = id
        self.merchant_id = merchant_id
        self.amount = amount
        self.posted_date = posted_date
        self.expected_amount = None
        self.deviation_pct = 42.0
        self.is_drift = is_drift


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeDB:
    def __init__(self, merchants):
        self.merchants = merchants

    async def execute(self, query):
        return FakeResult(self.merchants)


@pytest.mark.asyncio
async def test_chains_sync_clustering_scoring_and_serializes_new_alerts():
    merchant = FakeMerchant(id=1, normalized_name="NETFLIX INC")
    flagged_txn = FakeTxn(id=101, merchant_id=1, amount=45.00, posted_date=date(2024, 6, 1))
    plaid_item = FakePlaidItem(id=7)
    db = FakeDB(merchants=[merchant])

    with (
        patch("app.services.pipeline.plaid_client.sync_transactions", new=AsyncMock(return_value=3)) as mock_sync,
        patch(
            "app.services.pipeline.clustering.run_clustering",
            new=AsyncMock(return_value={"subscriptions_created": 0, "transactions_linked": 1, "merchant_groups_considered": 1}),
        ) as mock_clustering,
        patch(
            "app.services.pipeline.scoring.run_scoring",
            new=AsyncMock(
                return_value={
                    "transactions_scored": 1,
                    "flagged_as_drift": 1,
                    "newly_flagged": [flagged_txn],
                }
            ),
        ) as mock_scoring,
    ):
        result = await run_pipeline(db, plaid_item)

    mock_sync.assert_awaited_once_with(db, plaid_item)
    mock_clustering.assert_awaited_once_with(db, [7])
    mock_scoring.assert_awaited_once_with(db, [7])

    assert result["ingested"] == 3
    assert result["scoring"] == {"transactions_scored": 1, "flagged_as_drift": 1}
    assert result["alerts"] == [
        {
            "id": 101,
            "merchant_name": "NETFLIX INC",
            "amount": 45.00,
            "posted_date": "2024-06-01",
            "expected_amount": None,
            "deviation_pct": 42.0,
            "is_drift": True,
        }
    ]
