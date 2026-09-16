from dataclasses import dataclass
from datetime import date, timedelta

from app.schemas.common import Esfera, FaixaValor, Momento, Urgencia

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

LIMITE_DISPENSA = 59_906.02
LIMITE_COTA_MPE = 80_000.00
LIMITE_MEDIO = 480_000.00


@dataclass
class Classificacao:
    esfera: Esfera
    modalidade: str
    momento: Momento
    exclusiva_mpe: bool
    catmat_catser: str | None
    valor_faixa: FaixaValor
    uf: str
    municipio_ibge: str | None
    urgencia: Urgencia


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


def classificar_momento(status: str | None, data_abertura: date | None) -> Momento:
    if status and "contrat" in status.lower():
        return Momento.CONTRATO
    if status and "resultado" in status.lower():
        return Momento.RESULTADO
    if data_abertura and data_abertura > date.today():
        return Momento.PCA
    return Momento.EDITAL


def classificar_exclusividade_mpe(
    modalidade_cod: int, valor_estimado: float | None
) -> bool:
    if modalidade_cod == 8 and valor_estimado and valor_estimado <= LIMITE_DISPENSA:
        return True
    if valor_estimado and valor_estimado <= LIMITE_COTA_MPE:
        return True
    return False


def classificar(contratacao: dict) -> Classificacao:
    """Classifica uma contratação do PNCP nas 8 dimensões."""
    modalidade_cod = contratacao.get("modalidadeId", 0)
    valor = contratacao.get("valorTotalEstimado")
    data_enc = contratacao.get("dataEncerramentoProposta")
    if isinstance(data_enc, str):
        data_enc = date.fromisoformat(data_enc)

    data_abertura = contratacao.get("dataAberturaProposta")
    if isinstance(data_abertura, str):
        data_abertura = date.fromisoformat(data_abertura)

    itens = contratacao.get("itens", [])
    catmat = itens[0].get("materialOuServico") if itens else None

    return Classificacao(
        esfera=classificar_esfera(contratacao.get("esferaId", "F")),
        modalidade=MODALIDADES.get(modalidade_cod, "outro"),
        momento=classificar_momento(contratacao.get("situacaoCompraDescricao"), data_abertura),
        exclusiva_mpe=classificar_exclusividade_mpe(modalidade_cod, valor),
        catmat_catser=catmat,
        valor_faixa=classificar_faixa_valor(valor),
        uf=contratacao.get("uf", ""),
        municipio_ibge=contratacao.get("codigoMunicipioIbge"),
        urgencia=classificar_urgencia(data_enc),
    )
