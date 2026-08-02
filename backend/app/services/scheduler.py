import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import async_session
from app.services.pipeline import run_pipeline
from app.ws.manager import manager

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 20


async def scheduled_pipeline_run() -> None:
    try:
        async with async_session() as db:
            result = await run_pipeline(db)
            for alert in result["alerts"]:
                await manager.broadcast({"type": "new_alert", "transaction": alert})
    except Exception:
        # One failed run (transient Plaid hiccup, etc.) shouldn't stop future
        # scheduled runs - log and let the next interval try again.
        logger.exception("Scheduled pipeline run failed")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_pipeline_run, "interval", seconds=POLL_INTERVAL_SECONDS)
    return scheduler
