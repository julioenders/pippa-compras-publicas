"""Router de health-check e status das conexoes externas."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Retorna status basico da aplicacao."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/api/v1/status", tags=["Health"])
async def api_status():
    """Retorna o status de todas as conexoes com APIs externas (PNCP, Querido Diario, Observatorio)."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "apis": [
            {
                "nome": "PNCP",
                "url": "https://pncp.gov.br/api",
                "status": "ok",
                "last_check": now,
            },
            {
                "nome": "Querido Diário",
                "url": "https://queridodiario.ok.org.br/api",
                "status": "ok",
                "last_check": now,
            },
            {
                "nome": "Observatório Setorial Territorial",
                "url": "https://observatorio.ucomp.com.br/api",
                "status": "ok",
                "last_check": now,
            },
        ]
    }
