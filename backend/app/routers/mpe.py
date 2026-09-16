"""Router de oportunidades para MPEs (Micro e Pequenas Empresas)."""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import dashboard_mpe

router = APIRouter()


@router.get("/oportunidades")
async def listar_oportunidades(
    cnae: str = Query(..., description="Codigo CNAE da atividade da empresa"),
    uf: str = Query(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", description="UF (2 letras maiusculas)"),
    municipio_ibge: Optional[str] = Query(None, description="Codigo IBGE do municipio (opcional)"),
    limite: int = Query(10, ge=1, le=50, description="Quantidade maxima de resultados"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_mpe.buscar_oportunidades(db, cnae, uf, municipio_ibge, limite)


@router.get("/oportunidade/{id}")
async def detalhe_oportunidade(
    id: int = Path(..., description="ID unico da oportunidade"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_mpe.detalhar_oportunidade(db, id)


@router.get("/referencia-precos")
async def referencia_precos(
    catmat: str = Query(..., description="Codigo CATMAT do item"),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_mpe.buscar_referencia_precos(db, catmat)


@router.get("/guia/{modalidade}")
async def guia_modalidade(
    modalidade: str = Path(..., description="Slug da modalidade (ex: pregao-eletronico, dispensa, concorrencia)"),
):
    guias = {
        "pregao-eletronico": {
            "modalidade": "Pregao Eletronico",
            "descricao_simples": "E a forma mais comum de compra do governo. Tudo e feito pela internet.",
            "valor_limite": "Sem limite de valor",
            "tempo_medio": "15 a 30 dias",
            "dificuldade": "Moderada",
            "dicas": [
                "Cadastre-se no ComprasNet com antecedencia.",
                "Acompanhe os lances em tempo real na sessao publica.",
                "Tenha todos os documentos digitalizados e prontos para envio.",
                "O menor preco geralmente vence - calcule bem sua margem.",
            ],
        },
        "dispensa": {
            "modalidade": "Dispensa de Licitacao",
            "descricao_simples": "Para compras de menor valor. Processo mais rapido e simples.",
            "valor_limite": "Ate R$ 59.906,02 (bens) ou R$ 119.812,03 (servicos/obras) - valores 2024",
            "tempo_medio": "5 a 15 dias",
            "dificuldade": "Baixa",
            "dicas": [
                "Fique atento as publicacoes nos diarios oficiais e no PNCP.",
                "A proposta pode ser enviada de forma simples, sem sistema eletronico.",
                "Negocie diretamente com o orgao - muitas vezes e possivel.",
                "Ideal para quem esta comecando a vender para o governo.",
            ],
        },
        "concorrencia": {
            "modalidade": "Concorrencia",
            "descricao_simples": "Para obras e servicos de engenharia de maior valor. Processo mais longo.",
            "valor_limite": "Sem limite de valor",
            "tempo_medio": "45 a 90 dias",
            "dificuldade": "Alta",
            "dicas": [
                "Exige documentacao tecnica mais robusta.",
                "Considere formar consorcio com outras MPEs para obras maiores.",
                "Visite o local da obra antes de elaborar a proposta.",
                "Atencao aos atestados de capacidade tecnica exigidos.",
            ],
        },
    }
    guia = guias.get(modalidade)
    if guia:
        return guia
    return {
        "modalidade": modalidade,
        "descricao_simples": "Guia ainda nao disponivel para esta modalidade.",
        "valor_limite": None,
        "tempo_medio": None,
        "dificuldade": None,
        "dicas": ["Consulte o portal PNCP para mais informacoes sobre esta modalidade."],
    }
