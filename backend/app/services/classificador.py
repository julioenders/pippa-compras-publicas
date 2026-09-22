from dataclasses import dataclass
from datetime import date

from app.schemas.common import (
    BeneficioMPE,
    CriterioJulgamento,
    Esfera,
    FaixaValor,
    ModoDisputa,
    Momento,
    SituacaoContratacao,
    TipoInstrumento,
    Urgencia,
)

MODALIDADES = {
    1: "leilao",
    2: "dialogo_competitivo",
    3: "concurso",
    4: "concorrencia",
    5: "pregao",
    6: "pregao",
    7: "credenciamento",
    8: "dispensa",
    9: "inexigibilidade",
    10: "manifestacao_interesse",
    11: "pre_qualificacao",
    12: "concorrencia_internacional",
    13: "ato_especial",
}

MODALIDADE_TO_INSTRUMENTO = {
    5: TipoInstrumento.PREGAO_ELETRONICO,
    6: TipoInstrumento.PREGAO_ELETRONICO,
    4: TipoInstrumento.CONCORRENCIA,
    3: TipoInstrumento.CONCURSO,
    2: TipoInstrumento.DIALOGO_COMPETITIVO,
    8: TipoInstrumento.DISPENSA_ELETRONICA,
    9: TipoInstrumento.INEXIGIBILIDADE,
    7: TipoInstrumento.CREDENCIAMENTO,
    11: TipoInstrumento.PRE_QUALIFICACAO,
    1: TipoInstrumento.AVISO_LICITACAO,
}

LIMITE_DISPENSA = 59_906.02
LIMITE_COTA_MPE = 80_000.00
LIMITE_MEDIO = 480_000.00

CRITERIOS_JULGAMENTO = {
    1: CriterioJulgamento.MENOR_PRECO,
    2: CriterioJulgamento.MAIOR_DESCONTO,
    3: CriterioJulgamento.MELHOR_TECNICA,
    4: CriterioJulgamento.TECNICA_PRECO,
    5: CriterioJulgamento.MAIOR_LANCE,
    6: CriterioJulgamento.MAIOR_RETORNO,
    7: CriterioJulgamento.NAO_SE_APLICA,
}

MODOS_DISPUTA = {
    1: ModoDisputa.ABERTO,
    2: ModoDisputa.FECHADO,
    3: ModoDisputa.ABERTO_FECHADO,
    4: ModoDisputa.FECHADO_ABERTO,
    5: ModoDisputa.NAO_SE_APLICA,
}


@dataclass
class Classificacao:
    esfera: Esfera
    modalidade: str
    tipo_instrumento: TipoInstrumento
    momento: Momento
    situacao: SituacaoContratacao
    beneficio_mpe: BeneficioMPE
    exclusiva_mpe: bool
    cota_reservada: bool
    subcontratacao_mpe: bool
    srp: bool
    catmat_catser: str | None
    material_ou_servico: str | None
    valor_faixa: FaixaValor
    uf: str
    municipio_ibge: str | None
    urgencia: Urgencia
    criterio_julgamento: CriterioJulgamento
    modo_disputa: ModoDisputa
    orcamento_sigiloso: bool


def classificar_esfera(esfera_id: str) -> Esfera:
    return {"F": Esfera.FEDERAL, "E": Esfera.ESTADUAL, "M": Esfera.MUNICIPAL}.get(
        esfera_id, Esfera.FEDERAL
    )


def classificar_faixa_valor(valor: float | None) -> FaixaValor:
    if valor is None:
        return FaixaValor.MEDIO
    if valor <= LIMITE_DISPENSA:
        return FaixaValor.MICRO
    if valor <= LIMITE_COTA_MPE:
        return FaixaValor.PEQUENO
    if valor <= LIMITE_MEDIO:
        return FaixaValor.MEDIO
    return FaixaValor.GRANDE


def classificar_urgencia(data_encerramento: date | None) -> Urgencia:
    if data_encerramento is None:
        return Urgencia.NORMAL
    dias_restantes = (data_encerramento - date.today()).days
    if dias_restantes <= 3:
        return Urgencia.URGENTE
    if dias_restantes > 30:
        return Urgencia.PLANEJADO
    return Urgencia.NORMAL


def classificar_situacao(status: str | None) -> SituacaoContratacao:
    if not status:
        return SituacaoContratacao.ABERTA
    s = status.lower()
    mapa = {
        "aberta": SituacaoContratacao.ABERTA,
        "recebendo propostas": SituacaoContratacao.ABERTA,
        "divulgada": SituacaoContratacao.ABERTA,
        "publicada": SituacaoContratacao.ABERTA,
        "suspensa": SituacaoContratacao.SUSPENSA,
        "revogada": SituacaoContratacao.REVOGADA,
        "anulada": SituacaoContratacao.ANULADA,
        "encerrada": SituacaoContratacao.ENCERRADA,
        "homologada": SituacaoContratacao.ENCERRADA,
        "adjudicada": SituacaoContratacao.ENCERRADA,
        "contratada": SituacaoContratacao.ENCERRADA,
        "deserta": SituacaoContratacao.DESERTA,
        "fracassada": SituacaoContratacao.FRACASSADA,
        "em julgamento": SituacaoContratacao.EM_JULGAMENTO,
        "julgamento": SituacaoContratacao.EM_JULGAMENTO,
    }
    for chave, sit in mapa.items():
        if chave in s:
            return sit
    return SituacaoContratacao.ABERTA


