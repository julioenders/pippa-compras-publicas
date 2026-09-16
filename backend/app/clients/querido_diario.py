import logging

from app.clients.base import BaseClient

logger = logging.getLogger(__name__)


class QueridoDiarioClient(BaseClient):
    """Cliente para a API do Querido Diario (diarios oficiais municipais)."""

    def __init__(self):
        from app.config import settings
        super().__init__(base_url=settings.QUERIDO_DIARIO_URL)

    async def buscar_gazetas(
        self,
        territory_ids: list[str],
        querystring: str,
        since: str,
        until: str,
        size: int = 10,
    ) -> dict:
        """Busca publicacoes em diarios oficiais por territorio e termo."""
        params = {
            "territory_ids": ",".join(territory_ids),
            "querystring": querystring,
            "published_since": since,
            "published_until": until,
            "size": size,
        }
        return await self._get("/gazettes", params)

    async def buscar_por_tema(
        self,
        theme: str,
        territory_ids: list[str] | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> dict:
        """Busca publicacoes por tema predefinido."""
        params = {}
        if territory_ids:
            params["territory_ids"] = ",".join(territory_ids)
        if since:
            params["published_since"] = since
        if until:
            params["published_until"] = until
        return await self._get(f"/gazettes/by_theme/{theme}", params)

    async def listar_temas(self) -> list:
        """Lista todos os temas disponiveis para busca tematica."""
        return await self._get("/gazettes/by_theme/themes/")

    async def buscar_cidade(self, territory_id: str) -> dict:
        """Busca informacoes sobre uma cidade pelo codigo IBGE."""
        return await self._get(f"/cities/{territory_id}")
