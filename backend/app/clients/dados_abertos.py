import logging

from app.clients.base import BaseClient

logger = logging.getLogger(__name__)


class DadosAbertosComprasClient(BaseClient):
    """Cliente para a API de Dados Abertos de Compras Governamentais."""

    def __init__(self):
        from app.config import settings
        super().__init__(base_url=settings.DADOS_ABERTOS_URL)

    async def buscar_catmat(self, grupo: str | None = None) -> dict:
        """Busca itens no catalogo CATMAT (materiais)."""
        params = {}
        if grupo:
            params["grupo"] = grupo
        return await self._get("/modulo-pesquisa-preco/1_consultarMaterial", params)

    async def buscar_catser(self, grupo: str | None = None) -> dict:
        """Busca itens no catalogo CATSER (servicos)."""
        params = {}
        if grupo:
            params["grupo"] = grupo
        return await self._get("/modulo-pesquisa-preco/2_consultarServico", params)

    async def pesquisa_preco_material(
        self,
        catmat: str,
        uf: str | None = None,
    ) -> dict:
        """Pesquisa precos praticados para um material (CATMAT)."""
        params = {"codigoItemCatmat": catmat}
        if uf:
            params["uf"] = uf
        return await self._get("/modulo-pesquisa-preco/3_consultarPrecosPraticados", params)
