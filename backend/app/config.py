from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://pippa:pippa_dev@localhost:5432/pippa_compras"

    PNCP_BASE_URL: str = "https://pncp.gov.br/api/consulta"
    PNCP_INTEGRATION_URL: str = "https://pncp.gov.br/api/pncp"
    QUERIDO_DIARIO_URL: str = "https://api.queridodiario.org.br"
    DADOS_ABERTOS_URL: str = "https://dadosabertos.compras.gov.br"
    DOU_WEB_URL: str = "https://www.in.gov.br/consulta/-/buscar/dou"
    OBSERVATORIO_BASE_URL: str = "https://apiv2-observatorio.sebrae.com.br/tesseract"
    OBSERVATORIO_TOKEN: str = ""

    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    COLLECTION_CRON_HOUR: int = 3
    COLLECTION_CRON_MINUTE: int = 0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
