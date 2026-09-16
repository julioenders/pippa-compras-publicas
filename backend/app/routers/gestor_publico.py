"""Router do painel do Gestor Publico."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import dashboard_gestor

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    orgao_cnpj: str = Query(..., description="CNPJ do orgao publico"),
    periodo_inicio: Optional[date] = Query(None, description="Inicio do periodo (YYYY-MM-DD)"),
    periodo_fim: Optional[date] = Query(None, description="Fim do periodo (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_gestor.montar_dashboard(db, orgao_cnpj, periodo_inicio, periodo_fim)


@router.get("/participacao-mpe")
async def participacao_mpe(
    orgao_cnpj: str = Query(..., description="CNPJ do orgao publico"),
    periodo_meses: int = Query(12, ge=1, le=60, description="Quantidade de meses para a serie temporal"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_gestor.serie_participacao_mpe(db, orgao_cnpj, periodo_meses)


@router.get("/benchmark-precos")
async def benchmark_precos(
    catmat: str = Query(..., description="Codigo CATMAT do item"),
    uf: Optional[str] = Query(None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_gestor.benchmark_precos(db, catmat, uf)
