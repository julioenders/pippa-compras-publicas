import json
import logging
import re

import httpx

logger = logging.getLogger(__name__)


class DOUClient:
    """Cliente para busca na Secao 3 do Diario Oficial da Uniao (DOU).

    Uses web scraping since DOU does not provide a structured API.
    The search endpoint returns HTML with embedded JSON data.
    """

    def __init__(self):
        from app.config import settings
        self.base_url = settings.DOU_WEB_URL
        self.timeout = 30.0

    async def buscar_secao3(
        self,
        data_publicacao: str,  # format: YYYY-MM-DD
        termo: str | None = None,
    ) -> list[dict]:
        """Busca publicacoes na Secao 3 do DOU (licitacoes e contratos).

        Args:
            data_publicacao: Data de publicacao no formato YYYY-MM-DD.
            termo: Termo opcional de busca textual.

        Returns:
            Lista de publicacoes encontradas.
        """
        # Convert date from YYYY-MM-DD to DD-MM-YYYY for the DOU search
        parts = data_publicacao.split("-")
        date_formatted = f"{parts[2]}-{parts[1]}-{parts[0]}"

        params = {
            "s": "do3",  # Section 3
            "exactDate": "personalizado",
            "publishFrom": date_formatted,
            "publishTo": date_formatted,
        }
        if termo:
            params["q"] = termo

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            logger.debug("GET %s params=%s", self.base_url, params)
            response = await client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()

        return self._parse_results(response.text)

    @staticmethod
    def _parse_results(html: str) -> list[dict]:
        """Extracts search results from the DOU HTML response.

        The DOU search page embeds results as JSON within a script tag
        or within specific HTML data attributes.
        """
        results = []

        # Try to find JSON data embedded in the search results page.
        # The DOU portal embeds results in a JSON structure within a script tag.
        json_pattern = re.compile(
            r'var\s+params\s*=\s*(\{.*?\});', re.DOTALL
        )
        match = json_pattern.search(html)
        if match:
            try:
                data = json.loads(match.group(1))
                if "jsonArray" in data:
                    return json.loads(data["jsonArray"])
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to parse embedded JSON from DOU response")

        # Fallback: try the Liferay-style JSON array pattern
        json_array_pattern = re.compile(
            r'"jsonArray"\s*:\s*"(\[.*?\])"', re.DOTALL
        )
        match = json_array_pattern.search(html)
        if match:
            try:
                json_str = match.group(1).replace('\\"', '"').replace("\\/", "/")
                results = json.loads(json_str)
                return results
            except json.JSONDecodeError:
                logger.warning("Failed to parse jsonArray from DOU response")

        # Fallback: extract from search-result divs
        result_pattern = re.compile(
            r'<div[^>]*class="[^"]*resultado-busca-dou[^"]*"[^>]*>(.*?)</div>',
            re.DOTALL,
        )
        for block in result_pattern.finditer(html):
            entry = {}
            title_match = re.search(
                r'<a[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', block.group(1), re.DOTALL
            )
            if title_match:
                entry["urlTitle"] = title_match.group(1)
                entry["title"] = re.sub(r"<[^>]+>", "", title_match.group(2)).strip()
            date_match = re.search(
                r'<span[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</span>',
                block.group(1),
                re.DOTALL,
            )
            if date_match:
                entry["pubDate"] = date_match.group(1).strip()
            if entry:
                results.append(entry)

        return results
