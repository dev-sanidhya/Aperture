from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchClient:
    DDG_HTML_URL = "https://html.duckduckgo.com/html/"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "ApertureBot/0.1"}) as client:
            response = await client.post(self.DDG_HTML_URL, data={"q": query})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for node in soup.select(".result"):
            link = node.select_one("a.result__a")
            if not link:
                continue
            url = link.get("href", "").strip()
            if not url:
                continue
            results.append(
                SearchResult(
                    title=link.get_text(" ", strip=True),
                    url=url,
                    snippet=(node.select_one(".result__snippet").get_text(" ", strip=True) if node.select_one(".result__snippet") else ""),
                )
            )
            if len(results) >= max_results:
                break
        return results


def root_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host

