"""Router administrativo para disparar coletas manualmente."""

import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/collect/pncp")
async def trigger_pncp(background_tasks: BackgroundTasks):
    from app.collectors.pncp_collector import coletar_contratacoes_diarias
    background_tasks.add_task(coletar_contratacoes_diarias)
    return {"status": "started", "job": "pncp"}


@router.post("/collect/observatorio")
async def trigger_observatorio(background_tasks: BackgroundTasks):
    from app.collectors.observatorio_sync import atualizar_cache_mpes
    background_tasks.add_task(atualizar_cache_mpes)
    return {"status": "started", "job": "observatorio"}


@router.post("/collect/dou")
async def trigger_dou(background_tasks: BackgroundTasks):
    from app.collectors.dou_collector import coletar_dou_secao3
    background_tasks.add_task(coletar_dou_secao3)
    return {"status": "started", "job": "dou"}


@router.post("/collect/all")
async def trigger_all(background_tasks: BackgroundTasks):
    from app.collectors.pncp_collector import coletar_contratacoes_diarias
    from app.collectors.dou_collector import coletar_dou_secao3
    from app.collectors.observatorio_sync import atualizar_cache_mpes

    background_tasks.add_task(coletar_contratacoes_diarias)
    background_tasks.add_task(coletar_dou_secao3)
    background_tasks.add_task(atualizar_cache_mpes)
    return {"status": "started", "jobs": ["pncp", "dou", "observatorio"]}
