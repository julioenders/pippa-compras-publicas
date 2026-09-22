"""Router administrativo para disparar coletas manualmente."""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contratacao import Contratacao

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/collect/dou")
async def trigger_dou(
    data: str | None = Query(
        None,
        description="Data no formato YYYY-MM-DD. Se omitida, coleta o dia anterior.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    """Dispara coleta do DOU Secao 3 para uma data especifica."""
    from app.collectors.dou_collector import coletar_dou_secao3

    data_alvo: date | None = None
    if data:
        data_alvo = date.fromisoformat(data)

    result = await coletar_dou_secao3(data_alvo=data_alvo)
    return {"status": "completed", "job": "dou", "result": result}


@router.post("/collect/all")
async def trigger_all(
    data: str | None = Query(
        None,
        description="Data no formato YYYY-MM-DD.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    """Dispara todas as coletas para uma data especifica."""
    from app.collectors.dou_collector import coletar_dou_secao3

    data_alvo: date | None = None
    if data:
        data_alvo = date.fromisoformat(data)

    result = await coletar_dou_secao3(data_alvo=data_alvo)
    return {"status": "completed", "jobs": ["dou"], "result": result}


@router.get("/stats")
async def collection_stats(db: AsyncSession = Depends(get_db)):
    """Retorna estatisticas gerais do banco de dados."""
    total = (await db.execute(
        select(func.count(Contratacao.id))
    )).scalar_one()

    por_situacao = (await db.execute(
        select(Contratacao.situacao, func.count(Contratacao.id))
        .group_by(Contratacao.situacao)
    )).all()

    por_uf = (await db.execute(
        select(Contratacao.uf, func.count(Contratacao.id))
        .group_by(Contratacao.uf)
        .order_by(func.count(Contratacao.id).desc())
        .limit(10)
    )).all()

    valor_total = (await db.execute(
        select(func.sum(Contratacao.valor_estimado))
    )).scalar_one()

    ultima_data = (await db.execute(
        select(func.max(Contratacao.data_publicacao))
    )).scalar_one()

    return {
        "total_contratacoes": total,
        "valor_total_estimado": float(valor_total or 0),
        "ultima_publicacao": ultima_data.isoformat() if ultima_data else None,
        "por_situacao": {s or "null": c for s, c in por_situacao},
        "top_ufs": {uf or "sem_uf": c for uf, c in por_uf},
    }


@router.post("/fix-uf")
async def fix_uf_from_raw_json(db: AsyncSession = Depends(get_db)):
    """Re-extract UF from raw_json for records missing UF."""
    stmt = select(Contratacao).where(
        (Contratacao.uf == None) | (Contratacao.uf == "")  # noqa: E711
    )
    result = await db.execute(stmt)
    contratacoes = result.scalars().all()

    fixed = 0
    for c in contratacoes:
        if not c.raw_json:
            continue
        hierarchy = c.raw_json.get("hierarchyStr", "") or ""
        import re
        uf_match = re.search(r"\b([A-Z]{2})\b", hierarchy)
        if uf_match and uf_match.group(1) in {
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        }:
            c.uf = uf_match.group(1)
            fixed += 1

    await db.commit()
    return {"fixed": fixed, "total_checked": len(contratacoes)}
