"""Router administrativo para disparar coletas manualmente."""

import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/collect/dou")
async def trigger_dou(background_tasks: BackgroundTasks):
    from app.collectors.dou_collector import coletar_dou_secao3
    background_tasks.add_task(coletar_dou_secao3)
    return {"status": "started", "job": "dou"}


@router.post("/collect/all")
async def trigger_all(background_tasks: BackgroundTasks):
    from app.collectors.dou_collector import coletar_dou_secao3
    background_tasks.add_task(coletar_dou_secao3)
    return {"status": "started", "jobs": ["dou"]}


@router.post("/fix-uf")
async def fix_uf_from_raw_json(db: AsyncSession = Depends(get_db)):
    """Re-extract UF and municipio_ibge from raw_json for all records missing UF."""
    from app.models.contratacao import Contratacao

    stmt = select(Contratacao).where(
        (Contratacao.uf == None) | (Contratacao.uf == "")  # noqa: E711
    )
    result = await db.execute(stmt)
    contratacoes = result.scalars().all()

    fixed = 0
    for c in contratacoes:
        if not c.raw_json:
            continue
        unidade = c.raw_json.get("unidadeOrgao", {})
        new_uf = unidade.get("ufSigla", "")
        new_mun = unidade.get("codigoIbge", "")
        if new_uf:
            c.uf = new_uf
            if new_mun:
                c.municipio_ibge = new_mun
            fixed += 1

    await db.commit()
    return {"fixed": fixed, "total_checked": len(contratacoes)}
