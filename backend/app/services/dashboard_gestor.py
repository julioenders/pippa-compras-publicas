"""Servico de dashboard para o perfil Gestor Publico."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, case, and_, or_, extract, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contratacao, Item, Contrato
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)

# Meta legal: LC 123/2006 exige pelo menos 25% de compras com MPEs
_META_PARTICIPACAO_MPE = 25.0

# Portes considerados MPE
_PORTES_MPE = ("MEI", "ME", "EPP")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def montar_dashboard(
    db: AsyncSession,
    orgao_cnpj: str,
    periodo_inicio: date | None = None,
    periodo_fim: date | None = None,
) -> dict[str, Any]:
    """Monta o dashboard completo do gestor publico.

    Indicadores:
    1. Total de contratacoes no periodo
    2. Soma do valor estimado
    3. Percentual de contratacoes com beneficio MPE (exclusiva_mpe ou cota_reservada)
    4. Score de conformidade (baseado na meta de 25% MPE)
    5. Top categorias por grupo CATMAT
    6. Total de contratacoes via SRP
    """
    if periodo_fim is None:
        periodo_fim = date.today()
    if periodo_inicio is None:
        periodo_inicio = periodo_fim - timedelta(days=365)

    # 1 & 2 -- Total de contratacoes e valor estimado
    stmt_resumo = select(
        func.count(Contratacao.id).label("total"),
        func.coalesce(func.sum(Contratacao.valor_estimado), 0).label("valor_total"),
    ).where(
        and_(
            Contratacao.orgao_cnpj == orgao_cnpj,
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
        )
    )
    resumo = (await db.execute(stmt_resumo)).one()

    total_contratacoes: int = resumo.total
    valor_total: float = float(resumo.valor_total)

    # 3 -- Percentual de contratos com fornecedores MPE
    pct_mpe = await _calcular_pct_mpe(db, orgao_cnpj, periodo_inicio, periodo_fim)

    # 4 -- Score de conformidade
    conformidade = _calcular_conformidade(pct_mpe)

    # 5 -- Top categorias
    categorias = await _top_categorias(db, orgao_cnpj, periodo_inicio, periodo_fim, limite=10)

    # 6 -- Total de contratacoes via SRP
    stmt_srp = select(
        func.count(Contratacao.id).label("total_srp"),
    ).where(
        and_(
            Contratacao.orgao_cnpj == orgao_cnpj,
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
            Contratacao.srp == True,  # noqa: E712
        )
    )
    srp_result = (await db.execute(stmt_srp)).one()
    total_srp: int = srp_result.total_srp

    return {
        "orgao_cnpj": orgao_cnpj,
        "periodo": {
            "inicio": periodo_inicio.isoformat(),
            "fim": periodo_fim.isoformat(),
        },
        "total_contratacoes": total_contratacoes,
        "valor_total_estimado": valor_total,
        "participacao_mpe": {
            "percentual": pct_mpe,
            "meta_legal": _META_PARTICIPACAO_MPE,
            "atingiu_meta": pct_mpe >= _META_PARTICIPACAO_MPE,
        },
        "conformidade": conformidade,
        "top_categorias": categorias,
        "total_srp": total_srp,
    }


async def serie_participacao_mpe(
    db: AsyncSession,
    orgao_cnpj: str,
    periodo_meses: int = 12,
) -> dict[str, Any]:
    """Serie temporal mensal de participacao % de MPEs nos contratos do orgao."""
    data_inicio = date.today() - timedelta(days=periodo_meses * 30)

    # Total de contratos por mes
    stmt_total = (
        select(
            extract("year", Contrato.data_assinatura).label("ano"),
            extract("month", Contrato.data_assinatura).label("mes"),
            func.count(Contrato.id).label("total"),
        )
        .join(Contratacao, Contrato.contratacao_id == Contratacao.id)
        .where(
            and_(
                Contratacao.orgao_cnpj == orgao_cnpj,
                Contrato.data_assinatura >= data_inicio,
                Contrato.data_assinatura.is_not(None),
            )
        )
        .group_by("ano", "mes")
        .order_by("ano", "mes")
    )

    # Contratos MPE por mes
    stmt_mpe = (
        select(
            extract("year", Contrato.data_assinatura).label("ano"),
            extract("month", Contrato.data_assinatura).label("mes"),
            func.count(Contrato.id).label("total_mpe"),
        )
        .join(Contratacao, Contrato.contratacao_id == Contratacao.id)
        .where(
            and_(
                Contratacao.orgao_cnpj == orgao_cnpj,
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

    # Build lookup for MPE counts
    mpe_lookup: dict[tuple[int, int], int] = {
        (int(r.ano), int(r.mes)): r.total_mpe for r in res_mpe
    }

    serie: list[dict[str, Any]] = []
    for row in res_total:
        ano, mes = int(row.ano), int(row.mes)
        total = row.total
        total_mpe = mpe_lookup.get((ano, mes), 0)
        pct = round((total_mpe / total) * 100, 1) if total > 0 else 0.0
        serie.append({
            "ano": ano,
            "mes": mes,
            "periodo": f"{ano}-{mes:02d}",
            "total_contratos": total,
            "contratos_mpe": total_mpe,
            "percentual_mpe": pct,
            "meta": _META_PARTICIPACAO_MPE,
        })

    return {
        "orgao_cnpj": orgao_cnpj,
        "periodo_meses": periodo_meses,
        "serie": serie,
    }


async def benchmark_precos(
    db: AsyncSession,
    catmat: str,
    uf: str | None = None,
) -> dict[str, Any]:
    """Benchmarking de precos entre orgaos para um item CATMAT.

    Compara o preco praticado pelo orgao com a media e mediana nacional
    para o mesmo item, permitindo ao gestor avaliar eficiencia.
    """
    filtros = [Item.catmat_catser == catmat]
    if uf:
        filtros.append(Contratacao.uf == uf)

    stmt = (
        select(
            Contratacao.orgao_nome,
            Contratacao.orgao_cnpj,
            Contratacao.uf,
            Item.valor_unitario_estimado,
            Item.descricao,
            Contrato.valor_contrato,
            Contrato.data_assinatura,
        )
        .join(Contratacao, Item.contratacao_id == Contratacao.id)
        .outerjoin(Contrato, Contrato.contratacao_id == Contratacao.id)
        .where(and_(*filtros))
        .order_by(Contrato.data_assinatura.desc().nulls_last())
        .limit(50)
    )

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "catmat": catmat,
            "encontrou": False,
            "registros": [],
            "estatisticas": {},
        }

    # Collect values for statistics
    valores_unitarios = [
        float(r.valor_unitario_estimado)
        for r in rows
        if r.valor_unitario_estimado is not None
    ]
    valores_contrato = [
        float(r.valor_contrato)
        for r in rows
        if r.valor_contrato is not None
    ]

    registros = [
        {
            "orgao": r.orgao_nome,
            "orgao_cnpj": r.orgao_cnpj,
            "uf": r.uf,
            "descricao_item": r.descricao,
            "valor_unitario_estimado": float(r.valor_unitario_estimado) if r.valor_unitario_estimado else None,
            "valor_contrato": float(r.valor_contrato) if r.valor_contrato else None,
            "data_contrato": r.data_assinatura.isoformat() if r.data_assinatura else None,
        }
        for r in rows
    ]

    return {
        "catmat": catmat,
        "encontrou": True,
        "total_registros": len(registros),
        "registros": registros,
        "estatisticas": {
            "valor_unitario": _resumo_estatistico(valores_unitarios),
            "valor_contrato": _resumo_estatistico(valores_contrato),
        },
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _calcular_pct_mpe(
    db: AsyncSession,
    orgao_cnpj: str,
    periodo_inicio: date,
    periodo_fim: date,
) -> float:
    """Calcula o percentual de contratacoes com beneficio MPE (LC 123/2006).

    Uma contratacao conta como beneficio MPE se ``exclusiva_mpe`` for True
    **ou** ``cota_reservada`` for True.
    """
    stmt = select(
        func.count(Contratacao.id).label("total"),
        func.count(
            case(
                (
                    or_(
                        Contratacao.exclusiva_mpe == True,   # noqa: E712
                        Contratacao.cota_reservada == True,   # noqa: E712
                    ),
                    Contratacao.id,
                ),
                else_=None,
            )
        ).label("total_mpe"),
    ).where(
        and_(
            Contratacao.orgao_cnpj == orgao_cnpj,
            Contratacao.data_publicacao >= periodo_inicio,
            Contratacao.data_publicacao <= periodo_fim,
        )
    )

    result = (await db.execute(stmt)).one()
    if result.total == 0:
        return 0.0
    return round((result.total_mpe / result.total) * 100, 1)


def _calcular_conformidade(pct_mpe: float) -> dict[str, Any]:
    """Calcula o score de conformidade baseado na meta legal de 25%."""
    if pct_mpe >= _META_PARTICIPACAO_MPE:
        nivel = "conforme"
        cor = "verde"
        mensagem = f"Parabens! Participacao de MPEs ({pct_mpe:.1f}%) acima da meta de {_META_PARTICIPACAO_MPE}%."
    elif pct_mpe >= _META_PARTICIPACAO_MPE * 0.8:  # >= 20%
        nivel = "atencao"
        cor = "amarelo"
        mensagem = f"Participacao de MPEs ({pct_mpe:.1f}%) proxima da meta de {_META_PARTICIPACAO_MPE}%."
    else:
        nivel = "critico"
        cor = "vermelho"
        mensagem = f"Participacao de MPEs ({pct_mpe:.1f}%) abaixo da meta de {_META_PARTICIPACAO_MPE}%."

    return {
        "score": round(min(100.0, (pct_mpe / _META_PARTICIPACAO_MPE) * 100), 1),
        "nivel": nivel,
        "cor": cor,
        "mensagem": mensagem,
    }


async def _top_categorias(
    db: AsyncSession,
    orgao_cnpj: str,
    periodo_inicio: date,
    periodo_fim: date,
    limite: int = 10,
) -> list[dict[str, Any]]:
    """Retorna as top categorias (por grupo CATMAT) do orgao no periodo."""
    # Group by the first 4 digits of catmat_catser as the category group
    grupo = func.substr(Item.catmat_catser, 1, 4).label("grupo_catmat")

    stmt = (
        select(
            grupo,
            func.count(Item.id).label("qtd_itens"),
            func.coalesce(func.sum(Item.valor_total_estimado), 0).label("valor_total"),
        )
        .join(Contratacao, Item.contratacao_id == Contratacao.id)
        .where(
            and_(
                Contratacao.orgao_cnpj == orgao_cnpj,
                Contratacao.data_publicacao >= periodo_inicio,
                Contratacao.data_publicacao <= periodo_fim,
                Item.catmat_catser.is_not(None),
            )
        )
        .group_by(grupo)
        .order_by(func.sum(Item.valor_total_estimado).desc().nulls_last())
        .limit(limite)
    )

    result = await db.execute(stmt)
    return [
        {
            "grupo_catmat": row.grupo_catmat,
            "qtd_itens": row.qtd_itens,
            "valor_total": float(row.valor_total),
        }
        for row in result.all()
    ]


def _resumo_estatistico(valores: list[float]) -> dict[str, float | None]:
    """Calcula resumo estatistico basico de uma lista de valores."""
    if not valores:
        return {"minimo": None, "maximo": None, "media": None, "mediana": None}

    valores_ord = sorted(valores)
    n = len(valores_ord)
    mediana = (
        valores_ord[n // 2]
        if n % 2 == 1
        else (valores_ord[n // 2 - 1] + valores_ord[n // 2]) / 2
    )

    return {
        "minimo": min(valores),
        "maximo": max(valores),
        "media": round(sum(valores) / n, 2),
        "mediana": round(mediana, 2),
    }
