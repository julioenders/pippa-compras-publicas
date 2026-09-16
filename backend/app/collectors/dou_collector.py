"""Coletor diário da Seção 3 do Diário Oficial da União (DOU).

Busca publicações de licitação e contratos na Seção 3 do DOU do dia anterior,
extraindo informações relevantes e criando alertas para os perfis SEBRAE.
Este é um coletor suplementar -- o PNCP é a fonte primária.
O DOU captura itens que aparecem antes de serem integrados ao PNCP.
"""

import logging
import re
from datetime import date, timedelta

from app.clients.dou import DOUClient
from app.database import async_session, init_engine
from app.models.alerta import Alerta

logger = logging.getLogger(__name__)

# Termos indicativos de compras públicas na Seção 3
TERMOS_LICITACAO = [
    "licitação",
    "licitacao",
    "pregão",
    "pregao",
    "dispensa",
    "inexigibilidade",
    "concorrência",
    "concorrencia",
    "tomada de preços",
    "tomada de precos",
    "convite",
    "edital",
    "aviso de licitação",
    "aviso de licitacao",
    "resultado de julgamento",
    "extrato de contrato",
    "registro de preços",
    "registro de precos",
    "ata de registro",
]

# Padrão para extrair CNPJ (XX.XXX.XXX/XXXX-XX)
CNPJ_PATTERN = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

# Padrão para extrair valores monetários (R$ X.XXX,XX)
VALOR_PATTERN = re.compile(r"R\$\s*([\d.]+,\d{2})")

# Termos de modalidade para classificação
MODALIDADE_MAP = {
    "pregão": "pregão",
    "pregao": "pregão",
    "dispensa": "dispensa",
    "inexigibilidade": "inexigibilidade",
    "concorrência": "concorrência",
    "concorrencia": "concorrência",
    "tomada de preços": "tomada de preços",
    "tomada de precos": "tomada de preços",
    "convite": "convite",
    "leilão": "leilão",
    "leilao": "leilão",
}

BATCH_SIZE = 50


def _ensure_session():
    """Garante que o engine e async_session estejam inicializados."""
    if async_session is None:
        init_engine()


def _eh_relevante(publicacao: dict) -> bool:
    """Verifica se a publicação contém termos relacionados a compras públicas."""
    texto = " ".join(
        str(v).lower()
        for v in [
            publicacao.get("title", ""),
            publicacao.get("abstract", ""),
            publicacao.get("content", ""),
        ]
    )
    return any(termo in texto for termo in TERMOS_LICITACAO)


def _extrair_cnpj(texto: str) -> str | None:
    """Tenta extrair o primeiro CNPJ encontrado no texto."""
    match = CNPJ_PATTERN.search(texto)
    return match.group(0) if match else None


def _extrair_valor(texto: str) -> str | None:
    """Tenta extrair o primeiro valor monetário encontrado no texto."""
    match = VALOR_PATTERN.search(texto)
    return match.group(0) if match else None


def _extrair_modalidade(texto: str) -> str | None:
    """Identifica a modalidade de licitação mencionada no texto."""
    texto_lower = texto.lower()
    for termo, modalidade in MODALIDADE_MAP.items():
        if termo in texto_lower:
            return modalidade
    return None


def _extrair_uf(publicacao: dict) -> str | None:
    """Tenta extrair a UF do órgão a partir dos campos da publicação."""
    # Alguns resultados do DOU trazem o artType ou hierarquia com a localidade
    hierarchy = publicacao.get("hierarchy", "") or ""
    # Padrão UF em formato "SIGLA" (2 letras maiúsculas isoladas)
    uf_match = re.search(r"\b([A-Z]{2})\b", hierarchy)
    if uf_match:
        uf = uf_match.group(1)
        ufs_validas = {
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        }
        if uf in ufs_validas:
            return uf
    return None


async def coletar_dou_secao3():
    """Coleta publicações da Seção 3 do DOU do dia anterior.

    Busca a Seção 3 (licitações e contratos), filtra por termos relevantes,
    extrai informações estruturadas (CNPJ, valor, modalidade) e cria alertas
    no banco de dados para os perfis SEBRAE.

    Esta função é chamada pelo scheduler sem parâmetros.
    """
    logger.info("Iniciando coleta DOU Seção 3")
    _ensure_session()

    ontem = date.today() - timedelta(days=1)
    data_str = ontem.strftime("%Y-%m-%d")

    client = DOUClient()
    total_relevantes = 0
    total_alertas = 0

    try:
        publicacoes = await client.buscar_secao3(data_publicacao=data_str)
    except Exception:
        logger.exception("Erro ao buscar DOU Seção 3 para data %s", data_str)
        return

    if not publicacoes:
        logger.info("Nenhuma publicação encontrada no DOU Seção 3 para %s", data_str)
        return

    logger.info(
        "DOU Seção 3: %d publicações brutas encontradas para %s",
        len(publicacoes),
        data_str,
    )

    relevantes = [pub for pub in publicacoes if _eh_relevante(pub)]
    total_relevantes = len(relevantes)

    if not relevantes:
        logger.info("Nenhuma publicação relevante encontrada no DOU Seção 3 para %s", data_str)
        return

    async with async_session() as session:
        batch_count = 0
        for pub in relevantes:
            titulo = pub.get("title", "Publicação DOU Seção 3")
            conteudo = pub.get("abstract", "") or pub.get("content", "")
            texto_completo = f"{titulo} {conteudo}"

            cnpj = _extrair_cnpj(texto_completo)
            valor = _extrair_valor(texto_completo)
            modalidade = _extrair_modalidade(texto_completo)
            uf = _extrair_uf(pub)

            # Build alert body with extracted information
            corpo_parts = [f"Publicação: {titulo}"]
            if cnpj:
                corpo_parts.append(f"CNPJ do órgão: {cnpj}")
            if modalidade:
                corpo_parts.append(f"Modalidade: {modalidade}")
            if valor:
                corpo_parts.append(f"Valor: {valor}")
            if pub.get("urlTitle"):
                corpo_parts.append(f"Link: {pub['urlTitle']}")
            corpo = "\n".join(corpo_parts)

            alerta = Alerta(
                perfil="sebrae_uf",
                tipo="dou_secao3",
                titulo=f"DOU Seção 3: {titulo[:200]}",
                corpo=corpo,
                uf=uf,
            )
            session.add(alerta)
            batch_count += 1
            total_alertas += 1

            if batch_count % BATCH_SIZE == 0:
                await session.commit()
                logger.debug("Batch commit DOU: %d alertas", batch_count)

        # Commit remaining
        if batch_count % BATCH_SIZE != 0:
            await session.commit()

    logger.info(
        "Coleta DOU Seção 3 finalizada: %d publicações relevantes, %d alertas criados (data=%s)",
        total_relevantes,
        total_alertas,
        data_str,
    )
