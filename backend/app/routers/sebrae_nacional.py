"""Router do painel SEBRAE Nacional."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import dashboard_nacional

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    periodo_inicio: Optional[date] = Query(None, description="Inicio do periodo (YYYY-MM-DD)"),
    periodo_fim: Optional[date] = Query(None, description="Fim do periodo (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_nacional.montar_dashboard(db, periodo_inicio, periodo_fim)


@router.get("/mapa")
async def mapa(
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_nacional.dados_mapa(db)


@router.get("/desertos")
async def desertos(
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_nacional.desertos_fornecimento(db)


@router.get("/tendencias")
async def tendencias(
    periodo_meses: int = Query(12, ge=1, le=60, description="Quantidade de meses para a serie temporal"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_nacional.tendencias(db, periodo_meses)
