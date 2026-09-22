"""Router de dados de contratacoes publicas."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Contratacao, EventoContratacao, Item

router = APIRouter()


@router.get("/")
async def listar_contratacoes(
    data_inicio: Optional[date] = Query(None, description="Data inicial do filtro (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final do filtro (YYYY-MM-DD)"),
    uf: Optional[str] = Query(None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    municipio_ibge: Optional[str] = Query(None, description="Codigo IBGE do municipio"),
    modalidade: Optional[str] = Query(None, description="Modalidade da contratacao"),
    esfera: Optional[str] = Query(None, description="Esfera: federal, estadual ou municipal"),
    exclusiva_mpe: Optional[bool] = Query(None, description="Filtrar apenas contratacoes exclusivas para MPE"),
    situacao: Optional[str] = Query(None, description="Situacao da contratacao (ex: Aberto, Encerrado)"),
    srp: Optional[bool] = Query(None, description="Filtrar contratacoes com Sistema de Registro de Precos"),
    beneficio_mpe: Optional[str] = Query(None, description="Tipo de beneficio MPE (ex: exclusiva, cota_reservada)"),
    pagina: int = Query(1, ge=1, description="Numero da pagina"),
    tamanho: int = Query(20, ge=1, le=100, description="Quantidade de itens por pagina"),
    db: AsyncSession = Depends(get_db),
):
    filtros = []
    if data_inicio:
        filtros.append(Contratacao.data_publicacao >= data_inicio)
    if data_fim:
        filtros.append(Contratacao.data_publicacao <= data_fim)
    if uf:
        filtros.append(Contratacao.uf == uf)
    if municipio_ibge:
        filtros.append(Contratacao.municipio_ibge == municipio_ibge)
    if modalidade:
        filtros.append(Contratacao.modalidade_nome.ilike(f"%{modalidade}%"))
    if esfera:
        filtros.append(Contratacao.esfera == esfera[0].upper())
    if exclusiva_mpe is not None:
        filtros.append(Contratacao.exclusiva_mpe == exclusiva_mpe)
    if situacao:
        filtros.append(Contratacao.situacao.ilike(f"%{situacao}%"))
    if srp is not None:
        filtros.append(Contratacao.srp == srp)
    if beneficio_mpe:
        filtros.append(Contratacao.beneficio_mpe.ilike(f"%{beneficio_mpe}%"))

    where = and_(*filtros) if filtros else True

    stmt_count = select(func.count(Contratacao.id)).where(where)
    total = (await db.execute(stmt_count)).scalar_one()

    stmt = (
        select(Contratacao)
        .where(where)
        .order_by(Contratacao.data_publicacao.desc().nulls_last())
        .offset((pagina - 1) * tamanho)
        .limit(tamanho)
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "pagina": pagina,
        "tamanho": tamanho,
        "total": total,
        "itens": [
            {
                "id": c.id,
                "numero_controle": f"{c.sequencial}/{c.ano}" if c.sequencial and c.ano else None,
                "orgao_cnpj": c.orgao_cnpj,
                "orgao_nome": c.orgao_nome,
                "objeto_resumo": c.objeto,
                "valor_estimado": float(c.valor_estimado) if c.valor_estimado else None,
                "modalidade": c.modalidade_nome,
                "data_publicacao": c.data_publicacao.isoformat() if c.data_publicacao else None,
                "uf": c.uf,
                "municipio_ibge": c.municipio_ibge,
                "exclusiva_mpe": c.exclusiva_mpe,
                "esfera": c.esfera,
                "situacao": c.situacao,
                "situacao_descricao": c.situacao_descricao,
                "beneficio_mpe": c.beneficio_mpe,
                "srp": c.srp,
                "tipo_instrumento": c.tipo_instrumento,
                "criterio_julgamento": c.criterio_julgamento,
                "modo_disputa": c.modo_disputa,
            }
            for c in rows
        ],
    }


@router.get("/{id}")
async def detalhe_contratacao(
    id: int = Path(..., description="ID unico da contratacao"),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Contratacao)
        .options(selectinload(Contratacao.items), selectinload(Contratacao.eventos))
        .where(Contratacao.id == id)
    )
    result = await db.execute(stmt)
    c = result.scalar_one_or_none()

    if c is None:
        return {"erro": "Contratacao nao encontrada", "id": id}

    return {
        "id": c.id,
        "numero_controle": f"{c.sequencial}/{c.ano}" if c.sequencial and c.ano else None,
        "orgao_cnpj": c.orgao_cnpj,
        "orgao_nome": c.orgao_nome,
        "objeto_completo": c.objeto,
        "valor_estimado": float(c.valor_estimado) if c.valor_estimado else None,
        "modalidade": c.modalidade_nome,
        "data_publicacao": c.data_publicacao.isoformat() if c.data_publicacao else None,
        "data_abertura": c.data_abertura_proposta.isoformat() if c.data_abertura_proposta else None,
        "data_encerramento": c.data_encerramento_proposta.isoformat() if c.data_encerramento_proposta else None,
        "uf": c.uf,
        "municipio_ibge": c.municipio_ibge,
        "exclusiva_mpe": c.exclusiva_mpe,
        "esfera": c.esfera,
        "situacao": c.situacao,
        "situacao_descricao": c.situacao_descricao,
        "beneficio_mpe": c.beneficio_mpe,
        "srp": c.srp,
        "tipo_instrumento": c.tipo_instrumento,
        "criterio_julgamento": c.criterio_julgamento,
        "modo_disputa": c.modo_disputa,
        "link_sistema_origem": c.link_sistema_origem,
        "link_edital": c.link_edital,
        "itens": [
            {
                "numero": it.numero_item,
                "descricao": it.descricao,
                "quantidade": float(it.quantidade) if it.quantidade else None,
                "unidade": it.unidade,
                "valor_unitario": float(it.valor_unitario_estimado) if it.valor_unitario_estimado else None,
                "catmat": it.catmat_catser,
            }
            for it in c.items
        ],
        "eventos": [
            {
                "id": ev.id,
                "tipo": ev.tipo,
                "data_evento": ev.data_evento.isoformat() if ev.data_evento else None,
                "descricao": ev.descricao,
            }
            for ev in c.eventos
        ],
        "fonte": "PNCP",
    }
