import logging
from typing import Any

from app.clients.base import BaseClient

logger = logging.getLogger(__name__)

# Guardrails: mandatory filters per cube to ensure data quality
_CUBE_GUARDRAILS: dict[str, dict[str, str]] = {
    "receita_federal": {
        "Registration Status": "2",
        "Sebrae Commercial Company Indicator": "1",
    },
    "rais": {
        "Active worker indicator": "1",
    },
}


class ObservatorioClient(BaseClient):
    """Cliente para a API OLAP do Observatorio Setorial Territorial SEBRAE."""

    def __init__(self):
        from app.config import settings
        super().__init__(
            base_url=settings.OBSERVATORIO_BASE_URL,
            headers={"Authorization": f"Bearer {settings.OBSERVATORIO_TOKEN}"},
        )

    async def query_cube(
        self,
        cube: str,
        drilldowns: list[str],
        measures: list[str],
        filters: dict[str, str] | None = None,
    ) -> dict:
        """Executa uma consulta OLAP em um cubo do Observatorio.

        Applies automatic guardrails per cube:
        - RF cube: Registration Status=2, Sebrae Commercial Company Indicator=1
        - RAIS cube: Active worker indicator=1
        """
        params: dict[str, Any] = {
            "cube": cube,
            "drilldowns": ",".join(drilldowns),
            "measures": ",".join(measures),
        }

        # Merge user filters with guardrail filters (guardrails take precedence)
        merged_filters: dict[str, str] = dict(filters) if filters else {}
        guardrails = _CUBE_GUARDRAILS.get(cube, {})
        for key, value in guardrails.items():
            if key not in merged_filters:
                merged_filters[key] = value
                logger.debug("Guardrail applied: %s=%s for cube %s", key, value, cube)

        for key, value in merged_filters.items():
            params[key] = value

        return await self._get("/data.jsonrecords", params)

    async def contar_mpes(
        self,
        cnae_divisao: str,
        uf: str | None = None,
        municipio_ibge: str | None = None,
    ) -> int:
        """Conta o numero de MPEs em uma divisao CNAE, opcionalmente filtrado por UF/municipio."""
        filters: dict[str, str] = {
            "CNAE 2 Division": cnae_divisao,
        }
        if uf:
            filters["State"] = uf
        if municipio_ibge:
            filters["Municipality"] = municipio_ibge

        result = await self.query_cube(
            cube="receita_federal",
            drilldowns=["CNAE 2 Division"],
            measures=["Establishments"],
            filters=filters,
        )

        data = result.get("data", [])
        if data:
            return sum(row.get("Establishments", 0) for row in data)
        return 0

    async def list_members(self, cube: str, dimension: str) -> dict:
        """Lista os valores possiveis de uma dimensao em um cubo."""
        params = {
            "cube": cube,
            "dimension": dimension,
        }
        return await self._get("/members", params)
