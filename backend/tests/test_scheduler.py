import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.scheduler import scheduled_pipeline_run


class FakePlaidItem:
    def __init__(self, id, user_id):
        self.id = id
        self.user_id = user_id


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
    def __init__(self, plaid_items):
        self.plaid_items = plaid_items
        self.rollback_count = 0

    async def execute(self, query):
        return FakeResult(self.plaid_items)

    async def rollback(self):
        self.rollback_count += 1


def _session_yielding(fake_db):
    class _Ctx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *args):
            return False

    return lambda: _Ctx()


USER_A = uuid.uuid4()
USER_B = uuid.uuid4()


@pytest.mark.asyncio
async def test_runs_pipeline_once_per_plaid_item_and_broadcasts_to_its_owner():
    item_a, item_b = FakePlaidItem(id=1, user_id=USER_A), FakePlaidItem(id=2, user_id=USER_B)
    fake_db = FakeDB([item_a, item_b])

    async def fake_run_pipeline(db, plaid_item):
        return {"alerts": [{"id": plaid_item.id, "merchant_name": "X"}]}

    with (
        patch("app.services.scheduler.async_session", new=_session_yielding(fake_db)),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock(side_effect=fake_run_pipeline)) as mock_pipeline,
        patch("app.services.scheduler.manager.broadcast_to_user", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()

    assert mock_pipeline.await_count == 2
    mock_pipeline.assert_any_await(fake_db, item_a)
    mock_pipeline.assert_any_await(fake_db, item_b)

    assert mock_broadcast.await_count == 2
    mock_broadcast.assert_any_await(USER_A, {"type": "new_alert", "transaction": {"id": 1, "merchant_name": "X"}})
    mock_broadcast.assert_any_await(USER_B, {"type": "new_alert", "transaction": {"id": 2, "merchant_name": "X"}})


@pytest.mark.asyncio
async def test_no_plaid_items_is_a_noop():
    fake_db = FakeDB([])

    with (
        patch("app.services.scheduler.async_session", new=_session_yielding(fake_db)),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock()) as mock_pipeline,
        patch("app.services.scheduler.manager.broadcast_to_user", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()

    mock_pipeline.assert_not_awaited()
    mock_broadcast.assert_not_awaited()


@pytest.mark.asyncio
async def test_exception_from_run_pipeline_is_swallowed():
    fake_db = FakeDB([FakePlaidItem(id=1, user_id=USER_A)])

    with (
        patch("app.services.scheduler.async_session", new=_session_yielding(fake_db)),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock(side_effect=RuntimeError("boom"))),
        patch("app.services.scheduler.manager.broadcast_to_user", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()

    mock_broadcast.assert_not_awaited()
    assert fake_db.rollback_count == 1


@pytest.mark.asyncio
async def test_one_tenants_exception_does_not_abort_other_tenants_in_same_tick():
    item_a, item_b = FakePlaidItem(id=1, user_id=USER_A), FakePlaidItem(id=2, user_id=USER_B)
    fake_db = FakeDB([item_a, item_b])

    async def fake_run_pipeline(db, plaid_item):
        if plaid_item is item_a:
            raise RuntimeError("boom")
        return {"alerts": [{"id": plaid_item.id, "merchant_name": "X"}]}

    with (
        patch("app.services.scheduler.async_session", new=_session_yielding(fake_db)),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock(side_effect=fake_run_pipeline)) as mock_pipeline,
        patch("app.services.scheduler.manager.broadcast_to_user", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()

    assert mock_pipeline.await_count == 2
    assert fake_db.rollback_count == 1
    mock_broadcast.assert_awaited_once_with(USER_B, {"type": "new_alert", "transaction": {"id": 2, "merchant_name": "X"}})
