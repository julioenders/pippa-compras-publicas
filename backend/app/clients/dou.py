"""Cliente para busca na Secao 3 do Diario Oficial da Uniao (DOU).

Coleta publicacoes via HTTP puro (sem Playwright/headless browser),
parseando o JSON que o Liferay embute no HTML server-side dentro do
elemento portlet ``BuscaDouPortlet_params``.

Como o portal nao suporta paginacao via URL, a cobertura e maximizada
fazendo multiplas buscas com termos especificos de compras publicas
(licitacao, pregao, contrato, etc.) e deduplicando por ``urlTitle``.
"""

from __future__ import annotations

import html as html_mod
import json
import logging
import re
from datetime import datetime
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DOU_SEARCH_URL = "https://www.in.gov.br/consulta/-/buscar/dou"
_DOU_ARTICLE_BASE = "https://www.in.gov.br/web/dou/-/"
_DOU_BASE = "https://www.in.gov.br"

_PORTLET_RE = re.compile(
    r'id="_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params"[^>]*>'
    r"(.*?)</",
    re.DOTALL,
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

_HTTP_TIMEOUT = 45.0
_RESULTS_PER_PAGE = 75

# Termos de busca para compras publicas -- cada termo gera uma requisicao
# HTTP separada e os resultados sao deduplicados por urlTitle.
_TERMOS_COMPRAS = [
    '"aviso de licitacao"',
    '"pregao eletronico"',
    '"resultado de julgamento"',
    '"extrato de contrato"',
    '"dispensa de licitacao"',
    '"inexigibilidade"',
    '"registro de precos"',
    '"concorrencia"',
    '"tomada de precos"',
    '"credenciamento"',
    '"chamamento publico"',
    '"extrato de termo aditivo"',
    '"homologacao"',
    '"adjudicacao"',
    '"aviso de suspensao"',
    '"aviso de revogacao"',
    '"aviso de anulacao"',
    '"aviso de alteracao"',
    '"edital de licitacao"',
]


# ---------------------------------------------------------------------------
# DOUClient
# ---------------------------------------------------------------------------


class DOUClient:
    """Cliente HTTP para busca na Secao 3 do DOU.

    Faz requisicoes HTTP GET ao portal in.gov.br e extrai o JSON que o
    Liferay embute no HTML server-side.  Nao requer Playwright nem
    headless browser.
    """

    def __init__(self, *, timeout: float = _HTTP_TIMEOUT):
        self.search_url = _DOU_SEARCH_URL
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def buscar_secao3(
        self,
        data_publicacao: str,
        termo: str | None = None,
    ) -> list[dict]:
        """Busca publicacoes na Secao 3 do DOU.

        Faz multiplas requisicoes HTTP com termos especificos de compras
        publicas e deduplica os resultados por ``urlTitle``.

        Args:
            data_publicacao: Data no formato ``YYYY-MM-DD``.
            termo: Termo de busca.  Se fornecido, faz apenas uma busca
                com esse termo.  Se ``None``, usa a lista padrao de
                termos de compras publicas.

        Returns:
            Lista de dicts com chaves como ``title``, ``content``,
            ``urlTitle``, ``artType``, ``pubDate``, ``hierarchyStr``, etc.
        """
        date_dou = self._format_date_for_dou(data_publicacao)

        if termo:
            results = await self._buscar_termo(date_dou, termo)
            logger.info(
                "%d publicacoes encontradas para %s (termo: %s)",
                len(results), data_publicacao, termo,
            )
            return results

        seen: set[str] = set()
        all_results: list[dict] = []

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers=_HTTP_HEADERS,
            verify=False,
        ) as client:
            for search_term in _TERMOS_COMPRAS:
                try:
                    articles = await self._buscar_termo_com_client(
                        client, date_dou, search_term,
                    )
                except Exception:
                    logger.warning(
                        "Erro na busca DOU com termo %s", search_term,
                        exc_info=True,
                    )
                    continue

                new_count = 0
                for art in articles:
                    key = art.get("urlTitle") or art.get("classPK", "")
                    if key and key not in seen:
                        seen.add(key)
                        all_results.append(art)
                        new_count += 1

                logger.debug(
                    "Termo %s: %d resultados, %d novos (total: %d)",
                    search_term, len(articles), new_count, len(all_results),
                )

        logger.info(
            "%d publicacoes unicas encontradas para %s (%d termos)",
            len(all_results), data_publicacao, len(_TERMOS_COMPRAS),
        )
        return all_results

    async def buscar_materia(self, url_title: str) -> dict | None:
        """Busca o conteudo completo de uma materia individual do DOU."""
        url = self._resolve_article_url(url_title)

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers=_HTTP_HEADERS,
                verify=False,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            return self._parse_article_html(response.text, url)
        except Exception:
            logger.exception("Erro ao buscar materia %s", url)
            return None

    # ------------------------------------------------------------------
    # HTTP search
    # ------------------------------------------------------------------

    async def _buscar_termo(self, date_dou: str, termo: str) -> list[dict]:
        """Single-term search with a fresh client."""
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers=_HTTP_HEADERS,
            verify=False,
        ) as client:
            return await self._buscar_termo_com_client(
                client, date_dou, termo
            )

    async def _buscar_termo_com_client(
        self,
        client: httpx.AsyncClient,
        date_dou: str,
        termo: str,
    ) -> list[dict]:
        """Fetch one search term using an existing client."""
        url = self._build_search_url(date_dou, termo)
        response = await client.get(url)
        response.raise_for_status()
        return self._extract_articles_from_html(response.text)

    # ------------------------------------------------------------------
    # HTML parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_articles_from_html(page_html: str) -> list[dict]:
        """Extract the article list from the portlet JSON in the HTML."""
        match = _PORTLET_RE.search(page_html)
        if not match:
            return []

        raw = match.group(1).strip()
        if not raw:
            return []

        try:
            decoded = html_mod.unescape(raw)
            data = json.loads(decoded)
        except (json.JSONDecodeError, ValueError):
            logger.debug("Falha ao parsear portlet JSON")
            return []

        json_array = data.get("jsonArray")
        if not json_array:
            return []

        if isinstance(json_array, list):
            return json_array

        if isinstance(json_array, str):
            try:
                parsed = json.loads(json_array)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []

        return []

    @staticmethod
    def _parse_article_html(page_html: str, source_url: str) -> dict | None:
        """Parse an individual DOU article page."""
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
            m = pattern.search(page_html)
            if m:
                result["titulo"] = _strip_html(m.group(1)).strip()
                if result["titulo"]:
                    break

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
            m = pattern.search(page_html)
            if m:
                result["orgao"] = _strip_html(m.group(1)).strip()
                if result["orgao"]:
                    break

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
            m = pattern.search(page_html)
            if m:
                result["conteudo_completo"] = _strip_html(m.group(1)).strip()
                if result["conteudo_completo"]:
                    break

        date_match = re.search(
            r'<span[^>]*class="[^"]*publicado-dou-data[^"]*"[^>]*>(.*?)</span>',
            page_html, re.DOTALL,
        )
        if date_match:
            result["data_publicacao"] = _parse_date_br(
                _strip_html(date_match.group(1)).strip()
            )

        type_match = re.search(
            r'<span[^>]*class="[^"]*detalhes-dou[^"]*"[^>]*>(.*?)</span>',
            page_html, re.DOTALL,
        )
        if type_match:
            result["tipo_ato"] = _strip_html(type_match.group(1)).strip()

        if not result["tipo_ato"] and result["titulo"]:
            result["tipo_ato"] = _infer_tipo_ato(result["titulo"])

        if result["titulo"] or result["conteudo_completo"]:
            return result
        return None

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_date_for_dou(iso_date: str) -> str:
        """Convert ``YYYY-MM-DD`` to ``DD-MM-YYYY`` for the DOU portal."""
        parts = iso_date.split("-")
        if len(parts) != 3:
            raise ValueError(f"Data invalida (esperado YYYY-MM-DD): {iso_date}")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"

    def _build_search_url(self, date_dou: str, termo: str) -> str:
        """Build the full DOU search URL."""
        return (
            f"{self.search_url}"
            f"?q={quote(termo)}"
            f"&s=do3"
            f"&exactDate=personalizado"
            f"&publishFrom={date_dou}"
            f"&publishTo={date_dou}"
            f"&delta={_RESULTS_PER_PAGE}"
        )

    @staticmethod
    def _resolve_article_url(url_title: str) -> str:
        """Resolve an article URL-title to a full URL."""
        if url_title.startswith("http"):
            return url_title
        slug = url_title.lstrip("/")
        if slug.startswith("web/dou/"):
            return f"{_DOU_BASE}/{slug}"
        return f"{_DOU_ARTICLE_BASE}{slug}"


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    return html_mod.unescape(_HTML_TAG_RE.sub("", text))


def _parse_date_br(raw: str) -> str | None:
    """Parse a Brazilian date string to ISO format."""
    if not raw:
        return None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
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
