import logging

from app.schemas.common import BeneficioMPE, SinalOportunidade

logger = logging.getLogger(__name__)


def calcular_sinal(
    qtd_mpes: int,
    beneficio_mpe: str,
) -> SinalOportunidade:
    """Calcula o sinal de oportunidade considerando tipo de beneficio MPE."""
    if qtd_mpes == 0:
        return SinalOportunidade.DESERTO

    is_exclusiva = beneficio_mpe == BeneficioMPE.EXCLUSIVA.value
    is_cota = beneficio_mpe == BeneficioMPE.COTA_RESERVADA.value

    if is_exclusiva or is_cota:
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


def calcular_score(
    qtd_mpes: int,
    beneficio_mpe: str,
    valor_estimado: float | None,
    srp: bool = False,
    criterio_julgamento: str | None = None,
) -> float:
    """Score de 0.0 a 10.0 — quanto maior, melhor a oportunidade para a MPE.

    Fatores do score alinhados a matriz:
    - Beneficio MPE (exclusiva +2, cota +1.5, subcontratacao +0.5)
    - Densidade de concorrentes (poucos = melhor)
    - Faixa de valor (menor = mais acessivel)
    - SRP (bonus: demanda recorrente)
    - Criterio de julgamento (menor preco = mais objetivo)
    """
    score = 5.0

    if beneficio_mpe == BeneficioMPE.EXCLUSIVA.value:
        score += 2.0
    elif beneficio_mpe == BeneficioMPE.COTA_RESERVADA.value:
        score += 1.5
    elif beneficio_mpe == BeneficioMPE.SUBCONTRATACAO.value:
        score += 0.5

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

    if srp:
        score += 0.5

    if criterio_julgamento in ("menor_preco", "maior_desconto"):
        score += 0.5

    return max(0.0, min(10.0, score))


async def cruzar_demanda_oferta(
    cnae_divisao: str,
    uf: str,
    municipio_ibge: str | None,
    beneficio_mpe: str,
    valor_estimado: float | None,
    qtd_mpes: int | None = None,
    srp: bool = False,
    criterio_julgamento: str | None = None,
) -> dict:
    """Cruza a demanda de uma contratacao com a oferta de MPEs na regiao.

    Se qtd_mpes nao for fornecido, retorna um sinal COMPETITIVO padrao com score 5.0.
    """
    if qtd_mpes is None:
        return {
            "cnae_divisao": cnae_divisao,
            "uf": uf,
            "municipio_ibge": municipio_ibge,
            "qtd_mpes_regiao": None,
            "sinal": SinalOportunidade.COMPETITIVO.value,
            "score": 5.0,
        }

    sinal = calcular_sinal(qtd_mpes, beneficio_mpe)
    score = calcular_score(
        qtd_mpes, beneficio_mpe, valor_estimado,
        srp=srp, criterio_julgamento=criterio_julgamento,
    )

    return {
        "cnae_divisao": cnae_divisao,
        "uf": uf,
        "municipio_ibge": municipio_ibge,
        "qtd_mpes_regiao": qtd_mpes,
        "sinal": sinal.value,
        "score": round(score, 1),
    }
