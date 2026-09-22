"""Servico de dashboard para o perfil SEBRAE Nacional."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, case, and_, or_, extract, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contratacao, Contrato, Cruzamento, Item
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)

# Portes considerados MPE
_PORTES_MPE = ("MEI", "ME", "EPP")

# Situacoes consideradas como oportunidades abertas
_SITUACOES_ABERTAS = ("aberta", "futura")

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
    3. Total de contratacoes via SRP (Sistema de Registro de Precos)
    4. Participacao nacional de MPEs (%) -- exclusiva_mpe + cota_reservada
    5. Oportunidades abertas (baseado em situacao)
    6. Contagem de desertos de fornecimento
    7. Detalhamento por UF
    """
    if periodo_fim is None:
        periodo_fim = date.today()
    if periodo_inicio is None:
        periodo_inicio = periodo_fim - timedelta(days=365)

    # 1 & 2 -- Totais nacionais + SRP
    stmt_totais = select(
        func.count(Contratacao.id).label("total"),
        func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
        func.count(
            case(
                (Contratacao.srp == True, Contratacao.id),  # noqa: E712
                else_=None,
            )
        ).label("total_srp"),
    ).where(
        and_(
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
        )
    )
    totais = (await db.execute(stmt_totais)).one()

    # 3 -- Participacao nacional de MPEs (exclusiva_mpe + cota_reservada)
    pct_mpe = await _pct_mpe_nacional(db, periodo_inicio, periodo_fim)

    # 4 -- Desertos de fornecimento
    qtd_desertos = await _contar_desertos(db)

    # 5 -- Resumo por UF
    resumo_uf = await _resumo_por_uf(db, periodo_inicio, periodo_fim)

    # 6 -- Oportunidades abertas (baseado em situacao, nao apenas datas)
    oportunidades_abertas = await _contar_oportunidades_abertas(db)

    return {
        "periodo": {
            "inicio": periodo_inicio.isoformat(),
            "fim": periodo_fim.isoformat(),
        },
        "total_contratacoes": totais.total,
        "valor_total_estimado": float(totais.valor_total),
        "total_srp": totais.total_srp,
        "participacao_mpe_nacional": pct_mpe,
        "oportunidades_abertas": oportunidades_abertas,
        "desertos_fornecimento": qtd_desertos,
        "resumo_por_uf": resumo_uf,
    }


async def dados_mapa(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Dados para mapa coropletico: agregacao por UF de contratacoes.

    Retorna todas as 27 UFs, mesmo as sem dados (com zeros).
    Usa tabela Contratacao diretamente com beneficio MPE (exclusiva_mpe
    ou cota_reservada) em vez de Contrato.
    """
    cond_mpe = _beneficio_mpe_condition()

    stmt = (
        select(
            Contratacao.uf,
            func.count(Contratacao.id).label("total_contratos"),
            func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
            func.count(
                case(
                    (cond_mpe, Contratacao.id),
                    else_=None,
                )
            ).label("total_mpe"),
            func.coalesce(
                func.sum(
                    case(
                        (cond_mpe, Contratacao.valor_estimado),
                        else_=None,
                    )
                ), 0
            ).label("valor_mpe"),
            func.count(
                case(
                    (Contratacao.srp == True, Contratacao.id),  # noqa: E712
                    else_=None,
                )
            ).label("total_srp"),
        )
        .where(
            and_(
                Contratacao.uf.is_not(None),
                Contratacao.uf != "",
            )
        )
        .group_by(Contratacao.uf)
    )

    result = (await db.execute(stmt)).all()
    uf_map = {r.uf: r for r in result}

    resultado: list[dict[str, Any]] = []
    for uf in _UFS_BRASIL:
        r = uf_map.get(uf)
        total = r.total_contratos if r else 0
        total_mpe = r.total_mpe if r else 0
        pct = round((total_mpe / total) * 100, 1) if total > 0 else 0.0

        resultado.append({
            "uf": uf,
            "total_contratos": total,
            "valor_total": float(r.valor_total) if r else 0.0,
            "contratos_mpe": total_mpe,
            "valor_mpe": float(r.valor_mpe) if r else 0.0,
            "percentual_mpe": pct,
            "total_srp": r.total_srp if r else 0,
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
    """Tendencias mensais nacionais de contratacoes.

    Usa Contratacao.data_publicacao em vez de Contrato.data_assinatura.
    Beneficio MPE considera exclusiva_mpe e cota_reservada.
    """
    data_inicio = date.today() - timedelta(days=periodo_meses * 30)

    col_ano = extract("year", Contratacao.data_publicacao).label("ano")
    col_mes = extract("month", Contratacao.data_publicacao).label("mes")
    cond_mpe = _beneficio_mpe_condition()

    stmt = (
        select(
            col_ano,
            col_mes,
            func.count(Contratacao.id).label("total"),
            func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
            func.count(
                case(
                    (cond_mpe, Contratacao.id),
                    else_=None,
                )
            ).label("total_mpe"),
            func.coalesce(
                func.sum(
                    case(
                        (cond_mpe, Contratacao.valor_estimado),
                        else_=None,
                    )
                ), 0
            ).label("valor_mpe"),
            func.count(
                case(
                    (Contratacao.srp == True, Contratacao.id),  # noqa: E712
                    else_=None,
                )
            ).label("total_srp"),
        )
        .where(
            and_(
                Contratacao.data_publicacao >= data_inicio,
                Contratacao.data_publicacao.is_not(None),
            )
        )
        .group_by(col_ano, col_mes)
        .order_by(col_ano, col_mes)
    )

    result = (await db.execute(stmt)).all()

    serie: list[dict[str, Any]] = []
    for row in result:
        ano, mes = int(row.ano), int(row.mes)
        total = row.total
        total_mpe = row.total_mpe
        pct = round((total_mpe / total) * 100, 1) if total > 0 else 0.0

        serie.append({
            "periodo": f"{ano}-{mes:02d}",
            "ano": ano,
            "mes": mes,
            "total_contratos": total,
            "valor_total": float(row.valor_total),
            "contratos_mpe": total_mpe,
            "valor_mpe": float(row.valor_mpe),
            "percentual_mpe": pct,
            "total_srp": row.total_srp,
        })

    return serie


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _beneficio_mpe_condition():
    """Condicao SQLAlchemy para contratacoes com beneficio MPE.

    Considera tanto exclusiva_mpe quanto cota_reservada como beneficios
    para micro e pequenas empresas.
    """
    return or_(
        Contratacao.exclusiva_mpe == True,  # noqa: E712
        Contratacao.cota_reservada == True,  # noqa: E712
    )


async def _pct_mpe_nacional(
    db: AsyncSession,
    periodo_inicio: date,
    periodo_fim: date,
) -> float:
    """Calcula o percentual nacional de contratacoes com beneficio MPE.

    Considera exclusiva_mpe e cota_reservada como beneficios para MPEs.
    """
    stmt = select(
        func.count(Contratacao.id).label("total"),
        func.count(
            case(
                (_beneficio_mpe_condition(), Contratacao.id),
                else_=None,
            )
        ).label("total_mpe"),
    ).where(
        and_(
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
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


async def _contar_oportunidades_abertas(db: AsyncSession) -> int:
    """Conta contratacoes com oportunidades abertas.

    Filtra por situacao em ('aberta', 'futura') ou situacao nula,
    em vez de depender apenas de datas.
    """
    stmt = select(
        func.count(Contratacao.id)
    ).where(
        or_(
            Contratacao.situacao.in_(_SITUACOES_ABERTAS),
            Contratacao.situacao.is_(None),
        )
    )

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
