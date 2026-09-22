"""Coletor primario da Secao 3 do Diario Oficial da Uniao (DOU).

Busca publicacoes de licitacao e contratos na Secao 3 do DOU,
extrai informacoes estruturadas e cria registros de Contratacao, Item,
EventoContratacao e Alerta no banco de dados.

O DOU Secao 3 e a fonte primaria de dados do sistema.
"""

import hashlib
import logging
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.clients.dou import DOUClient
from app.database import async_session, init_engine
from app.models.alerta import Alerta
from app.models.contratacao import Contratacao
from app.models.evento import EventoContratacao
from app.models.item import Item

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

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
    "credenciamento",
    "chamamento público",
    "chamamento publico",
]

# ---------------------------------------------------------------------------
# Regex compilados
# ---------------------------------------------------------------------------

CNPJ_PATTERN = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

VALOR_PATTERN = re.compile(r"R\$\s*([\d.]+,\d{2})")

PROCESSO_PATTERN = re.compile(
    r"(?:Processo|Proc\.?)\s*(?:n[.ºo°]\s*)?(\d[\d./-]+\d)",
    re.IGNORECASE,
)

DATA_NUMERICA_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")

DATA_EXTENSO_PATTERN = re.compile(
    r"(\d{1,2})\s+de\s+"
    r"(janeiro|fevereiro|março|marco|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)"
    r"\s+de\s+(\d{4})",
    re.IGNORECASE,
)

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}

# ---------------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------------

# keyword -> (modalidade_nome, tipo_instrumento)
# Entries ordered longest-first so broader terms don't shadow narrower ones.
MODALIDADE_MAP = {
    "pregão eletrônico": ("pregão eletrônico", "pregao_eletronico"),
    "pregao eletronico": ("pregão eletrônico", "pregao_eletronico"),
    "pregão presencial": ("pregão presencial", "aviso_licitacao"),
    "pregao presencial": ("pregão presencial", "aviso_licitacao"),
    "pregão": ("pregão", "pregao_eletronico"),
    "pregao": ("pregão", "pregao_eletronico"),
    "concorrência": ("concorrência", "concorrencia"),
    "concorrencia": ("concorrência", "concorrencia"),
    "dispensa eletrônica": ("dispensa eletrônica", "dispensa_eletronica"),
    "dispensa eletronica": ("dispensa eletrônica", "dispensa_eletronica"),
    "dispensa de licitação": ("dispensa", "dispensa_ratificacao"),
    "dispensa de licitacao": ("dispensa", "dispensa_ratificacao"),
    "dispensa": ("dispensa", "dispensa_ratificacao"),
    "inexigibilidade": ("inexigibilidade", "inexigibilidade"),
    "tomada de preços": ("tomada de preços", "aviso_licitacao"),
    "tomada de precos": ("tomada de preços", "aviso_licitacao"),
    "convite": ("convite", "aviso_licitacao"),
    "leilão": ("leilão", "aviso_licitacao"),
    "leilao": ("leilão", "aviso_licitacao"),
    "concurso": ("concurso", "concurso"),
    "credenciamento": ("credenciamento", "credenciamento"),
    "chamamento público": ("chamamento público", "chamamento_publico"),
    "chamamento publico": ("chamamento público", "chamamento_publico"),
    "diálogo competitivo": ("diálogo competitivo", "dialogo_competitivo"),
    "dialogo competitivo": ("diálogo competitivo", "dialogo_competitivo"),
}

# Pre-sorted keys (longest first) for deterministic matching.
_MODALIDADE_KEYS_SORTED = sorted(MODALIDADE_MAP.keys(), key=len, reverse=True)

