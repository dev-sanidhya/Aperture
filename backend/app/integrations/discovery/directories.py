from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.integrations.discovery.search import root_domain
from app.services.normalization import normalize_phone


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
MOBILE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")


@dataclass(slots=True)
class DirectoryExtraction:
    final_url: str
    directory_name: str
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    website_urls: list[str] = field(default_factory=list)
    whatsapp_numbers: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)
    notes: str | None = None


class DirectoryClient:
    def __init__(self) -> None:
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; ApertureBot/0.1)"}

    async def extract(self, url: str) -> DirectoryExtraction | None:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=self.headers) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError:
                return None
        return self._parse(str(response.url), response.text)

    def _parse(self, final_url: str, html: str) -> DirectoryExtraction:
        soup = BeautifulSoup(html, "html.parser")
        text = unescape(soup.get_text(" ", strip=True))
        emails = dedupe([email.lower() for email in EMAIL_RE.findall(text)])
        phones = dedupe([normalize_phone(phone) for phone in MOBILE_RE.findall(text)])
        website_urls: list[str] = []
        whatsapp_numbers: list[str] = []
        social_links: list[str] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            absolute = urljoin(final_url, href)
            lowered = absolute.lower()
            if href.startswith("mailto:"):
                emails = dedupe(emails + [href.removeprefix("mailto:").split("?")[0].strip().lower()])
            elif href.startswith("tel:"):
                phones = dedupe(phones + [normalize_phone(href.removeprefix("tel:"))])
            elif any(domain in lowered for domain in ("instagram.com", "facebook.com", "linkedin.com")):
                social_links.append(absolute)
            elif "wa.me/" in lowered or "api.whatsapp.com" in lowered:
                digits = re.sub(r"\D", "", absolute)
                if len(digits) >= 10:
                    whatsapp_numbers.append(normalize_phone(digits[-12:] if digits.startswith("91") else digits[-10:]))
            elif lowered.startswith("http"):
                host = root_domain(absolute)
                if host not in {"justdial.com", "indiamart.com", "sulekha.com", "tradeindia.com"}:
                    website_urls.append(absolute)

        title = soup.title.get_text(" ", strip=True) if soup.title else root_domain(final_url)
        note_parts: list[str] = []
        if phones:
            note_parts.append("public phone present")
        if emails:
            note_parts.append("public email present")
        if website_urls:
            note_parts.append("website listed")
        if not note_parts:
            note_parts.append("directory page captured")

        return DirectoryExtraction(
            final_url=final_url,
            directory_name=root_domain(final_url),
            phones=phones,
            emails=emails,
            website_urls=dedupe(website_urls),
            whatsapp_numbers=dedupe(whatsapp_numbers),
            social_links=dedupe(social_links),
            notes=f"{title}: " + ", ".join(note_parts),
        )


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out

