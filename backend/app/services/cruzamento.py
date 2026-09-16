import logging

from app.clients.observatorio import ObservatorioClient
from app.schemas.common import SinalOportunidade

logger = logging.getLogger(__name__)


def calcular_sinal(qtd_mpes: int, exclusiva_mpe: bool) -> SinalOportunidade:
    """Calcula o sinal de oportunidade com base na quantidade de MPEs na região."""
    if qtd_mpes == 0:
        return SinalOportunidade.DESERTO

    if exclusiva_mpe:
        if qtd_mpes >= 50:
            return SinalOportunidade.COMPETITIVO
        return SinalOportunidade.OPORTUNIDADE

    if qtd_mpes > 500:
        return SinalOportunidade.SATURADO
    if qtd_mpes > 200:
        return SinalOportunidade.CAUTELA
    if qtd_mpes > 50:
        return SinalOportunidade.COMPETITIVO
    return SinalOportunidade.OPORTUNIDADE


def calcular_score(qtd_mpes: int, exclusiva_mpe: bool, valor_estimado: float | None) -> float:
    """Score de 0.0 a 10.0 — quanto maior, melhor a oportunidade para a MPE."""
    score = 5.0

    if exclusiva_mpe:
        score += 2.0

    if qtd_mpes == 0:
        score = 1.0
    elif qtd_mpes <= 20:
        score += 2.0
    elif qtd_mpes <= 100:
        score += 1.0
    elif qtd_mpes > 500:
        score -= 2.0

    if valor_estimado:
        if valor_estimado <= 80_000:
            score += 1.0
        elif valor_estimado > 480_000:
            score -= 1.0

    return max(0.0, min(10.0, score))


async def cruzar_demanda_oferta(
    cnae_divisao: str,
    uf: str,
    municipio_ibge: str | None,
    exclusiva_mpe: bool,
    valor_estimado: float | None,
    observatorio: ObservatorioClient,
) -> dict:
    """Cruza a demanda de uma contratação com a oferta de MPEs na região."""
    try:
        qtd_mpes = await observatorio.contar_mpes(
            cnae_divisao=cnae_divisao,
            uf=uf,
            municipio_ibge=municipio_ibge,
        )
    except Exception:
        logger.warning("Falha ao consultar Observatório para CNAE %s, UF %s", cnae_divisao, uf)
        qtd_mpes = -1

    if qtd_mpes < 0:
        return {
            "cnae_divisao": cnae_divisao,
            "uf": uf,
            "municipio_ibge": municipio_ibge,
            "qtd_mpes_regiao": None,
            "sinal": SinalOportunidade.COMPETITIVO.value,
            "score": 5.0,
            "observatorio_indisponivel": True,
        }

    sinal = calcular_sinal(qtd_mpes, exclusiva_mpe)
    score = calcular_score(qtd_mpes, exclusiva_mpe, valor_estimado)

    return {
        "cnae_divisao": cnae_divisao,
        "uf": uf,
        "municipio_ibge": municipio_ibge,
        "qtd_mpes_regiao": qtd_mpes,
        "sinal": sinal.value,
        "score": round(score, 1),
        "observatorio_indisponivel": False,
    }
