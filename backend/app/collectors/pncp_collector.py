"""Coletor diario de contratacoes do PNCP alinhado a Matriz DOU+PNCP.

Executa a ingestao de contratacoes publicadas no dia anterior, extraindo
todos os campos de prioridade Altissima e Alta da matriz: objeto, itens
com beneficio MPE por item, situacao, datas, link de participacao,
criterio de julgamento, modo de disputa, SRP, orcamento sigiloso.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.clients.pncp import PNCPClient
from app.database import async_session, init_engine
from app.models.contratacao import Contratacao
from app.models.evento import EventoContratacao
from app.models.item import Item
from app.services.classificador import classificar

logger = logging.getLogger(__name__)

MODALIDADES = [5, 6, 8, 4, 9, 1, 2, 3, 7, 11, 10]

BATCH_SIZE = 50


def _ensure_session():
    if async_session is None:
        init_engine()


def _parse_date_field(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _parse_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def _contratacao_existe(session, orgao_cnpj: str, ano: int, sequencial: int) -> int | None:
    stmt = select(Contratacao.id).where(
        Contratacao.orgao_cnpj == orgao_cnpj,
        Contratacao.ano == ano,
        Contratacao.sequencial == sequencial,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _extrair_contratacao(raw: dict) -> dict:
    """Extrai campos da contratacao alinhados a matriz."""
    classificacao = classificar(raw)

    orgao = raw.get("orgaoEntidade", {})
    orgao_cnpj = orgao.get("cnpj", raw.get("cnpj", ""))
    orgao_nome = orgao.get("razaoSocial", raw.get("nomeOrgao"))

    unidade = raw.get("unidadeOrgao", {})
    uf_extraido = unidade.get("ufSigla") or raw.get("uf") or classificacao.uf or ""
    municipio_ibge = (
        unidade.get("codigoIbge")
        or raw.get("codigoMunicipioIbge")
        or classificacao.municipio_ibge
    )
    municipio_nome = unidade.get("nomeUnidade")

    link_sistema = raw.get("linkSistemaOrigem") or raw.get("linkProcesso")
    link_edital = raw.get("linkEdital")

    return {
        "orgao_cnpj": orgao_cnpj,
        "orgao_nome": orgao_nome,
        "unidade_codigo": unidade.get("codigoUnidade"),
        "unidade_nome": unidade.get("nomeUnidade"),
        "ano": raw.get("anoCompra", 0),
        "sequencial": raw.get("sequencialCompra", 0),
        "numero_processo": raw.get("processo"),
        "numero_contratacao": raw.get("numeroContratacao"),
        "objeto": raw.get("objetoCompra") or raw.get("descricao"),
        "informacao_complementar": raw.get("informacaoComplementar"),
        "modalidade": raw.get("modalidadeId", 0),
        "modalidade_nome": raw.get("modalidadeNome") or classificacao.modalidade,
        "tipo_instrumento": classificacao.tipo_instrumento.value,
        "amparo_legal": raw.get("amparoLegalNome") or raw.get("amparoLegal"),
        "valor_estimado": _parse_decimal(raw.get("valorTotalEstimado")),
        "orcamento_sigiloso": classificacao.orcamento_sigiloso,
        "esfera": classificacao.esfera.value,
        "poder": raw.get("poderNome"),
        "uf": uf_extraido,
        "municipio_ibge": municipio_ibge,
        "municipio_nome": municipio_nome,
        "beneficio_mpe": classificacao.beneficio_mpe.value,
        "exclusiva_mpe": classificacao.exclusiva_mpe,
        "cota_reservada": classificacao.cota_reservada,
        "subcontratacao_mpe": classificacao.subcontratacao_mpe,
        "srp": classificacao.srp,
        "data_publicacao": _parse_date_field(raw.get("dataPublicacaoPncp")) or date.today(),
        "data_abertura_proposta": _parse_date_field(raw.get("dataAberturaProposta")),
        "data_encerramento_proposta": _parse_date_field(raw.get("dataEncerramentoProposta")),
        "criterio_julgamento": classificacao.criterio_julgamento.value,
        "modo_disputa": classificacao.modo_disputa.value,
        "link_sistema_origem": link_sistema,
        "link_edital": link_edital,
        "situacao": classificacao.situacao.value,
        "situacao_descricao": raw.get("situacaoCompraDescricao"),
        "data_ultima_atualizacao": _parse_date_field(raw.get("dataAtualizacao")),
        "margem_preferencia": bool(raw.get("margemPreferencia")),
        "exigencia_conteudo_nacional": bool(raw.get("exigenciaConteudoNacional")),
        "fonte": "pncp",
        "raw_json": raw,
    }


def _extrair_itens(raw: dict, contratacao_id: int) -> list[dict]:
    """Extrai itens com todos os campos da matriz (beneficio MPE, NCM/NBS)."""
    itens_raw = raw.get("itens", [])
    itens = []
    for item_raw in itens_raw:
        beneficio_item = item_raw.get("tipoBeneficioNome", "")
        is_cota = "cota" in beneficio_item.lower() if beneficio_item else False

        itens.append({
            "contratacao_id": contratacao_id,
            "numero_item": item_raw.get("numeroItem"),
            "catmat_catser": (
                item_raw.get("materialOuServico")
                or item_raw.get("codigoItemCatalogo")
            ),
            "tipo_catalogo": item_raw.get("tipoCatalogo"),
            "descricao": item_raw.get("descricao"),
            "material_ou_servico": item_raw.get("materialOuServicoNome"),
            "unidade": item_raw.get("unidadeMedida"),
            "quantidade": _parse_decimal(item_raw.get("quantidade")),
            "valor_unitario_estimado": _parse_decimal(item_raw.get("valorUnitarioEstimado")),
            "valor_total_estimado": _parse_decimal(item_raw.get("valorTotalEstimado")),
            "ncm": item_raw.get("codigoNcm"),
            "nbs": item_raw.get("codigoNbs"),
            "beneficio_mpe": item_raw.get("tipoBeneficioNome"),
            "cota_reservada": is_cota,
            "cnae_mapeado": item_raw.get("cnaeMapeado"),
        })
    return itens


async def _atualizar_contratacao_existente(
    session, contratacao_id: int, raw: dict
) -> bool:
    """Atualiza situacao de contratacao existente se mudou.

    Cria evento de ciclo de vida quando detecta mudanca de status.
    Retorna True se houve atualizacao.
    """
    stmt = select(Contratacao).where(Contratacao.id == contratacao_id)
    result = await session.execute(stmt)
    contratacao = result.scalar_one_or_none()
    if not contratacao:
        return False

    nova_situacao_desc = raw.get("situacaoCompraDescricao")
    if not nova_situacao_desc:
        return False

    situacao_anterior = contratacao.situacao_descricao
    if situacao_anterior == nova_situacao_desc:
        return False

    from app.services.classificador import classificar_situacao
    nova_situacao = classificar_situacao(nova_situacao_desc)

    evento = EventoContratacao(
        contratacao_id=contratacao_id,
        tipo="atualizacao_status",
        descricao=f"Status alterado de '{situacao_anterior}' para '{nova_situacao_desc}'",
        campo_alterado="situacao",
        valor_anterior=situacao_anterior,
        valor_novo=nova_situacao_desc,
        fonte="pncp",
    )
    session.add(evento)

    contratacao.situacao = nova_situacao.value
    contratacao.situacao_descricao = nova_situacao_desc
    contratacao.data_ultima_atualizacao = _parse_date_field(raw.get("dataAtualizacao"))

    link = raw.get("linkSistemaOrigem") or raw.get("linkProcesso")
    if link and not contratacao.link_sistema_origem:
        contratacao.link_sistema_origem = link

    return True


async def _coletar_modalidade(
    client: PNCPClient,
    data_str: str,
    modalidade: int,
) -> tuple[int, int, int]:
    """Coleta contratacoes de uma modalidade.

    Returns:
        Tuple (novos, atualizados, ignorados).
    """
    _ensure_session()
    novos = 0
    atualizados = 0
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
                modalidade, pagina, data_str,
            )
            break

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
                    ignorados += 1
                    continue

                existing_id = await _contratacao_existe(session, orgao_cnpj, ano, sequencial)
                if existing_id:
                    updated = await _atualizar_contratacao_existente(session, existing_id, raw)
                    if updated:
                        atualizados += 1
                    else:
                        ignorados += 1
                    continue

                dados = _extrair_contratacao(raw)
                contratacao = Contratacao(**dados)
                session.add(contratacao)
                await session.flush()

                itens_dados = _extrair_itens(raw, contratacao.id)
                for item_dict in itens_dados:
                    session.add(Item(**item_dict))

                batch_novos += 1

                if batch_novos % BATCH_SIZE == 0:
                    await session.commit()

            if batch_novos % BATCH_SIZE != 0:
                await session.commit()

            novos += batch_novos

        if len(registros) < BATCH_SIZE:
            break

        pagina += 1

    return novos, atualizados, ignorados


async def coletar_contratacoes_diarias():
    """Coleta contratacoes publicadas no dia anterior no PNCP.

    Alinhado a matriz: itera por todas as modalidades incluindo
    pre-qualificacao (11) e manifestacao de interesse (10).
    Atualiza contratacoes existentes quando detecta mudanca de status.
    """
    logger.info("Iniciando coleta diaria PNCP")
    _ensure_session()

    ontem = date.today() - timedelta(days=1)
    data_str = ontem.strftime("%Y%m%d")

    client = PNCPClient()
    total_novos = 0
    total_atualizados = 0
    total_ignorados = 0

    for modalidade in MODALIDADES:
        try:
            novos, atualizados, ignorados = await _coletar_modalidade(
                client, data_str, modalidade
            )
            total_novos += novos
            total_atualizados += atualizados
            total_ignorados += ignorados
            logger.info(
                "Modalidade %d: %d novas, %d atualizadas, %d ignoradas (data=%s)",
                modalidade, novos, atualizados, ignorados, data_str,
            )
        except Exception:
            logger.exception(
                "Erro fatal na coleta da modalidade %d para data %s",
                modalidade, data_str,
            )
            continue

    logger.info(
        "Coleta diaria PNCP finalizada: %d novas, %d atualizadas, %d ignoradas (data=%s)",
        total_novos, total_atualizados, total_ignorados, data_str,
    )
