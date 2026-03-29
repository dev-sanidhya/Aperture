from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.normalization import normalize_domain, normalize_phone


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
MOBILE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
WHATSAPP_RE = re.compile(r"(wa\.me/|api\.whatsapp\.com/send|whatsapp\.com/)", re.I)


@dataclass(slots=True)
class WebsiteExtraction:
    final_url: str
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    whatsapp_numbers: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)
    contact_pages: list[str] = field(default_factory=list)
    audit_summary: str | None = None


class WebsiteClient:
    def __init__(self) -> None:
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; ApertureBot/0.1)"}

    async def extract(self, url: str) -> WebsiteExtraction | None:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=self.headers) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError:
                return None

            extraction = self._parse_page(str(response.url), response.text)

            for contact_url in extraction.contact_pages[:2]:
                try:
                    contact_response = await client.get(contact_url)
                    contact_response.raise_for_status()
                except httpx.HTTPError:
                    continue
                contact_extraction = self._parse_page(str(contact_response.url), contact_response.text)
                extraction.emails = dedupe(extraction.emails + contact_extraction.emails)
                extraction.phones = dedupe(extraction.phones + contact_extraction.phones)
                extraction.whatsapp_numbers = dedupe(extraction.whatsapp_numbers + contact_extraction.whatsapp_numbers)
                extraction.social_links = dedupe(extraction.social_links + contact_extraction.social_links)
                extraction.contact_pages = dedupe(extraction.contact_pages + contact_extraction.contact_pages)

            extraction.audit_summary = self._build_audit_summary(extraction)
            return extraction

    def _parse_page(self, base_url: str, html: str) -> WebsiteExtraction:
        soup = BeautifulSoup(html, "html.parser")
        text = unescape(soup.get_text(" ", strip=True))
        emails = dedupe([email.lower() for email in EMAIL_RE.findall(text)])
        phones = dedupe([normalize_phone(phone) for phone in MOBILE_RE.findall(text)])
        whatsapp_numbers: list[str] = []
        social_links: list[str] = []
        contact_pages: list[str] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            absolute = urljoin(base_url, href)
            lowered = absolute.lower()
            if href.startswith("mailto:"):
                emails = dedupe(emails + [href.removeprefix("mailto:").split("?")[0].strip().lower()])
            elif href.startswith("tel:"):
                phones = dedupe(phones + [normalize_phone(href.removeprefix("tel:"))])
            elif WHATSAPP_RE.search(lowered):
                social_links.append(absolute)
                digits = re.sub(r"\D", "", absolute)
                if len(digits) >= 10:
                    whatsapp_numbers.append(normalize_phone(digits[-12:] if digits.startswith("91") else digits[-10:]))
            elif any(domain in lowered for domain in ("instagram.com", "facebook.com", "linkedin.com")):
                social_links.append(absolute)

            anchor_text = anchor.get_text(" ", strip=True).lower()
            if any(keyword in lowered or keyword in anchor_text for keyword in ("contact", "about", "reach", "connect")):
                parsed = urlparse(absolute)
                if normalize_domain(absolute) == normalize_domain(base_url) and parsed.scheme in {"http", "https"}:
                    contact_pages.append(absolute)

        return WebsiteExtraction(
            final_url=base_url,
            emails=emails,
            phones=phones,
            whatsapp_numbers=dedupe(whatsapp_numbers),
            social_links=dedupe(social_links),
            contact_pages=dedupe(contact_pages),
        )

    @staticmethod
    def _build_audit_summary(extraction: WebsiteExtraction) -> str:
        issues: list[str] = []
        if not extraction.emails:
            issues.append("no public email found")
        if not extraction.whatsapp_numbers:
            issues.append("no WhatsApp link found")
        if not extraction.contact_pages:
            issues.append("no obvious contact page found")
        if not issues:
            return "Website exposes multiple direct contact paths."
        return "Website review: " + ", ".join(issues[:2]) + "."


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
