import logging

import httpx

from app.clients.base import BaseClient

logger = logging.getLogger(__name__)


class PNCPClient(BaseClient):
    """Cliente para a API de Consulta do PNCP (Portal Nacional de Contratacoes Publicas)."""

    def __init__(self):
        from app.config import settings
        super().__init__(base_url=settings.PNCP_BASE_URL)

    async def buscar_contratacoes(
        self,
        data_inicio: str,  # format: yyyyMMdd
        data_fim: str,
        modalidade: int,
        uf: str | None = None,
        municipio_ibge: str | None = None,
        cnpj: str | None = None,
        pagina: int = 1,
        tamanho: int = 50,
    ) -> dict:
        """Busca contratacoes por data de publicacao."""
        params = {
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
            "codigoModalidadeContratacao": modalidade,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }
        if uf:
            params["uf"] = uf
        if municipio_ibge:
            params["codigoMunicipioIbge"] = municipio_ibge
        if cnpj:
            params["cnpj"] = cnpj
        return await self._get("/v1/contratacoes/publicacao", params)

    async def buscar_contratacoes_abertas(
        self,
        data_fim: str,
        modalidade: int | None = None,
        uf: str | None = None,
        municipio_ibge: str | None = None,
        pagina: int = 1,
        tamanho: int = 50,
    ) -> dict:
        """Busca contratacoes com periodo de propostas aberto."""
        params = {
            "dataFinal": data_fim,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }
        if modalidade:
            params["codigoModalidadeContratacao"] = modalidade
        if uf:
            params["uf"] = uf
        if municipio_ibge:
            params["codigoMunicipioIbge"] = municipio_ibge
        return await self._get("/v1/contratacoes/proposta", params)

    async def detalhar_contratacao(self, cnpj_orgao: str, ano: int, sequencial: int) -> dict:
        """Busca detalhes de uma contratacao especifica."""
        return await self._get(f"/v1/orgaos/{cnpj_orgao}/compras/{ano}/{sequencial}")

    async def buscar_contratos(
        self,
        data_inicio: str,
        data_fim: str,
        cnpj_orgao: str | None = None,
        pagina: int = 1,
        tamanho: int = 50,
    ) -> dict:
        """Busca contratos por data de publicacao."""
        params = {
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }
        if cnpj_orgao:
            params["cnpjOrgao"] = cnpj_orgao
        return await self._get("/v1/contratos", params)

    async def buscar_atas(
        self,
        data_inicio: str,
        data_fim: str,
        cnpj: str | None = None,
        pagina: int = 1,
        tamanho: int = 50,
    ) -> dict:
        """Busca atas de registro de preco por vigencia."""
        params = {
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }
        if cnpj:
            params["cnpj"] = cnpj
        return await self._get("/v1/atas", params)

    async def buscar_pca(
        self,
        ano: int,
        pagina: int = 1,
        tamanho: int = 50,
    ) -> dict:
        """Busca itens do Plano de Contratacao Anual."""
        params = {
            "anoPca": ano,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }
        return await self._get("/v1/pca/", params)

    async def buscar_modalidades(self) -> list:
        """Lista todas as modalidades de contratacao (da API de integracao)."""
        from app.config import settings
        # This endpoint is on the integration API, not consulta
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{settings.PNCP_INTEGRATION_URL}/v1/modalidades")
            response.raise_for_status()
            return response.json()
