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
    async with async_session() as db:
        try:
            result = await db.execute(select(PlaidItem))
            plaid_items = result.scalars().all()
        except Exception:
            logger.exception("Scheduled pipeline run failed to load plaid items")
            return

        for plaid_item in plaid_items:
            try:
                pipeline_result = await run_pipeline(db, plaid_item)
                for alert in pipeline_result["alerts"]:
                    await manager.broadcast_to_user(plaid_item.user_id, {"type": "new_alert", "transaction": alert})
            except Exception:
                logger.exception("Pipeline run failed for plaid_item_id=%s", plaid_item.id)
                await db.rollback()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_pipeline_run, "interval", seconds=POLL_INTERVAL_SECONDS)
    return scheduler
