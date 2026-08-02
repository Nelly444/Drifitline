from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.services.pipeline import run_pipeline


class FakeMerchant:
    def __init__(self, id, normalized_name):
        self.id = id
        self.normalized_name = normalized_name


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
    def __init__(self, items, single=None):
        self._items = items
        self._single = single

    def scalars(self):
        return FakeScalars(self._items)

    def scalar_one_or_none(self):
        return self._single


class FakeDB:
    def __init__(self, plaid_item, merchants):
        self.plaid_item = plaid_item
        self.merchants = merchants
        self.call_count = 0

    async def execute(self, query):
        # First call looks up the latest PlaidItem; second call (only reached
        # when a PlaidItem exists) looks up all merchants for serialization.
        self.call_count += 1
        if self.call_count == 1:
            return FakeResult([], single=self.plaid_item)
        return FakeResult(self.merchants)


@pytest.mark.asyncio
async def test_no_plaid_item_is_a_noop():
    db = FakeDB(plaid_item=None, merchants=[])

    result = await run_pipeline(db)

    assert result == {"ingested": 0, "clustering": None, "scoring": None, "alerts": []}


@pytest.mark.asyncio
async def test_chains_sync_clustering_scoring_and_serializes_new_alerts():
    merchant = FakeMerchant(id=1, normalized_name="NETFLIX INC")
    flagged_txn = FakeTxn(id=101, merchant_id=1, amount=45.00, posted_date=date(2024, 6, 1))
    db = FakeDB(plaid_item=object(), merchants=[merchant])

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
        result = await run_pipeline(db)

    mock_sync.assert_awaited_once()
    mock_clustering.assert_awaited_once()
    mock_scoring.assert_awaited_once()

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
