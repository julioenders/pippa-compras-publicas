import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseClient:
    """Async HTTP client with retry, timeout, and structured logging."""

    def __init__(self, base_url: str, timeout: float = 30.0, headers: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}{path}"
            logger.debug("GET %s params=%s", url, params)
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