# keyword in title/text -> tipo_ato
TIPO_ATO_KEYWORDS = [
    ("retificação", "retificacao"),
    ("retificacao", "retificacao"),
    ("errata", "retificacao"),
    ("suspensão", "suspensao"),
    ("suspensao", "suspensao"),
    ("revogação", "revogacao"),
    ("revogacao", "revogacao"),
    ("anulação", "anulacao"),
    ("anulacao", "anulacao"),
    ("adiamento", "adiamento"),
    ("prorrogação", "adiamento"),
    ("prorrogacao", "adiamento"),
    ("reabertura", "reabertura"),
    ("resultado de julgamento", "resultado"),
    ("resultado de habilitação", "resultado"),
    ("resultado de habilitacao", "resultado"),
    ("adjudicação", "adjudicacao"),
    ("adjudicacao", "adjudicacao"),
    ("homologação", "homologacao"),
    ("homologacao", "homologacao"),
    ("extrato de contrato", "extrato"),
    ("extrato de ata", "extrato"),
    ("extrato de inexigibilidade", "extrato"),
    ("extrato de dispensa", "extrato"),
    ("extrato de termo aditivo", "aditivo"),
    ("aviso de licitação", "aviso"),
    ("aviso de licitacao", "aviso"),
    ("aviso de dispensa", "aviso"),
    ("aviso de chamamento", "aviso"),
    ("edital de licitação", "aviso"),
    ("edital de licitacao", "aviso"),
    ("edital", "aviso"),
]

# tipo_ato -> situacao (SituacaoContratacao values)
SITUACAO_MAP = {
    "aviso": "aberta",
    "resultado": "encerrada",
    "adjudicacao": "encerrada",
    "homologacao": "encerrada",
    "extrato": "encerrada",
    "aditivo": "encerrada",
    "retificacao": "aberta",
    "suspensao": "suspensa",
    "revogacao": "revogada",
    "anulacao": "anulada",
    "adiamento": "aberta",
    "reabertura": "aberta",
}

# Tipos de ato que atualizam um registro existente (nao criam novo).
TIPOS_ATUALIZACAO = frozenset({
    "retificacao", "suspensao", "revogacao", "anulacao",
    "adiamento", "reabertura",
})

UFS_VALIDAS = frozenset({
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
})

BATCH_SIZE = 50


# ---------------------------------------------------------------------------
# Funcoes auxiliares de extracao
# ---------------------------------------------------------------------------

