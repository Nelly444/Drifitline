from unittest.mock import AsyncMock, patch

import pytest

from app.services.scheduler import scheduled_pipeline_run


class _FakeSessionCtx:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False


def _fake_async_session():
    return _FakeSessionCtx()


@pytest.mark.asyncio
async def test_broadcasts_one_message_per_alert():
    alerts = [{"id": 1, "merchant_name": "NETFLIX INC"}, {"id": 2, "merchant_name": "SPOTIFY INC"}]

    with (
        patch("app.services.scheduler.async_session", new=_fake_async_session),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock(return_value={"alerts": alerts})),
        patch("app.services.scheduler.manager.broadcast", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()

    assert mock_broadcast.await_count == 2
    mock_broadcast.assert_any_await({"type": "new_alert", "transaction": alerts[0]})
    mock_broadcast.assert_any_await({"type": "new_alert", "transaction": alerts[1]})


@pytest.mark.asyncio
async def test_exception_from_run_pipeline_is_swallowed():
    with (
        patch("app.services.scheduler.async_session", new=_fake_async_session),
        patch("app.services.scheduler.run_pipeline", new=AsyncMock(side_effect=RuntimeError("boom"))),
        patch("app.services.scheduler.manager.broadcast", new=AsyncMock()) as mock_broadcast,
    ):
        await scheduled_pipeline_run()  # must not raise

    mock_broadcast.assert_not_awaited()
