"""Servico de dashboard para o perfil MPE (Micro e Pequena Empresa)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Contratacao, Item, Contrato, Cruzamento
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SINAL_LABEL: dict[str, str] = {
    SinalOportunidade.OPORTUNIDADE.value: "Otima oportunidade",
    SinalOportunidade.COMPETITIVO.value: "Competitivo",
    SinalOportunidade.CAUTELA.value: "Muita concorrencia",
    SinalOportunidade.SATURADO.value: "Mercado saturado",
    SinalOportunidade.DESERTO.value: "Sem concorrentes na regiao",
}


def _formatar_valor(valor: Decimal | float | None) -> str:
    """Formata um valor monetario em linguagem acessivel."""
    if valor is None:
        return "Valor nao informado"
    v = float(valor)
    if v < 1_000:
        return f"R$ {v:,.2f}"
    if v < 1_000_000:
        return f"R$ {v / 1_000:,.1f} mil"
    return f"R$ {v / 1_000_000:,.2f} mi"


def _dias_restantes(data_enc: date | None) -> str:
    if data_enc is None:
        return "Prazo nao informado"
    dias = (data_enc - date.today()).days
    if dias < 0:
        return "Encerrado"
    if dias == 0:
        return "Encerra hoje!"
    if dias == 1:
        return "Encerra amanha"
    return f"Faltam {dias} dias"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def buscar_oportunidades(
    db: AsyncSession,
    cnae: str,
    uf: str,
    municipio_ibge: str | None = None,
    limite: int = 10,
) -> list[dict[str, Any]]:
    """Busca oportunidades abertas para a MPE.

    1. Filtra contratacoes com data_encerramento_proposta >= hoje
    2. Filtra por UF
    3. Join com itens para filtrar por CNAE (via cnae_mapeado)
    4. Left join com cruzamentos para obter sinal/score
    5. Ordena por exclusiva_mpe DESC, score DESC, data_encerramento ASC
    6. Retorna lista formatada com linguagem simplificada

    Caso o banco esteja vazio, faz fallback para a API do PNCP.
    """
    hoje = date.today()

    max_id_sub = (
        select(
            Cruzamento.contratacao_id,
            func.max(Cruzamento.id).label("max_id"),
        )
        .group_by(Cruzamento.contratacao_id)
        .subquery("max_cruzamento")
    )

    cruzamento_sub = (
        select(
            Cruzamento.contratacao_id,
            Cruzamento.sinal,
            Cruzamento.score,
            Cruzamento.qtd_mpes_regiao,
        )
        .join(
            max_id_sub,
            and_(
                Cruzamento.contratacao_id == max_id_sub.c.contratacao_id,
                Cruzamento.id == max_id_sub.c.max_id,
            ),
        )
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
            Contratacao.uf,
            Contratacao.municipio_ibge,
            cruzamento_sub.c.sinal,
            cruzamento_sub.c.score,
            cruzamento_sub.c.qtd_mpes_regiao,
        )
        .join(Item, Item.contratacao_id == Contratacao.id)
        .outerjoin(
            cruzamento_sub,
            cruzamento_sub.c.contratacao_id == Contratacao.id,
        )
        .where(
            and_(
                Contratacao.data_encerramento_proposta >= hoje,
                Contratacao.uf == uf,
                Item.cnae_mapeado.like(f"{cnae[:2]}%"),  # match by CNAE division
            )
        )
    )

    if municipio_ibge:
        stmt = stmt.where(Contratacao.municipio_ibge == municipio_ibge)

    # Ordering: exclusive MPE first, then by score desc, then nearest deadline
    stmt = stmt.order_by(
        Contratacao.exclusiva_mpe.desc(),
        cruzamento_sub.c.score.desc().nulls_last(),
        Contratacao.data_encerramento_proposta.asc(),
    ).limit(limite)

    result = await db.execute(stmt)
    rows = result.all()

    # Fallback: if database is empty, try the PNCP API directly
    if not rows:
        return await _fallback_pncp(cnae, uf, municipio_ibge, limite)

    oportunidades: list[dict[str, Any]] = []
    for row in rows:
        sinal_valor = row.sinal or SinalOportunidade.COMPETITIVO.value
        oportunidades.append({
            "id": row.id,
            "orgao": row.orgao_nome or "Orgao nao identificado",
            "objeto": row.objeto or "Sem descricao",
            "valor": _formatar_valor(row.valor_estimado),
            "valor_estimado": float(row.valor_estimado) if row.valor_estimado else None,
            "exclusiva_mpe": bool(row.exclusiva_mpe),
            "prazo": _dias_restantes(row.data_encerramento_proposta),
            "data_encerramento": row.data_encerramento_proposta.isoformat() if row.data_encerramento_proposta else None,
            "modalidade": row.modalidade_nome,
            "uf": row.uf,
            "municipio_ibge": row.municipio_ibge,
            "sinal": sinal_valor,
            "sinal_descricao": _SINAL_LABEL.get(sinal_valor, sinal_valor),
            "score": float(row.score) if row.score else None,
            "qtd_concorrentes_regiao": row.qtd_mpes_regiao,
        })

    return oportunidades


async def detalhar_oportunidade(
    db: AsyncSession,
    contratacao_id: int,
) -> dict[str, Any]:
    """Retorna o detalhe completo de uma oportunidade com guia passo-a-passo."""
    stmt = (
        select(Contratacao)
        .options(selectinload(Contratacao.items), selectinload(Contratacao.cruzamentos))
        .where(Contratacao.id == contratacao_id)
    )
    result = await db.execute(stmt)
    contratacao = result.scalar_one_or_none()

    if contratacao is None:
        return {"erro": "Oportunidade nao encontrada", "id": contratacao_id}

    # Get the most recent crossing signal
    sinal = SinalOportunidade.COMPETITIVO.value
    score: float | None = None
    if contratacao.cruzamentos:
        ultimo = max(contratacao.cruzamentos, key=lambda c: c.created_at or 0)
        sinal = ultimo.sinal
        score = float(ultimo.score) if ultimo.score else None

    itens = [
        {
            "numero": it.numero_item,
            "descricao": it.descricao,
            "catmat": it.catmat_catser,
            "unidade": it.unidade,
            "quantidade": float(it.quantidade) if it.quantidade else None,
            "valor_unitario": float(it.valor_unitario_estimado) if it.valor_unitario_estimado else None,
            "valor_total": float(it.valor_total_estimado) if it.valor_total_estimado else None,
        }
        for it in contratacao.items
    ]

    # Build step-by-step participation guide
    guia = _montar_guia_participacao(contratacao)

    return {
        "id": contratacao.id,
        "orgao": contratacao.orgao_nome,
        "orgao_cnpj": contratacao.orgao_cnpj,
        "objeto": contratacao.objeto,
        "modalidade": contratacao.modalidade_nome,
        "valor_estimado": float(contratacao.valor_estimado) if contratacao.valor_estimado else None,
        "exclusiva_mpe": contratacao.exclusiva_mpe,
        "data_publicacao": contratacao.data_publicacao.isoformat(),
        "data_abertura_proposta": contratacao.data_abertura_proposta.isoformat() if contratacao.data_abertura_proposta else None,
        "data_encerramento_proposta": contratacao.data_encerramento_proposta.isoformat() if contratacao.data_encerramento_proposta else None,
        "prazo": _dias_restantes(contratacao.data_encerramento_proposta),
        "uf": contratacao.uf,
        "municipio_ibge": contratacao.municipio_ibge,
        "status": contratacao.status,
        "sinal": sinal,
        "sinal_descricao": _SINAL_LABEL.get(sinal, sinal),
        "score": score,
        "itens": itens,
        "guia_participacao": guia,
    }


async def buscar_referencia_precos(
    db: AsyncSession,
    catmat: str,
) -> dict[str, Any]:
    """Busca os ultimos 5 precos praticados para um item CATMAT na tabela de contratos.

    Util para a MPE estimar precos competitivos na sua proposta.
    """
    stmt = (
        select(
            Contrato.fornecedor_nome,
            Contrato.fornecedor_porte,
            Contrato.valor_contrato,
            Contrato.data_assinatura,
            Contratacao.orgao_nome,
            Contratacao.uf,
        )
        .join(Contratacao, Contrato.contratacao_id == Contratacao.id)
        .join(Item, Item.contratacao_id == Contratacao.id)
        .where(Item.catmat_catser == catmat)
        .order_by(Contrato.data_assinatura.desc().nulls_last())
        .limit(5)
    )

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "catmat": catmat,
            "encontrou": False,
            "referencias": [],
            "mensagem": "Nenhum contrato encontrado para este item.",
        }

    valores = [float(r.valor_contrato) for r in rows if r.valor_contrato is not None]

    return {
        "catmat": catmat,
        "encontrou": True,
        "referencias": [
            {
                "fornecedor": r.fornecedor_nome,
                "porte": r.fornecedor_porte,
                "valor": float(r.valor_contrato) if r.valor_contrato else None,
                "data_assinatura": r.data_assinatura.isoformat() if r.data_assinatura else None,
                "orgao": r.orgao_nome,
                "uf": r.uf,
            }
            for r in rows
        ],
        "estatisticas": {
            "menor_valor": min(valores) if valores else None,
            "maior_valor": max(valores) if valores else None,
            "media": round(sum(valores) / len(valores), 2) if valores else None,
        },
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _montar_guia_participacao(contratacao: Contratacao) -> list[dict[str, str]]:
    """Monta um guia passo-a-passo simplificado para a MPE participar."""
    guia: list[dict[str, str]] = [
        {
            "passo": "1",
            "titulo": "Leia o edital completo",
            "descricao": (
                "Acesse o Portal Nacional de Contratacoes Publicas (PNCP) e "
                "busque pelo edital deste orgao. Leia com atencao os requisitos "
                "de habilitacao e as especificacoes tecnicas."
            ),
        },
        {
            "passo": "2",
            "titulo": "Verifique a documentacao",
            "descricao": (
                "Confira se sua empresa possui toda a documentacao exigida: "
                "CNPJ ativo, certidoes negativas (FGTS, INSS, tributos federais), "
                "balanco patrimonial e atestados tecnicos se necessario."
            ),
        },
        {
            "passo": "3",
            "titulo": "Analise os precos",
            "descricao": (
                "Use a funcao 'Referencia de Precos' do PIPPA para ver os "
                "precos praticados em licitacoes anteriores. Prepare uma "
                "proposta competitiva sem comprometer sua margem."
            ),
        },
    ]

    if contratacao.exclusiva_mpe:
        guia.append({
            "passo": "4",
            "titulo": "Licitacao exclusiva para MPE",
            "descricao": (
                "Esta licitacao e exclusiva para micro e pequenas empresas. "
                "Voce tem vantagem! Apenas MPEs podem participar."
            ),
        })
    else:
        guia.append({
            "passo": "4",
            "titulo": "Concorrencia aberta",
            "descricao": (
                "Esta licitacao e aberta a empresas de todos os portes. "
                "Lembre-se de que MPEs tem direito a tratamento diferenciado "
                "conforme a Lei Complementar 123/2006."
            ),
        })

    guia.append({
        "passo": "5",
        "titulo": "Envie sua proposta",
        "descricao": (
            f"Cadastre-se na plataforma de compras indicada no edital "
            f"e envie sua proposta antes do encerramento"
            f"{' em ' + contratacao.data_encerramento_proposta.isoformat() if contratacao.data_encerramento_proposta else ''}."
        ),
    })

    return guia


async def _fallback_pncp(
    cnae: str,
    uf: str,
    municipio_ibge: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    """Fallback: busca diretamente na API do PNCP quando o banco esta vazio."""
    try:
        from app.clients.pncp import PNCPClient

        client = PNCPClient()
        data_fim = (date.today() + timedelta(days=30)).strftime("%Y%m%d")
        resultado = await client.buscar_contratacoes_abertas(
            data_fim=data_fim,
            uf=uf,
            municipio_ibge=municipio_ibge,
            tamanho=limite,
        )

        if not resultado:
            return []

        # The PNCP API may return a list or a dict with a data key
        itens_raw = resultado if isinstance(resultado, list) else resultado.get("data", [])

        return [
            {
                "id": None,
                "orgao": item.get("nomeOrgao", "Orgao nao identificado"),
                "objeto": item.get("objetoCompra", "Sem descricao"),
                "valor": _formatar_valor(item.get("valorTotalEstimado")),
                "valor_estimado": item.get("valorTotalEstimado"),
                "exclusiva_mpe": item.get("srp", False),
                "prazo": _dias_restantes(
                    date.fromisoformat(item["dataEncerramentoProposta"])
                    if item.get("dataEncerramentoProposta")
                    else None
                ),
                "data_encerramento": item.get("dataEncerramentoProposta"),
                "modalidade": item.get("modalidadeNome"),
                "uf": uf,
                "municipio_ibge": municipio_ibge,
                "sinal": SinalOportunidade.COMPETITIVO.value,
                "sinal_descricao": _SINAL_LABEL[SinalOportunidade.COMPETITIVO.value],
                "score": None,
                "qtd_concorrentes_regiao": None,
                "fonte": "pncp_api",
            }
            for item in itens_raw[:limite]
        ]
    except Exception:
        logger.warning("Fallback PNCP tambem falhou para CNAE=%s UF=%s", cnae, uf, exc_info=True)
        return []
