"""Cliente para busca na Secao 3 do Diario Oficial da Uniao (DOU).

Estrategia dupla de coleta:
  1. Playwright (headless browser) -- renderiza o JavaScript do portal e
     extrai o JSON embutido no elemento do portlet Liferay. E a estrategia
     primaria pois o portal carrega os resultados via JS.
  2. HTTP scraping (fallback) -- tenta extrair dados do HTML cru retornado
     por httpx. Funciona apenas se o portal eventualmente incluir o JSON
     no HTML inicial (raro, mas mantido como fallback).

O Playwright e importado de forma condicional; se nao estiver instalado
o cliente opera apenas com a estrategia HTTP.
"""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Playwright availability check
# ---------------------------------------------------------------------------

_PLAYWRIGHT_AVAILABLE = False

try:
    from playwright.async_api import async_playwright  # noqa: F401

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


def verificar_playwright() -> bool:
    """Check if Playwright and a Chromium browser are available.

    Returns True if the ``playwright`` package is importable **and** the
    Chromium browser binary has been installed (via ``playwright install
    chromium``).
    """
    if not _PLAYWRIGHT_AVAILABLE:
        logger.warning(
            "Playwright nao esta instalado. "
            "Instale com: pip install playwright && playwright install chromium"
        )
        return False

    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # If dry-run exits 0, the browser is already installed.
        if result.returncode == 0:
            return True
        # Fallback: just check if we can import and assume browser is there.
        return True
    except Exception:
        # If the dry-run check itself fails, assume installed if the import
        # succeeded -- the actual browser launch will surface errors later.
        return True


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DOU_SEARCH_URL = "https://www.in.gov.br/consulta/-/buscar/dou"
_DOU_ARTICLE_BASE = "https://www.in.gov.br/web/dou/-/"
_DOU_BASE = "https://www.in.gov.br"

_PORTLET_ELEMENT_ID = (
    "#_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params"
)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

_HTTP_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

_PLAYWRIGHT_TIMEOUT_MS = 45_000  # 45 seconds for page + element wait
_HTTP_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# DOUClient
# ---------------------------------------------------------------------------


