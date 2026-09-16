"""Servico de dashboard para o perfil SEBRAE Nacional."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, case, and_, extract, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contratacao, Contrato, Cruzamento, Item
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)

# Portes considerados MPE
_PORTES_MPE = ("MEI", "ME", "EPP")

# Lista de UFs brasileiras para garantir cobertura no mapa
_UFS_BRASIL = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def montar_dashboard(
    db: AsyncSession,
    periodo_inicio: date | None = None,
    periodo_fim: date | None = None,
) -> dict[str, Any]:
    """Monta visao nacional consolidada.

    1. Total de contratacoes em todas as esferas
    2. Valor total
    3. Participacao nacional de MPEs (%)
    4. Contagem de desertos de fornecimento
    5. Detalhamento por UF
    """
    if periodo_fim is None:
        periodo_fim = date.today()
    if periodo_inicio is None:
        periodo_inicio = periodo_fim - timedelta(days=365)

    # 1 & 2 -- Totais nacionais
    stmt_totais = select(
        func.count(Contratacao.id).label("total"),
        func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
    ).where(
        and_(
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
        )
    )
    totais = (await db.execute(stmt_totais)).one()

    # 3 -- Participacao nacional de MPEs
    pct_mpe = await _pct_mpe_nacional(db, periodo_inicio, periodo_fim)

    # 4 -- Desertos de fornecimento
    qtd_desertos = await _contar_desertos(db)

    # 5 -- Resumo por UF
    resumo_uf = await _resumo_por_uf(db, periodo_inicio, periodo_fim)

    return {
        "periodo": {
            "inicio": periodo_inicio.isoformat(),
            "fim": periodo_fim.isoformat(),
        },
        "total_contratacoes": totais.total,
        "valor_total_estimado": float(totais.valor_total),
        "participacao_mpe_nacional": pct_mpe,
        "desertos_fornecimento": qtd_desertos,
        "resumo_por_uf": resumo_uf,
    }


async def dados_mapa(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Dados para mapa coropletico: agregacao por UF de participacao de MPEs.

    Retorna todas as 27 UFs, mesmo as sem dados (com zeros).
    """
    # Total de contratos por UF
    stmt_total = (
        select(
            Contratacao.uf,
            func.count(Contrato.id).label("total_contratos"),
            func.coalesce(func.sum(Contrato.valor_contrato), 0).label("valor_total"),
        )
        .join(Contratacao, Contrato.contratacao_id == Contratacao.id)
        .where(Contratacao.uf.is_not(None))
        .group_by(Contratacao.uf)
    )

    # Contratos MPE por UF
    stmt_mpe = (
        select(
            Contratacao.uf,
            func.count(Contrato.id).label("total_mpe"),
            func.coalesce(func.sum(Contrato.valor_contrato), 0).label("valor_mpe"),
        )
        .join(Contratacao, Contrato.contratacao_id == Contratacao.id)
        .where(
            and_(
                Contratacao.uf.is_not(None),
                Contrato.fornecedor_porte.in_(_PORTES_MPE),
            )
        )
        .group_by(Contratacao.uf)
    )

    res_total = (await db.execute(stmt_total)).all()
    res_mpe = (await db.execute(stmt_mpe)).all()

    total_map = {r.uf: r for r in res_total}
    mpe_map = {r.uf: r for r in res_mpe}

    resultado: list[dict[str, Any]] = []
    for uf in _UFS_BRASIL:
        t = total_map.get(uf)
        m = mpe_map.get(uf)

        total_contratos = t.total_contratos if t else 0
        valor_total = float(t.valor_total) if t else 0.0
        total_mpe = m.total_mpe if m else 0
        valor_mpe = float(m.valor_mpe) if m else 0.0
        pct = round((total_mpe / total_contratos) * 100, 1) if total_contratos > 0 else 0.0

        resultado.append({
            "uf": uf,
            "total_contratos": total_contratos,
            "valor_total": valor_total,
            "contratos_mpe": total_mpe,
            "valor_mpe": valor_mpe,
            "percentual_mpe": pct,
        })

    return resultado