def classificar_momento(
    status: str | None,
    data_abertura: date | None,
    modalidade_cod: int,
) -> Momento:
    if modalidade_cod == 11:
        return Momento.PRE_QUALIFICACAO
    if status:
        sl = status.lower()
        if "contrat" in sl:
            return Momento.CONTRATO
        if "resultado" in sl or "homolog" in sl or "adjudic" in sl:
            return Momento.RESULTADO
    if data_abertura and data_abertura > date.today():
        return Momento.PCA
    return Momento.EDITAL


def classificar_beneficio_mpe(
    modalidade_cod: int,
    valor_estimado: float | None,
    raw_beneficio: str | None,
    is_exclusiva: bool | None,
) -> tuple[BeneficioMPE, bool, bool, bool]:
    exclusiva = False
    cota = False
    subcontratacao = False

    if raw_beneficio:
        rb = raw_beneficio.lower()
        if "exclusi" in rb:
            exclusiva = True
        if "cota" in rb or "reserva" in rb:
            cota = True
        if "subcontrat" in rb:
            subcontratacao = True

    if is_exclusiva:
        exclusiva = True

    if not exclusiva and not cota and not subcontratacao:
        if modalidade_cod == 8 and valor_estimado and valor_estimado <= LIMITE_DISPENSA:
            exclusiva = True
        elif valor_estimado and valor_estimado <= LIMITE_COTA_MPE:
            cota = True

    if exclusiva:
        beneficio = BeneficioMPE.EXCLUSIVA
    elif cota:
        beneficio = BeneficioMPE.COTA_RESERVADA
    elif subcontratacao:
        beneficio = BeneficioMPE.SUBCONTRATACAO
    else:
        beneficio = BeneficioMPE.SEM_BENEFICIO

    return beneficio, exclusiva, cota, subcontratacao


def classificar(contratacao: dict) -> Classificacao:
    """Classifica uma contratacao do PNCP em todas as dimensoes da matriz."""
    modalidade_cod = contratacao.get("modalidadeId", 0)
    valor = contratacao.get("valorTotalEstimado")
    status = contratacao.get("situacaoCompraDescricao")

    data_enc = contratacao.get("dataEncerramentoProposta")
    if isinstance(data_enc, str):
        data_enc = date.fromisoformat(data_enc)

    data_abertura = contratacao.get("dataAberturaProposta")
    if isinstance(data_abertura, str):
        data_abertura = date.fromisoformat(data_abertura)

    itens = contratacao.get("itens", [])
    catmat = itens[0].get("materialOuServico") if itens else None
    mat_ou_serv = itens[0].get("tipoBeneficio") if itens else None

    raw_beneficio = contratacao.get("tipoBeneficioNome")
    is_exclusiva = contratacao.get("exclusivoMEEPP", False)
    beneficio, exclusiva, cota, sub = classificar_beneficio_mpe(
        modalidade_cod, valor, raw_beneficio, is_exclusiva
    )

    criterio_cod = contratacao.get("criterioJulgamentoId", 7)
    modo_cod = contratacao.get("modoDisputaId", 5)

    return Classificacao(
        esfera=classificar_esfera(contratacao.get("esferaId", "F")),
        modalidade=MODALIDADES.get(modalidade_cod, "outro"),
        tipo_instrumento=MODALIDADE_TO_INSTRUMENTO.get(
            modalidade_cod, TipoInstrumento.AVISO_LICITACAO
        ),
        momento=classificar_momento(status, data_abertura, modalidade_cod),
        situacao=classificar_situacao(status),
        beneficio_mpe=beneficio,
        exclusiva_mpe=exclusiva,
        cota_reservada=cota,
        subcontratacao_mpe=sub,
        srp=bool(contratacao.get("srp", False)),
        catmat_catser=catmat,
        material_ou_servico=mat_ou_serv,
        valor_faixa=classificar_faixa_valor(valor),
        uf=contratacao.get("uf", ""),
        municipio_ibge=contratacao.get("codigoMunicipioIbge"),
        urgencia=classificar_urgencia(data_enc),
        criterio_julgamento=CRITERIOS_JULGAMENTO.get(
            criterio_cod, CriterioJulgamento.NAO_SE_APLICA
        ),
        modo_disputa=MODOS_DISPUTA.get(modo_cod, ModoDisputa.NAO_SE_APLICA),
        orcamento_sigiloso=bool(contratacao.get("orcamentoSigiloso", False)),
    )
