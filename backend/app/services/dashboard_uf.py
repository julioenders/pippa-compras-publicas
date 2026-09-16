"""Servico de dashboard para o perfil SEBRAE UF (Unidade da Federacao)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, case, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Contratacao, Contrato, Cruzamento, Alerta, Item, CacheMPE
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)

# Portes considerados MPE
_PORTES_MPE = ("MEI", "ME", "EPP")

_SINAL_LABEL: dict[str, str] = {
    SinalOportunidade.OPORTUNIDADE.value: "Otima oportunidade",
    SinalOportunidade.COMPETITIVO.value: "Competitivo",
    SinalOportunidade.CAUTELA.value: "Muita concorrencia",
    SinalOportunidade.SATURADO.value: "Mercado saturado",
    SinalOportunidade.DESERTO.value: "Deserto de fornecimento",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def montar_dashboard(
    db: AsyncSession,
    uf: str,
) -> dict[str, Any]:
    """Visao estadual consolidada.

    1. Contagem de oportunidades abertas na UF
    2. Valor total estimado na UF
    3. Contagem de desertos na UF
    4. Contagem de alertas ativos para a UF
    """
    hoje = date.today()

    # 1 -- Oportunidades abertas
    stmt_abertas = select(
        func.count(Contratacao.id).label("total"),
        func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
    ).where(
        and_(
            Contratacao.uf == uf,
            Contratacao.data_encerramento_proposta >= hoje,
        )
    )
    abertas = (await db.execute(stmt_abertas)).one()

    # 2 -- Desertos na UF
    stmt_desertos = select(
        func.count(distinct(Cruzamento.cnae_divisao))
    ).where(
        and_(
            Cruzamento.uf == uf,
            Cruzamento.sinal == SinalOportunidade.DESERTO.value,
        )
    )
    qtd_desertos = (await db.execute(stmt_desertos)).scalar_one() or 0

    # 3 -- Alertas ativos (nao lidos)
    stmt_alertas = select(
        func.count(Alerta.id)
    ).where(
        and_(
            Alerta.uf == uf,
            Alerta.lido == False,
        )
    )
    qtd_alertas = (await db.execute(stmt_alertas)).scalar_one() or 0

    # 4 -- Participacao MPE na UF (ultimos 12 meses)
    pct_mpe = await _pct_mpe_uf(db, uf)

    return {
        "uf": uf,
        "oportunidades_abertas": abertas.total,
        "valor_total_estimado": float(abertas.valor_total),
        "desertos_fornecimento": qtd_desertos,
        "alertas_nao_lidos": qtd_alertas,
        "participacao_mpe_percentual": pct_mpe,
    }


async def radar_oportunidades(
    db: AsyncSession,
    uf: str,
) -> list[dict[str, Any]]:
    """Lista ranqueada de oportunidades abertas na UF com sinais de cruzamento.

    Ordena por score descendente para mostrar as melhores oportunidades
    para atuacao do SEBRAE UF.
    """
    hoje = date.today()

    # Subquery for latest cruzamento per contratacao
    cruzamento_sub = (
        select(
            Cruzamento.contratacao_id,
            Cruzamento.sinal,
            Cruzamento.score,
            Cruzamento.cnae_divisao,
            Cruzamento.cnae_descricao,
            Cruzamento.qtd_mpes_regiao,
        )
        .distinct(Cruzamento.contratacao_id)
        .order_by(Cruzamento.contratacao_id, Cruzamento.created_at.desc())
        .subquery("ultimo_cruzamento")
    )

    stmt = (
        select(
            Contratacao.id,
            Contratacao.orgao_nome,
            Contratacao.objeto,
            Contratacao.valor_estimado,
            Contratacao.exclusiva_mpe,
            Contratacao.data_encerramento_proposta,
            Contratacao.modalidade_nome,
            Contratacao.municipio_ibge,
            cruzamento_sub.c.sinal,
            cruzamento_sub.c.score,
            cruzamento_sub.c.cnae_divisao,
            cruzamento_sub.c.cnae_descricao,
            cruzamento_sub.c.qtd_mpes_regiao,
        )
        .outerjoin(
            cruzamento_sub,
            cruzamento_sub.c.contratacao_id == Contratacao.id,
        )
        .where(
            and_(
                Contratacao.uf == uf,
                Contratacao.data_encerramento_proposta >= hoje,
            )
        )
        .order_by(
            cruzamento_sub.c.score.desc().nulls_last(),
            Contratacao.valor_estimado.desc().nulls_last(),
        )
        .limit(50)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": row.id,
            "orgao": row.orgao_nome,
            "objeto": row.objeto,
            "valor_estimado": float(row.valor_estimado) if row.valor_estimado else None,
            "exclusiva_mpe": bool(row.exclusiva_mpe),
            "data_encerramento": row.data_encerramento_proposta.isoformat() if row.data_encerramento_proposta else None,
            "modalidade": row.modalidade_nome,
            "municipio_ibge": row.municipio_ibge,
            "sinal": row.sinal or SinalOportunidade.COMPETITIVO.value,
            "sinal_descricao": _SINAL_LABEL.get(
                row.sinal or SinalOportunidade.COMPETITIVO.value,
                row.sinal or "",
            ),
            "score": float(row.score) if row.score else None,
            "cnae_divisao": row.cnae_divisao,
            "cnae_descricao": row.cnae_descricao,
            "qtd_mpes_regiao": row.qtd_mpes_regiao,
        }
        for row in rows
    ]


async def cruzamento_oferta_demanda(
    db: AsyncSession,
    uf: str,
) -> list[dict[str, Any]]:
    """Dados de scatter plot: volume de demanda vs qtd de MPEs por divisao CNAE.

    Cada ponto representa uma divisao CNAE na UF, mostrando:
    - eixo X: quantidade de contratacoes (demanda)
    - eixo Y: quantidade de MPEs na regiao (oferta)
    - cor: sinal predominante
    """
    # Demand side: count contratacoes per CNAE division in the UF
    stmt_demanda = (
        select(
            Item.cnae_mapeado,
            func.count(distinct(Item.contratacao_id)).label("qtd_contratacoes"),
            func.coalesce(func.sum(Item.valor_total_estimado), 0).label("valor_total"),
        )
        .join(Contratacao, Item.contratacao_id == Contratacao.id)
        .where(
            and_(
                Contratacao.uf == uf,
                Item.cnae_mapeado.is_not(None),
            )
        )
        .group_by(Item.cnae_mapeado)
    )

    res_demanda = (await db.execute(stmt_demanda)).all()

    if not res_demanda:
        return []

    # Supply side: MPEs from CacheMPE table
    cnae_divisoes = list({
        r.cnae_mapeado[:2] for r in res_demanda if r.cnae_mapeado
    })

    stmt_oferta = (
        select(
            CacheMPE.cnae_divisao,
            func.sum(CacheMPE.qtd_mpes).label("total_mpes"),
        )
        .where(
            and_(
                CacheMPE.uf == uf,
                CacheMPE.cnae_divisao.in_(cnae_divisoes),
            )
        )
        .group_by(CacheMPE.cnae_divisao)
    )

    res_oferta = (await db.execute(stmt_oferta)).all()
    oferta_map: dict[str, int] = {r.cnae_divisao: r.total_mpes for r in res_oferta}

    # Sinal predominante por CNAE na UF
    stmt_sinal = (
        select(
            Cruzamento.cnae_divisao,
            Cruzamento.cnae_descricao,
            Cruzamento.sinal,
            func.count(Cruzamento.id).label("qtd"),
        )
        .where(Cruzamento.uf == uf)
        .group_by(Cruzamento.cnae_divisao, Cruzamento.cnae_descricao, Cruzamento.sinal)
    )

    res_sinal = (await db.execute(stmt_sinal)).all()

    # Pick the most frequent sinal per CNAE division
    sinal_map: dict[str, tuple[str, str | None]] = {}
    sinal_count: dict[str, int] = {}
    for row in res_sinal:
        div = row.cnae_divisao
        if div not in sinal_count or row.qtd > sinal_count[div]:
            sinal_count[div] = row.qtd
            sinal_map[div] = (row.sinal, row.cnae_descricao)

    # Aggregate demand by CNAE division (first 2 digits)
    demanda_por_divisao: dict[str, dict[str, Any]] = {}
    for row in res_demanda:
        if not row.cnae_mapeado:
            continue
        div = row.cnae_mapeado[:2]
        if div not in demanda_por_divisao:
            demanda_por_divisao[div] = {"qtd_contratacoes": 0, "valor_total": 0.0}
        demanda_por_divisao[div]["qtd_contratacoes"] += row.qtd_contratacoes
        demanda_por_divisao[div]["valor_total"] += float(row.valor_total)

    pontos: list[dict[str, Any]] = []
    for div, dem in demanda_por_divisao.items():
        sinal_info = sinal_map.get(div, (SinalOportunidade.COMPETITIVO.value, None))
        pontos.append({
            "cnae_divisao": div,
            "cnae_descricao": sinal_info[1],
            "qtd_contratacoes": dem["qtd_contratacoes"],
            "valor_total_demanda": dem["valor_total"],
            "qtd_mpes_regiao": oferta_map.get(div, 0),
            "sinal": sinal_info[0],
            "sinal_descricao": _SINAL_LABEL.get(sinal_info[0], sinal_info[0]),
        })

    # Sort by demand desc
    pontos.sort(key=lambda p: p["qtd_contratacoes"], reverse=True)
    return pontos


async def alertas_uf(
    db: AsyncSession,
    uf: str,
) -> list[dict[str, Any]]:
    """Alertas ativos (nao lidos) para a UF, ordenados por data de criacao."""
    stmt = (
        select(Alerta)
        .where(
            and_(
                Alerta.uf == uf,
                Alerta.lido == False,
            )
        )
        .order_by(Alerta.created_at.desc())
        .limit(50)
    )

    result = await db.execute(stmt)
    alertas = result.scalars().all()

    return [
        {
            "id": alerta.id,
            "tipo": alerta.tipo,
            "titulo": alerta.titulo,
            "corpo": alerta.corpo,
            "cnae_divisao": alerta.cnae_divisao,
            "contratacao_id": alerta.contratacao_id,
            "cruzamento_id": alerta.cruzamento_id,
            "criado_em": alerta.created_at.isoformat() if alerta.created_at else None,
        }
        for alerta in alertas
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _pct_mpe_uf(
    db: AsyncSession,
    uf: str,
) -> float:
    """Calcula o percentual de contratos com MPEs na UF nos ultimos 12 meses."""
    data_inicio = date.today() - timedelta(days=365)

    stmt = select(
        func.count(Contrato.id).label("total"),
        func.count(
            case(
                (Contrato.fornecedor_porte.in_(_PORTES_MPE), Contrato.id),
                else_=None,
            )
        ).label("total_mpe"),
    ).join(
        Contratacao, Contrato.contratacao_id == Contratacao.id
    ).where(
        and_(
            Contratacao.uf == uf,
            Contrato.data_assinatura >= data_inicio,
        )
    )

    result = (await db.execute(stmt)).one()
    if result.total == 0:
        return 0.0
    return round((result.total_mpe / result.total) * 100, 1)