async def desertos_fornecimento(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Desertos de fornecimento: divisoes CNAE com alta demanda e poucas/nenhuma MPE.

    Identifica cruzamentos com sinal 'deserto', agrupados por divisao CNAE e UF.
    """
    stmt = (
        select(
            Cruzamento.cnae_divisao,
            Cruzamento.cnae_descricao,
            Cruzamento.uf,
            func.count(Cruzamento.id).label("qtd_ocorrencias"),
            func.avg(Cruzamento.qtd_mpes_regiao).label("media_mpes"),
        )
        .where(Cruzamento.sinal == SinalOportunidade.DESERTO.value)
        .group_by(
            Cruzamento.cnae_divisao,
            Cruzamento.cnae_descricao,
            Cruzamento.uf,
        )
        .order_by(func.count(Cruzamento.id).desc())
        .limit(50)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "cnae_divisao": row.cnae_divisao,
            "cnae_descricao": row.cnae_descricao,
            "uf": row.uf,
            "qtd_ocorrencias": row.qtd_ocorrencias,
            "media_mpes_regiao": round(float(row.media_mpes), 1) if row.media_mpes is not None else 0,
            "severidade": "critico" if row.qtd_ocorrencias >= 10 else "atencao",
        }
        for row in rows
    ]


async def tendencias(
    db: AsyncSession,
    periodo_meses: int = 12,
) -> list[dict[str, Any]]:
    """Tendencias mensais nacionais de participacao de MPEs.

    Retorna serie temporal com total de contratos, contratos MPE e percentual
    para cada mes do periodo solicitado.
    """
    data_inicio = date.today() - timedelta(days=periodo_meses * 30)

    stmt_total = (
        select(
            extract("year", Contrato.data_assinatura).label("ano"),
            extract("month", Contrato.data_assinatura).label("mes"),
            func.count(Contrato.id).label("total"),
            func.coalesce(func.sum(Contrato.valor_contrato), 0).label("valor_total"),
        )
        .where(
            and_(
                Contrato.data_assinatura >= data_inicio,
                Contrato.data_assinatura.is_not(None),
            )
        )
        .group_by("ano", "mes")
        .order_by("ano", "mes")
    )

    stmt_mpe = (
        select(
            extract("year", Contrato.data_assinatura).label("ano"),
            extract("month", Contrato.data_assinatura).label("mes"),
            func.count(Contrato.id).label("total_mpe"),
            func.coalesce(func.sum(Contrato.valor_contrato), 0).label("valor_mpe"),
        )
        .where(
            and_(
                Contrato.data_assinatura >= data_inicio,
                Contrato.data_assinatura.is_not(None),
                Contrato.fornecedor_porte.in_(_PORTES_MPE),
            )
        )
        .group_by("ano", "mes")
        .order_by("ano", "mes")
    )

    res_total = (await db.execute(stmt_total)).all()
    res_mpe = (await db.execute(stmt_mpe)).all()

    mpe_lookup: dict[tuple[int, int], Any] = {
        (int(r.ano), int(r.mes)): r for r in res_mpe
    }

    serie: list[dict[str, Any]] = []
    for row in res_total:
        ano, mes = int(row.ano), int(row.mes)
        total = row.total
        m = mpe_lookup.get((ano, mes))
        total_mpe = m.total_mpe if m else 0
        valor_mpe = float(m.valor_mpe) if m else 0.0
        pct = round((total_mpe / total) * 100, 1) if total > 0 else 0.0

        serie.append({
            "periodo": f"{ano}-{mes:02d}",
            "ano": ano,
            "mes": mes,
            "total_contratos": total,
            "valor_total": float(row.valor_total),
            "contratos_mpe": total_mpe,
            "valor_mpe": valor_mpe,
            "percentual_mpe": pct,
        })

    return serie


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _pct_mpe_nacional(
    db: AsyncSession,
    periodo_inicio: date,
    periodo_fim: date,
) -> float:
    """Calcula o percentual nacional de contratos com MPEs."""
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
            Contrato.data_assinatura >= periodo_inicio,
            Contrato.data_assinatura <= periodo_fim,
        )
    )

    result = (await db.execute(stmt)).one()
    if result.total == 0:
        return 0.0
    return round((result.total_mpe / result.total) * 100, 1)


async def _contar_desertos(db: AsyncSession) -> int:
    """Conta quantos cruzamentos distintos (CNAE+UF) sao desertos."""
    stmt = select(
        func.count(distinct(func.concat(Cruzamento.cnae_divisao, "-", Cruzamento.uf)))
    ).where(Cruzamento.sinal == SinalOportunidade.DESERTO.value)

    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def _resumo_por_uf(
    db: AsyncSession,
    periodo_inicio: date,
    periodo_fim: date,
) -> list[dict[str, Any]]:
    """Resumo agregado por UF: contratacoes, valor e qtd de desertos."""
    stmt = (
        select(
            Contratacao.uf,
            func.count(Contratacao.id).label("total_contratacoes"),
            func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
        )
        .where(
            and_(
                Contratacao.data_publicacao >= periodo_inicio,
                Contratacao.data_publicacao <= periodo_fim,
                Contratacao.uf.is_not(None),
            )
        )
        .group_by(Contratacao.uf)
        .order_by(func.sum(Contratacao.valor_estimado).desc().nulls_last())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "uf": row.uf,
            "total_contratacoes": row.total_contratacoes,
            "valor_total": float(row.valor_total),
        }
        for row in rows
    ]
