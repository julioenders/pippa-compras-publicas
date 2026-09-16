import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Configure and start the collection scheduler."""
    from app.collectors.pncp_collector import coletar_contratacoes_diarias
    from app.collectors.dou_collector import coletar_dou_secao3
    from app.collectors.observatorio_sync import atualizar_cache_mpes

    # Daily at configured hour (BRT): fetch new PNCP procurements
    scheduler.add_job(
        coletar_contratacoes_diarias,
        CronTrigger(hour=settings.COLLECTION_CRON_HOUR, minute=settings.COLLECTION_CRON_MINUTE),
        id="pncp_daily",
        name="Coleta diária PNCP",
        replace_existing=True,
    )

    # Daily at CRON_HOUR+1: scrape DOU Section 3
    scheduler.add_job(
        coletar_dou_secao3,
        CronTrigger(hour=settings.COLLECTION_CRON_HOUR + 1, minute=0),
        id="dou_daily",
        name="Coleta diária DOU Seção 3",
        replace_existing=True,
    )

    # Weekly on Monday: refresh Observatorio MPE cache
    scheduler.add_job(
        atualizar_cache_mpes,
        CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="observatorio_weekly",
        name="Atualização semanal cache MPEs",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado com %d jobs", len(scheduler.get_jobs()))


def stop_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler encerrado")
