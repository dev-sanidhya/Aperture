from __future__ import annotations

import re
from urllib.parse import urlparse


SPACE_RE = re.compile(r"\s+")


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s&]", " ", value)
    value = value.replace("&", " and ")
    return SPACE_RE.sub(" ", value).strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    return value.strip()


def normalize_domain(url_or_domain: str) -> str:
    value = url_or_domain.lower().strip()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0]
    return value.removeprefix("www.")


DIRECTORY_DOMAINS = {
    "justdial.com",
    "indiamart.com",
    "sulekha.com",
    "tradeindia.com",
}

SOCIAL_DOMAINS = {
    "instagram.com",
    "facebook.com",
    "linkedin.com",
}


def hostname(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_directory_domain(url: str) -> bool:
    return hostname(url) in DIRECTORY_DOMAINS


def is_social_domain(url: str) -> bool:
    return hostname(url) in SOCIAL_DOMAINS
