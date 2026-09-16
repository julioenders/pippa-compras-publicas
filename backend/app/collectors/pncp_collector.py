"""Coletor diário de contratações do PNCP (Portal Nacional de Contratações Públicas).

Executa a ingestão de contratações publicadas no dia anterior, classificando-as
e persistindo no banco de dados com seus respectivos itens.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.clients.pncp import PNCPClient
from app.database import async_session, init_engine
from app.models.contratacao import Contratacao
from app.models.item import Item
from app.services.classificador import classificar

logger = logging.getLogger(__name__)

# Modalidades a coletar: pregão, dispensa, concorrência, inexigibilidade,
# leilão, diálogo competitivo, concurso, credenciamento
MODALIDADES = [5, 6, 8, 4, 9, 1, 2, 3, 7]

BATCH_SIZE = 50


def _ensure_session():
    """Garante que o engine e async_session estejam inicializados."""
    if async_session is None:
        init_engine()


def _parse_date_field(value: str | None) -> date | None:
    """Converte string ISO para date, retornando None se inválido."""
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _parse_decimal(value) -> Decimal | None:
    """Converte valor numérico para Decimal, retornando None se inválido."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def _contratacao_existe(session, orgao_cnpj: str, ano: int, sequencial: int) -> bool:
    """Verifica se a contratação já existe no banco pelo identificador único."""
    stmt = select(Contratacao.id).where(
        Contratacao.orgao_cnpj == orgao_cnpj,
        Contratacao.ano == ano,
        Contratacao.sequencial == sequencial,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


def _extrair_contratacao(raw: dict) -> dict:
    """Extrai campos da contratação a partir do JSON bruto do PNCP."""
    classificacao = classificar(raw)

    orgao = raw.get("orgaoEntidade", {})
    orgao_cnpj = orgao.get("cnpj", raw.get("cnpj", ""))
    orgao_nome = orgao.get("razaoSocial", raw.get("nomeOrgao"))

    unidade = raw.get("unidadeOrgao", {})
    uf_extraido = unidade.get("ufSigla") or raw.get("uf") or classificacao.uf or ""
    municipio_ibge = unidade.get("codigoIbge") or raw.get("codigoMunicipioIbge") or classificacao.municipio_ibge

    return {
        "orgao_cnpj": orgao_cnpj,
        "orgao_nome": orgao_nome,
        "ano": raw.get("anoCompra", 0),
        "sequencial": raw.get("sequencialCompra", 0),
        "objeto": raw.get("objetoCompra") or raw.get("descricao"),
        "modalidade": raw.get("modalidadeId", 0),
        "modalidade_nome": raw.get("modalidadeNome") or classificacao.modalidade,
        "valor_estimado": _parse_decimal(raw.get("valorTotalEstimado")),
        "esfera": classificacao.esfera.value,
        "uf": uf_extraido,
        "municipio_ibge": municipio_ibge,
        "exclusiva_mpe": classificacao.exclusiva_mpe,
        "data_publicacao": _parse_date_field(raw.get("dataPublicacaoPncp"))
        or date.today(),
        "data_abertura_proposta": _parse_date_field(raw.get("dataAberturaProposta")),
        "data_encerramento_proposta": _parse_date_field(
            raw.get("dataEncerramentoProposta")
        ),
        "status": raw.get("situacaoCompraDescricao"),
        "raw_json": raw,
    }


def _extrair_itens(raw: dict, contratacao_id: int) -> list[dict]:
    """Extrai os itens de uma contratação a partir do JSON bruto."""
    itens_raw = raw.get("itens", [])
    itens = []
    for item_raw in itens_raw:
        itens.append(
            {
                "contratacao_id": contratacao_id,
                "numero_item": item_raw.get("numeroItem"),
                "catmat_catser": item_raw.get("materialOuServico")
                or item_raw.get("codigoItemCatalogo"),
                "descricao": item_raw.get("descricao"),
                "unidade": item_raw.get("unidadeMedida"),
                "quantidade": _parse_decimal(item_raw.get("quantidade")),
                "valor_unitario_estimado": _parse_decimal(
                    item_raw.get("valorUnitarioEstimado")
                ),
                "valor_total_estimado": _parse_decimal(
                    item_raw.get("valorTotalEstimado")
                ),
                "cnae_mapeado": item_raw.get("cnaeMapeado"),
            }
        )
    return itens


async def _coletar_modalidade(
    client: PNCPClient,
    data_str: str,
    modalidade: int,
) -> tuple[int, int]:
    """Coleta contratações de uma modalidade específica para uma data.

    Returns:
        Tuple (novos, ignorados) com contagem de registros.
    """
    _ensure_session()
    novos = 0
    ignorados = 0
    pagina = 1

    while True:
        try:
            resultado = await client.buscar_contratacoes(
                data_inicio=data_str,
                data_fim=data_str,
                modalidade=modalidade,
                pagina=pagina,
                tamanho=BATCH_SIZE,
            )
        except Exception:
            logger.exception(
                "Erro ao buscar PNCP modalidade=%d pagina=%d data=%s",
                modalidade,
                pagina,
                data_str,
            )
            break

        # The PNCP API returns a list directly or a dict with "data" key
        if isinstance(resultado, dict):
            registros = resultado.get("data", resultado.get("resultado", []))
        elif isinstance(resultado, list):
            registros = resultado
        else:
            registros = []

        if not registros:
            break

        async with async_session() as session:
            batch_novos = 0
            for raw in registros:
                orgao = raw.get("orgaoEntidade", {})
                orgao_cnpj = orgao.get("cnpj", raw.get("cnpj", ""))
                ano = raw.get("anoCompra", 0)
                sequencial = raw.get("sequencialCompra", 0)

                if not orgao_cnpj or not ano or not sequencial:
                    logger.warning(
                        "Contratação sem identificador completo: cnpj=%s ano=%s seq=%s",
                        orgao_cnpj,
                        ano,
                        sequencial,
                    )
                    ignorados += 1
                    continue

                if await _contratacao_existe(session, orgao_cnpj, ano, sequencial):
                    ignorados += 1
                    continue

                dados = _extrair_contratacao(raw)
                contratacao = Contratacao(**dados)
                session.add(contratacao)
                await session.flush()  # Get the generated ID

                itens_dados = _extrair_itens(raw, contratacao.id)
                for item_dict in itens_dados:
                    session.add(Item(**item_dict))

                batch_novos += 1

                # Commit in batches for efficiency
                if batch_novos % BATCH_SIZE == 0:
                    await session.commit()
                    logger.debug(
                        "Batch commit: %d registros (modalidade=%d, pagina=%d)",
                        batch_novos,
                        modalidade,
                        pagina,
                    )

            # Commit remaining records in this page
            if batch_novos % BATCH_SIZE != 0:
                await session.commit()

            novos += batch_novos

        # If fewer records than page size, we reached the last page
        if len(registros) < BATCH_SIZE:
            break

        pagina += 1

    return novos, ignorados


async def coletar_contratacoes_diarias():
    """Coleta as contratações publicadas no dia anterior no PNCP.

    Itera por todas as modalidades configuradas, paginando os resultados,
    classificando cada contratação e persistindo no banco com seus itens.
    Duplicatas são detectadas pela constraint única (orgao_cnpj, ano, sequencial).

    Esta função é chamada pelo scheduler sem parâmetros.
    """
    logger.info("Iniciando coleta diária PNCP")
    _ensure_session()

    ontem = date.today() - timedelta(days=1)
    data_str = ontem.strftime("%Y%m%d")

    client = PNCPClient()
    total_novos = 0
    total_ignorados = 0

    for modalidade in MODALIDADES:
        try:
            novos, ignorados = await _coletar_modalidade(client, data_str, modalidade)
            total_novos += novos
            total_ignorados += ignorados
            logger.info(
                "Modalidade %d: %d novas, %d ignoradas (data=%s)",
                modalidade,
                novos,
                ignorados,
                data_str,
            )
        except Exception:
            logger.exception(
                "Erro fatal na coleta da modalidade %d para data %s",
                modalidade,
                data_str,
            )
            # Continue with next modalidade - never crash the scheduler
            continue

    logger.info(
        "Coleta diária PNCP finalizada: %d novas contratações, %d ignoradas (data=%s)",
        total_novos,
        total_ignorados,
        data_str,
    )
