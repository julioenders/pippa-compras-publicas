"""Sincronização semanal do cache de MPEs a partir do Observatório SEBRAE.

Atualiza a tabela cache_mpes com contagens de MPEs por UF e Divisão CNAE,
consultando o cubo receita_federal da API OLAP do Observatório.
Os guardrails (Registration Status=2, Sebrae Commercial Company Indicator=1)
são aplicados automaticamente pelo ObservatorioClient.
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.clients.observatorio import ObservatorioClient
from app.database import async_session, init_engine
from app.models.cache_mpe import CacheMPE

logger = logging.getLogger(__name__)

# Todas as UFs brasileiras
UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

BATCH_SIZE = 50


def _ensure_session():
    """Garante que o engine e async_session estejam inicializados."""
    if async_session is None:
        init_engine()


async def _sincronizar_uf(client: ObservatorioClient, uf: str) -> int:
    """Consulta e upserta contagens de MPEs para uma UF.

    Returns:
        Número de registros atualizados/inseridos.
    """
    _ensure_session()

    try:
        resultado = await client.query_cube(
            cube="receita_federal",
            drilldowns=["CNAE 2 Division"],
            measures=["Establishments"],
            filters={"State": uf},
        )
    except Exception:
        logger.exception("Erro ao consultar Observatório para UF=%s", uf)
        return 0

    data = resultado.get("data", [])
    if not data:
        logger.warning("Nenhum dado retornado do Observatório para UF=%s", uf)
        return 0

    periodo_ref = date.today().strftime("%Y-%m")
    registros_atualizados = 0

    async with async_session() as session:
        batch_count = 0
        for row in data:
            cnae_divisao = str(row.get("CNAE 2 Division", ""))
            qtd_mpes = int(row.get("Establishments", 0))

            if not cnae_divisao:
                continue

            # Use PostgreSQL upsert (INSERT ... ON CONFLICT ... DO UPDATE)
            stmt = pg_insert(CacheMPE).values(
                uf=uf,
                municipio_ibge=None,
                cnae_divisao=cnae_divisao,
                cnae_subclasse=None,
                qtd_mpes=qtd_mpes,
                periodo_referencia=periodo_ref,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_cache_mpe_uf_mun_cnae",
                set_={
                    "qtd_mpes": stmt.excluded.qtd_mpes,
                    "periodo_referencia": stmt.excluded.periodo_referencia,
                    "atualizado_em": CacheMPE.atualizado_em.default.arg,
                },
            )
            await session.execute(stmt)
            batch_count += 1
            registros_atualizados += 1

            if batch_count % BATCH_SIZE == 0:
                await session.commit()
                logger.debug("Batch commit Observatório UF=%s: %d registros", uf, batch_count)

        # Commit remaining
        if batch_count % BATCH_SIZE != 0:
            await session.commit()

    return registros_atualizados


async def atualizar_cache_mpes():
    """Atualiza o cache de MPEs consultando o Observatório SEBRAE para todas as UFs.

    Para cada UF, consulta o cubo receita_federal por Divisão CNAE e realiza
    upsert na tabela cache_mpes. Os guardrails de qualidade (Registration Status=2,
    Sebrae Commercial Company Indicator=1) são aplicados automaticamente pelo client.

    Executa semanalmente porque os dados do Observatório são atualizados mensalmente.
    O cache evita consultas à API para cada cálculo de cruzamento.

    Esta função é chamada pelo scheduler sem parâmetros.
    """
    logger.info("Iniciando atualização semanal do cache de MPEs")
    _ensure_session()

    client = ObservatorioClient()
    total_registros = 0
    ufs_com_erro = []

    for uf in UFS:
        try:
            qtd = await _sincronizar_uf(client, uf)
            total_registros += qtd
            logger.info("UF %s: %d registros atualizados no cache", uf, qtd)
        except Exception:
            logger.exception("Erro fatal ao sincronizar UF=%s", uf)
            ufs_com_erro.append(uf)
            continue

    if ufs_com_erro:
        logger.warning(
            "Atualização do cache concluída com erros em %d UFs: %s",
            len(ufs_com_erro),
            ", ".join(ufs_com_erro),
        )
    else:
        logger.info("Atualização do cache concluída sem erros")

    logger.info(
        "Cache MPEs atualizado: %d registros total (%d UFs processadas, %d com erro)",
        total_registros,
        len(UFS) - len(ufs_com_erro),
        len(ufs_com_erro),
    )
