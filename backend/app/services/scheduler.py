import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db import async_session
from app.models import PlaidItem
from app.services.pipeline import run_pipeline
from app.ws.manager import manager

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 20


async def scheduled_pipeline_run() -> None:
    try:
        async with async_session() as db:
            result = await db.execute(select(PlaidItem))
            for plaid_item in result.scalars().all():
                pipeline_result = await run_pipeline(db, plaid_item)
                for alert in pipeline_result["alerts"]:
                    await manager.broadcast_to_user(plaid_item.user_id, {"type": "new_alert", "transaction": alert})
    except Exception:
        # One failed run (transient Plaid hiccup, etc.) shouldn't stop future
        # scheduled runs - log and let the next interval try again. Note this
        # still wraps the whole per-tenant loop, so one tenant's failure
        # currently aborts the rest of that tick too - accepted limitation.
        logger.exception("Scheduled pipeline run failed")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_pipeline_run, "interval", seconds=POLL_INTERVAL_SECONDS)
    return scheduler