def _extrair_objeto(texto: str) -> str | None:
    """Extrai o objeto da contratacao a partir do texto da publicacao.

    Tenta dois padroes:
    1. Campo explicito ``OBJETO:`` seguido de texto ate o proximo rotulo.
    2. Construcao ``para <descricao>`` apos nome de modalidade.
    """
    # Padrao 1 -- campo "OBJETO:"
    match = re.search(
        r"(?:OBJETO|Objeto)\s*:\s*(.+?)"
        r"(?:\n\s*\n|"
        r"(?:VALOR|Valor|DATA|Data|EDITAL|Edital|PROCESSO|Processo|PRAZO|Prazo"
        r"|LOCAL|Local|CNPJ|CONTRATAD|Contratad|VIGÊNCIA|Vigência|VIGENCIA"
        r"|FUNDAMENTO|Fundamento)\s*:)",
        texto,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        obj = re.sub(r"\s+", " ", match.group(1).strip())
        return obj[:2000] if obj else None

    # Padrao 2 -- "... para aquisicao de ..."
    match = re.search(
        r"(?:pregão|pregao|licitação|licitacao|dispensa|inexigibilidade)"
        r"\s+(?:eletrônic[oa]?\s+|eletronico\s+)?"
        r"(?:n[.ºo°]\s*\S+\s+)?"
        r"para\s+(.+?)(?:\.|,\s*(?:conforme|de acordo|nos termos))",
        texto,
        re.IGNORECASE,
    )
    if match:
        obj = re.sub(r"\s+", " ", match.group(1).strip())
        return obj[:2000] if obj else None

    return None


def _extrair_valor(texto: str) -> Decimal | None:
    """Extrai o maior valor monetario encontrado no texto.

    Retorna ``Decimal`` ou ``None``.  O maior valor normalmente
    corresponde ao valor global estimado da contratacao.
    """
    matches = VALOR_PATTERN.findall(texto)
    if not matches:
        return None

    valores: list[Decimal] = []
    for val_str in matches:
        try:
            normalizado = val_str.replace(".", "").replace(",", ".")
            valores.append(Decimal(normalizado))
        except (InvalidOperation, ValueError):
            continue

    return max(valores) if valores else None


def _extrair_cnpj(texto: str) -> str | None:
    """Extrai o primeiro CNPJ encontrado no texto."""
    match = CNPJ_PATTERN.search(texto)
    return match.group(0) if match else None


def _extrair_processo(texto: str) -> str | None:
    """Extrai o numero do processo administrativo do texto."""
    match = PROCESSO_PATTERN.search(texto)
    return match.group(1).strip() if match else None


def _parse_data_numerica(texto_data: str) -> date | None:
    """Converte string DD/MM/YYYY em ``date``."""
    try:
        return datetime.strptime(texto_data.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_data_extenso(dia: str, mes_nome: str, ano: str) -> date | None:
    """Converte data por extenso (ex.: *15 de janeiro de 2024*) em ``date``."""
    mes_num = MESES.get(mes_nome.lower())
    if not mes_num:
        return None
    try:
        return date(int(ano), mes_num, int(dia))
    except (ValueError, TypeError):
        return None


def _extrair_datas(texto: str) -> dict[str, date | None]:
    """Extrai datas de abertura e encerramento de propostas.

    Retorna ``{"data_abertura": date | None, "data_encerramento": date | None}``.
    """
    result: dict[str, date | None] = {
        "data_abertura": None,
        "data_encerramento": None,
    }

    # --- data de abertura ---
    abertura_match = re.search(
        r"(?:abertura|recebimento\s+(?:das\s+)?propostas?"
        r"|sessão\s+pública|sessao\s+publica)"
        r"\s*(?:.*?)(\d{2}/\d{2}/\d{4})",
        texto,
        re.IGNORECASE,
    )
    if abertura_match:
        result["data_abertura"] = _parse_data_numerica(abertura_match.group(1))

    # Fallback: data por extenso perto de "abertura"
    if result["data_abertura"] is None:
        extenso_match = re.search(
            r"(?:abertura|sessão|sessao)\s+.*?"
            r"(\d{1,2})\s+de\s+"
            r"(janeiro|fevereiro|março|marco|abril|maio|junho"
            r"|julho|agosto|setembro|outubro|novembro|dezembro)"
            r"\s+de\s+(\d{4})",
            texto,
            re.IGNORECASE,
        )
        if extenso_match:
            result["data_abertura"] = _parse_data_extenso(
                extenso_match.group(1),
                extenso_match.group(2),
                extenso_match.group(3),
            )

    # --- data de encerramento ---
    encerramento_match = re.search(
        r"(?:encerramento|término|termino|prazo\s+final|data\s+limite)"
        r"\s*(?:.*?)(\d{2}/\d{2}/\d{4})",
        texto,
        re.IGNORECASE,
    )
    if encerramento_match:
        result["data_encerramento"] = _parse_data_numerica(
            encerramento_match.group(1)
        )

    # Fallback global: primeira data futura encontrada -> abertura
    if result["data_abertura"] is None:
        hoje = date.today()
        for d_str in DATA_NUMERICA_PATTERN.findall(texto):
            d = _parse_data_numerica(d_str)
            if d and d >= hoje:
                result["data_abertura"] = d
                break

    return result


def _extrair_modalidade(texto: str) -> tuple[str | None, str | None]:
    """Identifica a modalidade de licitacao no texto.

    Retorna ``(modalidade_nome, tipo_instrumento)``; ambos podem ser ``None``.
    """
    texto_lower = texto.lower()
    for termo in _MODALIDADE_KEYS_SORTED:
        if termo in texto_lower:
            nome, tipo = MODALIDADE_MAP[termo]
            return nome, tipo
    return None, None


def _classificar_tipo_ato(titulo: str, texto: str) -> str:
    """Classifica o tipo de ato a partir do titulo e texto da publicacao.

    Retorna um dos valores: ``aviso``, ``resultado``, ``adjudicacao``,
    ``homologacao``, ``extrato``, ``aditivo``, ``retificacao``,
    ``suspensao``, ``revogacao``, ``anulacao``, ``adiamento``,
    ``reabertura``.
    """
    # Prioriza o titulo, que e mais especifico.
    titulo_lower = titulo.lower()
    for keyword, tipo in TIPO_ATO_KEYWORDS:
        if keyword in titulo_lower:
            return tipo

    # Fallback: busca no inicio do texto (primeiros 500 caracteres).
    texto_inicio = texto[:500].lower()
    for keyword, tipo in TIPO_ATO_KEYWORDS:
        if keyword in texto_inicio:
            return tipo

    return "aviso"


def _classificar_situacao(tipo_ato: str) -> str:
    """Mapeia ``tipo_ato`` para a situacao correspondente da contratacao."""
    return SITUACAO_MAP.get(tipo_ato, "aberta")


def _detectar_mpe(texto: str) -> tuple[str, bool, bool, bool]:
    """Detecta beneficios para MPE (ME/EPP) no texto.

    Retorna ``(beneficio_mpe, exclusiva, cota_reservada, subcontratacao)``.
    """
    texto_lower = texto.lower()

    exclusiva = any(kw in texto_lower for kw in (
        "exclusiv",
        "microempresa",
        "pequena empresa",
        "me/epp",
        "me e epp",
        "lc 123",
        "lei complementar 123",
        "lei complementar nº 123",
        "lei complementar no 123",
        "decreto 8.538",
        "art. 48",
    ))

    cota = any(kw in texto_lower for kw in (
        "cota reservada",
        "cota de reserva",
        "25%",
        "vinte e cinco por cento",
    ))

    subcontratacao = any(kw in texto_lower for kw in (
        "subcontratação",
        "subcontratacao",
        "subcontrat",
    ))

    if exclusiva:
        beneficio = "exclusiva"
    elif cota:
        beneficio = "cota_reservada"
    elif subcontratacao:
        beneficio = "subcontratacao"
    else:
        beneficio = "sem_beneficio"

    return beneficio, exclusiva, cota, subcontratacao


def _detectar_srp(texto: str) -> bool:
    """Detecta se a contratacao utiliza SRP (Sistema de Registro de Precos)."""
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in (
        "registro de preços",
        "registro de precos",
        "ata de registro",
        "sistema de registro",
        "srp",
    ))


def _extrair_uf(publicacao: dict) -> str | None:
    """Extrai a UF a partir de hierarchy, campos do orgao ou corpo do texto."""
    # 1. Campo hierarchy (estrutura hierarquica do orgao)
    hierarchy = publicacao.get("hierarchy", "") or ""
    if hierarchy:
        uf_match = re.search(r"\b([A-Z]{2})\b", hierarchy)
        if uf_match and uf_match.group(1) in UFS_VALIDAS:
            return uf_match.group(1)

    # 2. Outros campos de metadados
    for field in ("artType", "orgao", "subTitulo"):
        val = publicacao.get(field, "") or ""
        if val:
            uf_match = re.search(r"\b([A-Z]{2})\b", val)
            if uf_match and uf_match.group(1) in UFS_VALIDAS:
                return uf_match.group(1)

    # 3. Padrao " - UF" ou "/UF" no titulo/conteudo
    texto = (
        f"{publicacao.get('title', '')} "
        f"{publicacao.get('abstract', '')} "
        f"{publicacao.get('content', '')}"
    )
    uf_match = re.search(r"[-/]\s*([A-Z]{2})\b", texto)
    if uf_match and uf_match.group(1) in UFS_VALIDAS:
        return uf_match.group(1)

    return None


def _extrair_orgao_nome(publicacao: dict) -> str | None:
    """Extrai o nome do orgao a partir dos metadados da publicacao."""
    hierarchy = publicacao.get("hierarchy", "") or ""
    if hierarchy:
        parts = [p.strip() for p in hierarchy.split("/") if p.strip()]
        if parts:
            return parts[0][:200]

    for field in ("artCategory", "subTitulo"):
        val = publicacao.get(field, "") or ""
        if val:
            return val[:200]

    return None


def _extrair_fornecedor(texto: str) -> tuple[str | None, str | None]:
    """Extrai CNPJ e nome do fornecedor vencedor em textos de resultado/extrato.

    Retorna ``(cnpj, nome)``; ambos podem ser ``None``.
    """
    texto_lower = texto.lower()

    # Localiza trecho proximo a palavras-chave de resultado
    winner_context: str | None = None
    for kw in ("vencedor", "adjudicad", "contratad", "fornecedor", "empresa"):
        idx = texto_lower.find(kw)
        if idx >= 0:
            winner_context = texto[max(0, idx - 50) : idx + 500]
            break

    if not winner_context:
        return None, None

    cnpj_match = CNPJ_PATTERN.search(winner_context)
    fornecedor_cnpj = cnpj_match.group(0) if cnpj_match else None

    fornecedor_nome: str | None = None
    if cnpj_match:
        before = winner_context[: cnpj_match.start()].strip()
        fragments = re.split(r"[;:\n]", before)
        if fragments:
            candidate = fragments[-1].strip().rstrip(",.-")
            if len(candidate) > 3:
                fornecedor_nome = candidate[:200]

    return fornecedor_cnpj, fornecedor_nome


def _derivar_ano_sequencial(
    processo: str | None,
    data_pub: date,
    cnpj: str | None = None,
    titulo: str | None = None,
) -> tuple[int, int]:
    """Deriva ``ano`` e ``sequencial`` para a unique constraint da Contratacao.

    Quando o numero de processo esta disponivel, extrai o ano e gera um
    sequencial deterministico via hash.  Caso contrario, utiliza CNPJ +
    titulo + data como semente para garantir estabilidade entre execucoes.
    """
    ano = data_pub.year

    if processo:
        year_match = re.search(r"/(\d{4})", processo)
        if year_match:
            ano = int(year_match.group(1))
        proc_hash = int(
            hashlib.sha256(processo.encode()).hexdigest()[:8], 16
        )
        sequencial = proc_hash % 9_000_000 + 1_000_000
    else:
        seed = f"{cnpj or ''}-{(titulo or '')[:100]}-{data_pub.isoformat()}"
        seq_hash = int(
            hashlib.sha256(seed.encode()).hexdigest()[:8], 16
        )
        sequencial = seq_hash % 9_000_000 + 1_000_000

    return ano, sequencial


# ---------------------------------------------------------------------------
# Verificadores e sessao
# ---------------------------------------------------------------------------

def _eh_relevante(publicacao: dict) -> bool:
    """Verifica se a publicacao contem termos relacionados a compras publicas."""
    texto = " ".join(
        str(v).lower()
        for v in (
            publicacao.get("title", ""),
            publicacao.get("abstract", ""),
            publicacao.get("content", ""),
        )
    )
    return any(termo in texto for termo in TERMOS_LICITACAO)


def _ensure_session():
    """Garante que o engine e async_session estejam inicializados."""
    if async_session is None:
        init_engine()


# ---------------------------------------------------------------------------
# Processamento de publicacao individual
# ---------------------------------------------------------------------------

async def _processar_publicacao(
    session,
    pub: dict,
    data_pub: date,
    stats: dict,
) -> None:
    """Processa uma publicacao do DOU em registros estruturados.

    Cria ou atualiza ``Contratacao``, cria ``Item`` (quando possivel),
    cria ``EventoContratacao`` e cria ``Alerta`` para perfil SEBRAE UF.
    """
    titulo = pub.get("title", "Publicação DOU Seção 3")
    conteudo = pub.get("abstract", "") or pub.get("content", "")
    texto_completo = f"{titulo}\n{conteudo}"

    # --- Extracao de campos estruturados ---
    tipo_ato = _classificar_tipo_ato(titulo, texto_completo)
    situacao = _classificar_situacao(tipo_ato)

    cnpj = _extrair_cnpj(texto_completo)
    processo = _extrair_processo(texto_completo)
    objeto = _extrair_objeto(texto_completo)
    valor = _extrair_valor(texto_completo)
    modalidade_nome, tipo_instrumento = _extrair_modalidade(texto_completo)
    datas = _extrair_datas(texto_completo)
    beneficio_mpe, exclusiva, cota, subcontratacao = _detectar_mpe(texto_completo)
    srp = _detectar_srp(texto_completo)
    uf = _extrair_uf(pub)
    orgao_nome = _extrair_orgao_nome(pub)

    ano, sequencial = _derivar_ano_sequencial(processo, data_pub, cnpj, titulo)

    # --- Busca contratacao existente ---
    contratacao_existente: Contratacao | None = None

    if cnpj and processo:
        stmt = select(Contratacao).where(
            Contratacao.orgao_cnpj == cnpj,
            Contratacao.numero_processo == processo,
        )
        result = await session.execute(stmt)
        contratacao_existente = result.scalar_one_or_none()

    if contratacao_existente is None and cnpj:
        stmt = select(Contratacao).where(
            Contratacao.orgao_cnpj == cnpj,
            Contratacao.ano == ano,
            Contratacao.sequencial == sequencial,
        )
        result = await session.execute(stmt)
        contratacao_existente = result.scalar_one_or_none()

    # --- Cria ou atualiza contratacao ---
    contratacao: Contratacao | None = None

    if contratacao_existente is not None:
        _atualizar_contratacao(
            contratacao_existente, tipo_ato, situacao,
            texto_completo, datas, valor,
        )

        evento = EventoContratacao(
            contratacao_id=contratacao_existente.id,
            tipo=tipo_ato,
            data_evento=datetime.combine(data_pub, datetime.min.time()),
            descricao=f"DOU Seção 3: {titulo[:500]}",
            campo_alterado="situacao" if tipo_ato in TIPOS_ATUALIZACAO else None,
            valor_anterior=(
                contratacao_existente.situacao
                if tipo_ato in TIPOS_ATUALIZACAO
                else None
            ),
            valor_novo=situacao if tipo_ato in TIPOS_ATUALIZACAO else None,
            fonte="dou_secao3",
            detalhes={
                "url": pub.get("urlTitle"),
                "titulo_dou": titulo[:500],
            },
        )
        session.add(evento)
        stats["eventos_criados"] += 1
        stats["contratacoes_atualizadas"] += 1

        contratacao = contratacao_existente

    elif cnpj:
        # Novo registro -- exige pelo menos o CNPJ do orgao.
        contratacao = Contratacao(
            orgao_cnpj=cnpj,
            orgao_nome=orgao_nome,
            ano=ano,
            sequencial=sequencial,
            numero_processo=processo,
            objeto=objeto,
            modalidade=0,
            modalidade_nome=modalidade_nome,
            tipo_instrumento=tipo_instrumento,
            valor_estimado=valor if tipo_ato == "aviso" else None,
            esfera="F",
            uf=uf,
            beneficio_mpe=beneficio_mpe,
            exclusiva_mpe=exclusiva,
            cota_reservada=cota,
            subcontratacao_mpe=subcontratacao,
            srp=srp,
            data_publicacao=data_pub,
            data_abertura_proposta=datas.get("data_abertura"),
            data_encerramento_proposta=datas.get("data_encerramento"),
            link_sistema_origem=pub.get("urlTitle"),
            situacao=situacao,
            data_ultima_atualizacao=data_pub,
            fonte="dou_secao3",
            raw_json=pub,
        )

        # Para resultado/extrato, preenche dados de resultado
        if tipo_ato in ("resultado", "adjudicacao", "homologacao", "extrato"):
            fornecedor_cnpj, fornecedor_nome = _extrair_fornecedor(texto_completo)
            if fornecedor_cnpj:
                contratacao.fornecedor_vencedor_cnpj = fornecedor_cnpj
                contratacao.fornecedor_vencedor_nome = fornecedor_nome
            if valor:
                contratacao.valor_adjudicado = valor

        session.add(contratacao)
        await session.flush()  # Obtem contratacao.id para registros filhos
        stats["contratacoes_criadas"] += 1

        # Evento inicial de publicacao
        evento = EventoContratacao(
            contratacao_id=contratacao.id,
            tipo="publicacao",
            data_evento=datetime.combine(data_pub, datetime.min.time()),
            descricao=f"Publicação DOU Seção 3: {titulo[:500]}",
            fonte="dou_secao3",
            detalhes={
                "url": pub.get("urlTitle"),
                "titulo_dou": titulo[:500],
            },
        )
        session.add(evento)
        stats["eventos_criados"] += 1

        # Cria Item a partir do objeto (quando disponivel)
        if objeto:
            item = Item(
                contratacao_id=contratacao.id,
                numero_item=1,
                descricao=objeto[:2000],
                valor_total_estimado=valor,
                beneficio_mpe=beneficio_mpe,
                cota_reservada=cota,
            )
            session.add(item)
            stats["itens_criados"] += 1

    else:
        # Sem CNPJ -- nao e possivel criar Contratacao.
        logger.debug(
            "Publicação sem CNPJ, apenas alerta criado: %s",
            titulo[:100],
        )

    # --- Alerta SEBRAE UF (sempre criado) ---
    corpo_parts = [f"Publicação: {titulo}"]
    if cnpj:
        corpo_parts.append(f"CNPJ do órgão: {cnpj}")
    if modalidade_nome:
        corpo_parts.append(f"Modalidade: {modalidade_nome}")
    if valor is not None:
        valor_fmt = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        corpo_parts.append(f"Valor estimado: R$ {valor_fmt}")
    if objeto:
        corpo_parts.append(f"Objeto: {objeto[:300]}")
    if pub.get("urlTitle"):
        corpo_parts.append(f"Link: {pub['urlTitle']}")

    alerta = Alerta(
        perfil="sebrae_uf",
        tipo="dou_secao3",
        titulo=f"DOU Seção 3 [{tipo_ato}]: {titulo[:200]}",
        corpo="\n".join(corpo_parts),
        uf=uf,
        contratacao_id=contratacao.id if contratacao else None,
    )
    session.add(alerta)
    stats["alertas_criados"] += 1


def _atualizar_contratacao(
    contratacao: Contratacao,
    tipo_ato: str,
    situacao: str,
    texto: str,
    datas: dict[str, date | None],
    valor: Decimal | None,
) -> None:
    """Atualiza uma Contratacao existente com base em nova publicacao do DOU."""
    contratacao.situacao = situacao
    contratacao.data_ultima_atualizacao = date.today()

    if tipo_ato in ("resultado", "adjudicacao", "homologacao", "extrato"):
        fornecedor_cnpj, fornecedor_nome = _extrair_fornecedor(texto)
        if fornecedor_cnpj:
            contratacao.fornecedor_vencedor_cnpj = fornecedor_cnpj
            contratacao.fornecedor_vencedor_nome = fornecedor_nome
        if valor:
            contratacao.valor_adjudicado = valor

    if tipo_ato == "retificacao":
        objeto = _extrair_objeto(texto)
        if objeto:
            contratacao.objeto = objeto
        if valor and not contratacao.valor_estimado:
            contratacao.valor_estimado = valor
        if datas.get("data_abertura"):
            contratacao.data_abertura_proposta = datas["data_abertura"]
        if datas.get("data_encerramento"):
            contratacao.data_encerramento_proposta = datas["data_encerramento"]

    if tipo_ato in ("adiamento", "reabertura") and datas.get("data_abertura"):
        contratacao.data_abertura_proposta = datas["data_abertura"]


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

async def coletar_dou_secao3(data_alvo: date | None = None) -> dict:
    """Coleta publicacoes da Secao 3 do DOU e cria registros estruturados.

    Args:
        data_alvo: Data para coletar.  Se ``None``, coleta o dia anterior.

    Returns:
        Dict com estatisticas da coleta.
    """
    logger.info("Iniciando coleta DOU Seção 3 (coletor primário)")
    _ensure_session()

    if data_alvo is None:
        data_alvo = date.today() - timedelta(days=1)
    data_str = data_alvo.strftime("%Y-%m-%d")

    client = DOUClient()

    try:
        publicacoes = await client.buscar_secao3(data_publicacao=data_str)
    except Exception:
        logger.exception("Erro ao buscar DOU Seção 3 para data %s", data_str)
        return {"erro": f"Falha ao buscar DOU para {data_str}"}

    if not publicacoes:
        logger.info(
            "Nenhuma publicação encontrada no DOU Seção 3 para %s", data_str
        )
        return {"data": data_str, "publicacoes_brutas": 0, "relevantes": 0}

    logger.info(
        "DOU Seção 3: %d publicações brutas encontradas para %s",
        len(publicacoes),
        data_str,
    )

    relevantes = [pub for pub in publicacoes if _eh_relevante(pub)]
    total_relevantes = len(relevantes)

    if not relevantes:
        logger.info(
            "Nenhuma publicação relevante encontrada no DOU Seção 3 para %s",
            data_str,
        )
        return {"data": data_str, "publicacoes_brutas": len(publicacoes), "relevantes": 0}

    logger.info(
        "DOU Seção 3: %d publicações relevantes de %d totais para %s",
        total_relevantes,
        len(publicacoes),
        data_str,
    )

    stats = {
        "contratacoes_criadas": 0,
        "contratacoes_atualizadas": 0,
        "itens_criados": 0,
        "eventos_criados": 0,
        "alertas_criados": 0,
        "duplicadas": 0,
        "erros": 0,
    }

    async with async_session() as session:
        batch_count = 0

        for pub in relevantes:
            try:
                async with session.begin_nested():
                    await _processar_publicacao(session, pub, data_alvo, stats)
                batch_count += 1
            except IntegrityError:
                logger.warning(
                    "Contratação duplicada, ignorando: %s",
                    pub.get("title", "sem título")[:100],
                )
                stats["duplicadas"] += 1
            except Exception:
                logger.exception(
                    "Erro ao processar publicação DOU: %s",
                    pub.get("title", "sem título")[:100],
                )
                stats["erros"] += 1

            if batch_count > 0 and batch_count % BATCH_SIZE == 0:
                await session.commit()
                logger.debug(
                    "Batch commit DOU: %d publicações processadas", batch_count
                )

        # Commit remanescente
        if batch_count % BATCH_SIZE != 0:
            try:
                await session.commit()
            except Exception:
                logger.exception("Erro no commit final do batch DOU")
                await session.rollback()

    logger.info(
        "Coleta DOU Seção 3 finalizada (data=%s): "
        "%d relevantes, %d contratações criadas, %d atualizadas, "
        "%d itens, %d eventos, %d alertas, %d duplicadas, %d erros",
        data_str,
        total_relevantes,
        stats["contratacoes_criadas"],
        stats["contratacoes_atualizadas"],
        stats["itens_criados"],
        stats["eventos_criados"],
        stats["alertas_criados"],
        stats["duplicadas"],
        stats["erros"],
    )

    return {
        "data": data_str,
        "publicacoes_brutas": len(publicacoes),
        "relevantes": total_relevantes,
        **stats,
    }
