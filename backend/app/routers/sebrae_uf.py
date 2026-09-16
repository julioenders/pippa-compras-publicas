"""Router do painel SEBRAE UF (visao estadual)."""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import dashboard_uf

router = APIRouter()


@router.get("/{uf}/dashboard")
async def dashboard(
    uf: str = Path(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_uf.montar_dashboard(db, uf)


@router.get("/{uf}/radar")
async def radar(
    uf: str = Path(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_uf.radar_oportunidades(db, uf)


@router.get("/{uf}/cruzamento")
async def cruzamento(
    uf: str = Path(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_uf.cruzamento_oferta_demanda(db, uf)


@router.get("/{uf}/alertas")
async def alertas(
    uf: str = Path(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_uf.alertas_uf(db, uf)