class DOUClient:
    """Cliente para busca na Secao 3 do Diario Oficial da Uniao (DOU).

    Usa Playwright (headless browser) como estrategia primaria e HTTP
    scraping como fallback.
    """

    def __init__(self, *, playwright_timeout_ms: int = _PLAYWRIGHT_TIMEOUT_MS):
        self.search_url = _DOU_SEARCH_URL
        self.playwright_timeout_ms = playwright_timeout_ms
        self._http_timeout = _HTTP_TIMEOUT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def buscar_secao3(
        self,
        data_publicacao: str,
        termo: str | None = None,
    ) -> list[dict]:
        """Busca publicacoes na Secao 3 do DOU.

        Args:
            data_publicacao: Data no formato ``YYYY-MM-DD``.
            termo: Termo opcional de busca textual.

        Returns:
            Lista de dicts de publicacao.  Cada dict pode conter chaves como
            ``title``, ``abstract``, ``content``, ``urlTitle``, ``artType``,
            ``artCategory``, ``pubDate``, ``hierarchy``, entre outras.
        """
        date_dou = self._format_date_for_dou(data_publicacao)

        # Strategy 1 -- Playwright
        if _PLAYWRIGHT_AVAILABLE:
            try:
                results = await self._buscar_playwright(date_dou, termo)
                if results:
                    logger.info(
                        "Playwright: %d publicacoes encontradas para %s",
                        len(results),
                        data_publicacao,
                    )
                    return results
                logger.warning(
                    "Playwright retornou 0 resultados para %s; "
                    "tentando fallback HTTP",
                    data_publicacao,
                )
            except Exception:
                logger.exception(
                    "Erro na estrategia Playwright para %s; "
                    "tentando fallback HTTP",
                    data_publicacao,
                )
        else:
            logger.info(
                "Playwright indisponivel; usando fallback HTTP para %s",
                data_publicacao,
            )

        # Strategy 2 -- HTTP fallback
        try:
            results = await self._buscar_http(date_dou, termo)
            logger.info(
                "HTTP fallback: %d publicacoes encontradas para %s",
                len(results),
                data_publicacao,
            )
            return results
        except Exception:
            logger.exception(
                "Erro na estrategia HTTP para %s", data_publicacao
            )
            return []

    async def buscar_materia(self, url_title: str) -> dict | None:
        """Busca o conteudo completo de uma materia individual do DOU.

        Args:
            url_title: Caminho relativo (e.g. ``aviso-de-licitacao-123456``)
                ou URL completa do artigo.

        Returns:
            Dict com chaves ``titulo``, ``orgao``, ``conteudo_completo``,
            ``data_publicacao``, ``secao``, ``tipo_ato`` -- ou ``None`` se
            a pagina nao puder ser acessada/parseada.
        """
        url = self._resolve_article_url(url_title)

        # Try Playwright first for individual articles too
        if _PLAYWRIGHT_AVAILABLE:
            try:
                result = await self._buscar_materia_playwright(url)
                if result:
                    return result
                logger.debug(
                    "Playwright nao extraiu conteudo de %s; tentando HTTP", url
                )
            except Exception:
                logger.debug(
                    "Playwright falhou para materia %s; tentando HTTP",
                    url,
                    exc_info=True,
                )

        # HTTP fallback
        try:
            return await self._buscar_materia_http(url)
        except Exception:
            logger.exception("Erro ao buscar materia %s", url)
            return None

    # ------------------------------------------------------------------
    # Strategy 1: Playwright
    # ------------------------------------------------------------------

    async def _buscar_playwright(
        self, date_dou: str, termo: str | None
    ) -> list[dict]:
        """Use Playwright to render the DOU search page and extract results."""
        from playwright.async_api import async_playwright

        url = self._build_search_url(date_dou, termo)
        logger.debug("Playwright: navegando para %s", url)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=_USER_AGENT,
                    locale="pt-BR",
                    viewport={"width": 1280, "height": 720},
                )
                page = await context.new_page()

                await page.goto(url, wait_until="domcontentloaded",
                                timeout=self.playwright_timeout_ms)

                # Wait for the portlet element to be populated with JSON data.
                # The element exists in the initial HTML but its innerHTML is
                # empty until JavaScript fills it.
                portlet_el = page.locator(_PORTLET_ELEMENT_ID)
                await portlet_el.wait_for(
                    state="attached", timeout=self.playwright_timeout_ms
                )

                # Poll until innerHTML is non-empty (JS has populated it).
                inner_html = ""
                try:
                    await page.wait_for_function(
                        f"""() => {{
                            const el = document.querySelector('{_PORTLET_ELEMENT_ID}');
                            return el && el.innerHTML.trim().length > 10;
                        }}""",
                        timeout=self.playwright_timeout_ms,
                    )
                    inner_html = await portlet_el.inner_html()
                except Exception:
                    # Element might exist but never get populated (no results)
                    inner_html = await portlet_el.inner_html()

                if not inner_html or not inner_html.strip():
                    logger.debug("Portlet element is empty -- no results")
                    return []

                return self._parse_portlet_json(inner_html)

            finally:
                await browser.close()

    async def _buscar_materia_playwright(self, url: str) -> dict | None:
        """Use Playwright to fetch and parse an individual DOU article."""
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=_USER_AGENT,
                    locale="pt-BR",
                )
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded",
                                timeout=self.playwright_timeout_ms)

                # Wait a moment for JS rendering
                await page.wait_for_load_state("networkidle",
                                               timeout=self.playwright_timeout_ms)

                page_html = await page.content()
                return self._parse_article_html(page_html, url)
            finally:
                await browser.close()

    # ------------------------------------------------------------------
    # Strategy 2: HTTP scraping (fallback)
    # ------------------------------------------------------------------

    async def _buscar_http(
        self, date_dou: str, termo: str | None
    ) -> list[dict]:
        """Fallback: try plain HTTP GET and parse whatever JSON the server
        includes in the initial HTML response."""
        url = self._build_search_url(date_dou, termo)
        logger.debug("HTTP fallback: GET %s", url)

        async with httpx.AsyncClient(
            timeout=self._http_timeout,
            follow_redirects=True,
            headers=_HTTP_HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        return self._parse_results_html(response.text)

    async def _buscar_materia_http(self, url: str) -> dict | None:
        """Fetch an individual DOU article page via plain HTTP."""
        logger.debug("HTTP: GET %s", url)

        async with httpx.AsyncClient(
            timeout=self._http_timeout,
            follow_redirects=True,
            headers=_HTTP_HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        return self._parse_article_html(response.text, url)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_portlet_json(raw: str) -> list[dict]:
        """Parse the JSON blob from the Liferay portlet element.

        The element innerHTML is a JSON object with a ``jsonArray`` key
        whose value is a JSON-encoded string of an array of articles.
        """
        try:
            # The raw content may be HTML-entity-encoded JSON
            decoded = html.unescape(raw).strip()
            data = json.loads(decoded)
        except json.JSONDecodeError:
            # Sometimes the element contains the JSON as a value attribute
            # inside a nested tag.
            value_match = re.search(
                r'value=["\']({.*?})["\']', raw, re.DOTALL
            )
            if not value_match:
                logger.warning(
                    "Nao foi possivel parsear JSON do portlet: %.200s", raw
                )
                return []
            try:
                data = json.loads(html.unescape(value_match.group(1)))
            except json.JSONDecodeError:
                logger.warning("Fallback de parse do portlet tambem falhou")
                return []

        # Extract jsonArray
        json_array_raw = data.get("jsonArray")
        if not json_array_raw:
            logger.debug("Chave 'jsonArray' ausente ou vazia no portlet data")
            return []

        if isinstance(json_array_raw, list):
            return json_array_raw

        if isinstance(json_array_raw, str):
            try:
                articles = json.loads(json_array_raw)
                if isinstance(articles, list):
                    return articles
            except json.JSONDecodeError:
                logger.warning("Falha ao parsear jsonArray string")

        return []

    @staticmethod
    def _parse_results_html(page_html: str) -> list[dict]:
        """Extract search results from raw HTML (HTTP fallback).

        Tries multiple patterns since the DOU portal may embed the data
        differently across page versions.
        """
        results: list[dict] = []

        # Pattern 1: var params = {...}; with jsonArray inside
        json_pattern = re.compile(
            r"var\s+params\s*=\s*(\{.*?\});", re.DOTALL
        )
        match = json_pattern.search(page_html)
        if match:
            try:
                data = json.loads(match.group(1))
                json_array = data.get("jsonArray")
                if json_array:
                    parsed = (
                        json.loads(json_array)
                        if isinstance(json_array, str)
                        else json_array
                    )
                    if isinstance(parsed, list) and parsed:
                        return parsed
            except (json.JSONDecodeError, KeyError):
                logger.debug("Pattern 1 (var params) falhou")

        # Pattern 2: "jsonArray" : "[...]" -- Liferay-style
        json_array_pattern = re.compile(
            r'"jsonArray"\s*:\s*"(\[.*?\])"', re.DOTALL
        )
        match = json_array_pattern.search(page_html)
        if match:
            try:
                json_str = (
                    match.group(1).replace('\\"', '"').replace("\\/", "/")
                )
                parsed = json.loads(json_str)
                if isinstance(parsed, list) and parsed:
                    return parsed
            except json.JSONDecodeError:
                logger.debug("Pattern 2 (jsonArray inline) falhou")

        # Pattern 3: portlet element with id containing JSON
        portlet_pattern = re.compile(
            r'id=["\']_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params["\'][^>]*>'
            r"(.*?)</",
            re.DOTALL,
        )
        match = portlet_pattern.search(page_html)
        if match:
            inner = html.unescape(match.group(1)).strip()
            if inner:
                try:
                    data = json.loads(inner)
                    json_array = data.get("jsonArray")
                    if json_array:
                        parsed = (
                            json.loads(json_array)
                            if isinstance(json_array, str)
                            else json_array
                        )
                        if isinstance(parsed, list) and parsed:
                            return parsed
                except json.JSONDecodeError:
                    logger.debug("Pattern 3 (portlet element) falhou")

        # Pattern 4: search-result divs (very basic extraction)
        result_pattern = re.compile(
            r'<div[^>]*class="[^"]*resultado-busca-dou[^"]*"[^>]*>(.*?)</div>',
            re.DOTALL,
        )
        for block in result_pattern.finditer(page_html):
            entry: dict = {}
            title_match = re.search(
                r'<a[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>',
                block.group(1),
                re.DOTALL,
            )
            if title_match:
                entry["urlTitle"] = title_match.group(1)
                entry["title"] = re.sub(
                    r"<[^>]+>", "", title_match.group(2)
                ).strip()
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

    @staticmethod
    def _parse_article_html(page_html: str, source_url: str) -> dict | None:
        """Parse an individual DOU article page into a structured dict."""
        if not page_html:
            return None

        result: dict = {
            "titulo": None,
            "orgao": None,
            "conteudo_completo": None,
            "data_publicacao": None,
            "secao": "3",
            "tipo_ato": None,
            "url": source_url,
        }

        # Title: <p class="identifica">...</p> or <h3 class="titulo-dou">
        for pattern in [
            re.compile(
                r'<p[^>]*class="[^"]*identifica[^"]*"[^>]*>(.*?)</p>',
                re.DOTALL,
            ),
            re.compile(
                r'<h\d[^>]*class="[^"]*titulo-dou[^"]*"[^>]*>(.*?)</h\d>',
                re.DOTALL,
            ),
            re.compile(r"<title>(.*?)</title>", re.DOTALL),
        ]:
            match = pattern.search(page_html)
            if match:
                result["titulo"] = _strip_html(match.group(1)).strip()
                if result["titulo"]:
                    break

        # Orgao: <span class="orgao-dou-data">...</span>
        for pattern in [
            re.compile(
                r'<span[^>]*class="[^"]*orgao-dou-data[^"]*"[^>]*>(.*?)</span>',
                re.DOTALL,
            ),
            re.compile(
                r'<p[^>]*class="[^"]*orgao-dou[^"]*"[^>]*>(.*?)</p>',
                re.DOTALL,
            ),
        ]:
            match = pattern.search(page_html)
            if match:
                result["orgao"] = _strip_html(match.group(1)).strip()
                if result["orgao"]:
                    break

        # Full content: <div class="texto-dou"> or <div class="dou-paragraph">
        for pattern in [
            re.compile(
                r'<div[^>]*class="[^"]*texto-dou[^"]*"[^>]*>(.*?)</div>',
                re.DOTALL,
            ),
            re.compile(
                r'<div[^>]*class="[^"]*dou-paragraph[^"]*"[^>]*>(.*?)</div>',
                re.DOTALL,
            ),
        ]:
            match = pattern.search(page_html)
            if match:
                result["conteudo_completo"] = _strip_html(
                    match.group(1)
                ).strip()
                if result["conteudo_completo"]:
                    break

        # Publication date: <span class="publicado-dou-data">...</span>
        date_match = re.search(
            r'<span[^>]*class="[^"]*publicado-dou-data[^"]*"[^>]*>(.*?)</span>',
            page_html,
            re.DOTALL,
        )
        if date_match:
            raw_date = _strip_html(date_match.group(1)).strip()
            result["data_publicacao"] = _parse_date_br(raw_date)

        # Article type: <span class="detalhes-dou">...</span> or from title
        type_match = re.search(
            r'<span[^>]*class="[^"]*detalhes-dou[^"]*"[^>]*>(.*?)</span>',
            page_html,
            re.DOTALL,
        )
        if type_match:
            result["tipo_ato"] = _strip_html(type_match.group(1)).strip()

        if not result["tipo_ato"] and result["titulo"]:
            result["tipo_ato"] = _infer_tipo_ato(result["titulo"])

        # Only return if we got at least a title or content
        if result["titulo"] or result["conteudo_completo"]:
            return result

        logger.debug("Nenhum conteudo extraido de %s", source_url)
        return None

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_date_for_dou(iso_date: str) -> str:
        """Convert ``YYYY-MM-DD`` to ``DD-MM-YYYY`` for the DOU portal."""
        parts = iso_date.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Data invalida (esperado YYYY-MM-DD): {iso_date}"
            )
        return f"{parts[2]}-{parts[1]}-{parts[0]}"

    def _build_search_url(self, date_dou: str, termo: str | None) -> str:
        """Build the full DOU search URL with query parameters."""
        params = (
            f"s=do3"
            f"&exactDate=personalizado"
            f"&publishFrom={date_dou}"
            f"&publishTo={date_dou}"
        )
        if termo:
            from urllib.parse import quote

            params += f"&q={quote(termo)}"
        return f"{self.search_url}?{params}"

    @staticmethod
    def _resolve_article_url(url_title: str) -> str:
        """Resolve an article URL-title to a full URL."""
        if url_title.startswith("http"):
            return url_title
        # Remove leading slash if present
        slug = url_title.lstrip("/")
        # If it already contains the path prefix, use base domain
        if slug.startswith("web/dou/"):
            return f"{_DOU_BASE}/{slug}"
        return f"{_DOU_ARTICLE_BASE}{slug}"


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    return html.unescape(_HTML_TAG_RE.sub("", text))


def _parse_date_br(raw: str) -> str | None:
    """Try to parse a Brazilian date string to ISO format.

    Handles formats like ``01/03/2025`` or ``01 de marco de 2025``.
    Returns ``YYYY-MM-DD`` or ``None``.
    """
    if not raw:
        return None
    # DD/MM/YYYY
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # DD-MM-YYYY
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # Try parsing with datetime
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d de %B de %Y"):
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


_TIPO_ATO_KEYWORDS = {
    "aviso de licitacao": "aviso de licitacao",
    "aviso de licitação": "aviso de licitacao",
    "extrato de contrato": "extrato de contrato",
    "extrato de inexigibilidade": "extrato de inexigibilidade",
    "extrato de dispensa": "extrato de dispensa",
    "resultado de julgamento": "resultado de julgamento",
    "resultado de habilitacao": "resultado de habilitacao",
    "resultado de habilitação": "resultado de habilitacao",
    "retificacao": "retificacao",
    "retificação": "retificacao",
    "pregao": "pregao",
    "pregão": "pregao",
    "concorrencia": "concorrencia",
    "concorrência": "concorrencia",
    "tomada de precos": "tomada de precos",
    "tomada de preços": "tomada de precos",
    "convite": "convite",
    "ata de registro": "ata de registro de precos",
    "registro de precos": "ata de registro de precos",
    "registro de preços": "ata de registro de precos",
}


def _infer_tipo_ato(titulo: str) -> str | None:
    """Infer the tipo_ato from the article title."""
    titulo_lower = titulo.lower()
    for keyword, tipo in _TIPO_ATO_KEYWORDS.items():
        if keyword in titulo_lower:
            return tipo
    return None
