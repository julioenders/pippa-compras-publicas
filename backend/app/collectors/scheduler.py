import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Configure and start the collection scheduler."""
    from app.collectors.dou_collector import coletar_dou_secao3

    # Daily at configured hour (BRT): scrape DOU Section 3
    scheduler.add_job(
        coletar_dou_secao3,
        CronTrigger(hour=settings.COLLECTION_CRON_HOUR, minute=settings.COLLECTION_CRON_MINUTE),
        id="dou_daily",
        name="Coleta diária DOU Seção 3",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado com %d jobs", len(scheduler.get_jobs()))


def stop_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler encerrado")
