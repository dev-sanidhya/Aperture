from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "data" / "prospects"
TODAY = date.today().isoformat()

SEED_URLS_FILE = SCRIPT_DIR / "agency_seed_urls.txt"
SEED_URLS_EXAMPLE_FILE = SCRIPT_DIR / "agency_seed_urls.example.txt"
LIST_SOURCES_FILE = SCRIPT_DIR / "agency_discovery_sources.txt"
LIST_SOURCES_EXAMPLE_FILE = SCRIPT_DIR / "agency_discovery_sources.example.txt"

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
SERPER_SEARCH_URL = "https://google.serper.dev/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
EXA_SEARCH_URL = "https://api.exa.ai/search"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TARGET_COUNTRIES = ("United States", "United Kingdom", "Canada", "Australia")

SEGMENTS: dict[str, dict[str, list[str]]] = {
    "b2b-lead-gen": {
        "terms": [
            "B2B lead generation agency",
            "appointment setting agency B2B",
            "sales development agency SaaS",
            "outbound sales agency B2B",
        ],
        "fit_terms": [
            "b2b lead generation",
            "appointment setting",
            "sales development",
            "outbound",
            "pipeline generation",
        ],
    },
    "paid-media-seo": {
        "terms": [
            "paid media agency B2B SaaS",
            "PPC agency B2B SaaS",
            "SEO agency B2B SaaS",
            "performance marketing agency B2B SaaS",
        ],
        "fit_terms": [
            "paid media",
            "ppc",
            "seo",
            "performance marketing",
            "google ads",
            "linkedin ads",
        ],
    },
    "revops-hubspot": {
        "terms": [
            "HubSpot partner agency RevOps",
            "revenue operations agency HubSpot",
            "CRM implementation agency B2B",
            "marketing automation agency HubSpot",
        ],
        "fit_terms": [
            "hubspot",
            "revops",
            "revenue operations",
            "crm implementation",
            "salesforce",
            "marketing automation",
        ],
    },
    "recruiting-staffing": {
        "terms": [
            "technology recruiting agency clients",
            "technology staffing agency clients",
            "executive search firm technology",
            "recruitment agency SaaS clients",
        ],
        "fit_terms": [
            "recruiting",
            "recruitment",
            "staffing",
            "executive search",
            "talent acquisition",
        ],
    },
    "product-dev": {
        "terms": [
            "software development agency AI startups",
            "product studio SaaS startups",
            "app development agency startups",
            "AI product development agency",
        ],
        "fit_terms": [
            "software development",
            "product studio",
            "app development",
            "ai product",
            "startups",
        ],
    },
}

QUERY_SUFFIXES = (
    "case studies {country}",
    "clients {country}",
    "results {country}",
    "book a call {country}",
)

B2B_TERMS = (
    "b2b",
    "saas",
    "startup",
    "startups",
    "founder",
    "revenue",
    "sales team",
    "marketing team",
    "technology company",
)

AGENCY_TERMS = (
    "agency",
    "consultancy",
    "consulting",
    "partner",
    "studio",
    "services",
    "firm",
)

LISTICLE_TERMS = (
    "top ",
    "best ",
    "list of",
    "companies in",
    "alternatives",
    "guide",
    "blog",
)

EXCLUDED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",
    "duckduckgo.com",
    "bing.com",
    "google.com",
    "serpapi.com",
    "brave.com",
    "clutch.co",
    "sortlist.com",
    "designrush.com",
    "themanifest.com",
    "upcity.com",
    "agencyspotter.com",
    "g2.com",
    "capterra.com",
    "trustpilot.com",
    "crunchbase.com",
    "wikipedia.org",
    "github.com",
    "medium.com",
    "forbes.com",
    "gartner.com",
    "hubspot.com",
}

TRACKING_DOMAINS = {
    "cta-na2.hubspot.com",
    "track.hubspot.com",
    "hsforms.com",
    "forms.hsforms.com",
    "doubleclick.net",
    "googleadservices.com",
}

RAW_FIELDS = [
    "source_type",
    "segment",
    "country",
    "query",
    "rank",
    "title",
    "url",
    "domain",
    "snippet",
    "source_url",
]

ACCOUNT_FIELDS = [
    "company_name",
    "website",
    "domain",
    "country",
    "segment",
    "source_count",
    "best_source_type",
    "best_source_query",
    "best_source_url",
    "best_title",
    "best_snippet",
    "discovery_score",
    "discovery_reasons",
    "status",
    "notes",
]

QUEUE_FIELDS = [
    "company_name",
    "website",
    "domain",
    "country",
    "segment",
    "source_type",
    "source_query",
    "source_url",
    "discovery_score",
    "discovery_reasons",
    "notes",
]


@dataclass(slots=True)
class SearchHit:
    source_type: str
    segment: str
    country: str
    query: str
    rank: int
    title: str
    url: str
    snippet: str
    source_url: str = ""


@dataclass(slots=True)
class AccountCandidate:
    company_name: str
    website: str
    domain: str
    country: str
    segment: str
    source_count: int
    best_source_type: str
    best_source_query: str
    best_source_url: str
    best_title: str
    best_snippet: str
    discovery_score: int
    discovery_reasons: list[str] = field(default_factory=list)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def root_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_url(url: str) -> str:
    value = clean_text(url)
    if not value:
        return ""
    if value.startswith("//"):
        value = f"https:{value}"
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".split("#")[0]


def base_website(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def is_excluded_domain(domain: str) -> bool:
    if not domain:
        return True
    if domain in TRACKING_DOMAINS:
        return True
    return any(domain == blocked or domain.endswith(f".{blocked}") for blocked in EXCLUDED_DOMAINS)


def company_name_from_domain(domain: str) -> str:
    stem = domain.split(".")[0]
    parts = re.split(r"[-_]+", stem)
    return " ".join(part.capitalize() for part in parts if part)


def company_name_from_title(title: str, domain: str) -> str:
    text = clean_text(title)
    for separator in (" | ", " - ", " / ", ": "):
        if separator in text:
            text = text.split(separator, 1)[0]
    text = re.sub(r"^(Top|Best)\s+\d+\s+", "", text, flags=re.I)
    text = clean_text(text)
    if not text or len(text) > 80:
        return company_name_from_domain(domain)
    return text


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        clean_text(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if clean_text(line) and not clean_text(line).startswith("#")
    ]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


def build_queries(segments: list[str], countries: list[str], max_queries: int) -> list[tuple[str, str, str]]:
    queries: list[tuple[str, str, str]] = []
    for segment in segments:
        config = SEGMENTS[segment]
        for country in countries:
            for term in config["terms"]:
                for suffix in QUERY_SUFFIXES:
                    queries.append((segment, country, f"{term} {suffix.format(country=country)}"))
                    if max_queries and len(queries) >= max_queries:
                        return queries
    return queries


def brave_search(query: str, *, api_key: str, count: int, timeout: float) -> list[dict[str, str]]:
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": min(count, 20), "search_lang": "en"}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.get(BRAVE_SEARCH_URL, params=params)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
        }
        for item in data.get("web", {}).get("results", [])
    ]


def serpapi_search(query: str, *, api_key: str, count: int, timeout: float) -> list[dict[str, str]]:
    params = {"engine": "google", "q": query, "num": min(count, 20), "api_key": api_key}
    with httpx.Client(timeout=timeout) as client:
        response = client.get(SERPAPI_SEARCH_URL, params=params)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in data.get("organic_results", [])
    ]


def google_cse_search(query: str, *, api_key: str, cse_id: str, count: int, timeout: float) -> list[dict[str, str]]:
    params = {"key": api_key, "cx": cse_id, "q": query, "num": min(count, 10)}
    with httpx.Client(timeout=timeout) as client:
        response = client.get(GOOGLE_CSE_URL, params=params)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in data.get("items", [])
    ]


def serper_search(query: str, *, api_key: str, count: int, timeout: float) -> list[dict[str, str]]:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": min(count, 20)}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.post(SERPER_SEARCH_URL, json=payload)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in data.get("organic", [])
    ]


def tavily_search(query: str, *, api_key: str, count: int, timeout: float) -> list[dict[str, str]]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": min(count, 20),
        "include_answer": False,
        "include_raw_content": False,
    }
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.post(TAVILY_SEARCH_URL, json=payload)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in data.get("results", [])
    ]


def exa_search(query: str, *, api_key: str, count: int, timeout: float) -> list[dict[str, str]]:
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    payload = {"query": query, "numResults": min(count, 20)}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.post(EXA_SEARCH_URL, json=payload)
        response.raise_for_status()
    data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("text", "") or item.get("summary", "") or item.get("author", ""),
        }
        for item in data.get("results", [])
    ]


def normalize_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if "duckduckgo.com/l/" not in url:
        return url
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url


def duckduckgo_html_search(query: str, *, count: int, timeout: float) -> list[dict[str, str]]:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.post(DUCKDUCKGO_HTML_URL, data={"q": query})
        response.raise_for_status()
    if response.status_code == 202 or "anomaly" in response.text.lower():
        print("  duckduckgo returned a throttle/anomaly page")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict[str, str]] = []
    for node in soup.select(".result"):
        link = node.select_one("a.result__a")
        if not link:
            continue
        snippet_node = node.select_one(".result__snippet")
        results.append(
            {
                "title": clean_text(link.get_text(" ", strip=True)),
                "url": normalize_duckduckgo_url(link.get("href", "")),
                "snippet": clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else ""),
            }
        )
        if len(results) >= count:
            break
    return results


def rows_from_search_results(
    source_type: str,
    segment: str,
    country: str,
    query: str,
    results: list[dict[str, str]],
) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for index, item in enumerate(results, start=1):
        url = normalize_url(item.get("url", ""))
        if not url:
            continue
        hits.append(
            SearchHit(
                source_type=source_type,
                segment=segment,
                country=country,
                query=query,
                rank=index,
                title=clean_text(item.get("title", "")),
                url=url,
                snippet=clean_text(item.get("snippet", "")),
            )
        )
    return hits


def discover_from_search(args: argparse.Namespace, source_type: str, queries: list[tuple[str, str, str]]) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for segment, country, query in queries:
        print(f"{source_type} searching: {query}")
        try:
            if source_type == "brave":
                results = brave_search(query, api_key=args.brave_api_key, count=args.max_results_per_query, timeout=args.timeout)
            elif source_type == "serpapi":
                results = serpapi_search(query, api_key=args.serpapi_api_key, count=args.max_results_per_query, timeout=args.timeout)
            elif source_type == "google-cse":
                results = google_cse_search(
                    query,
                    api_key=args.google_cse_api_key,
                    cse_id=args.google_cse_id,
                    count=args.max_results_per_query,
                    timeout=args.timeout,
                )
            elif source_type == "serper":
                results = serper_search(query, api_key=args.serper_api_key, count=args.max_results_per_query, timeout=args.timeout)
            elif source_type == "tavily":
                results = tavily_search(query, api_key=args.tavily_api_key, count=args.max_results_per_query, timeout=args.timeout)
            elif source_type == "exa":
                results = exa_search(query, api_key=args.exa_api_key, count=args.max_results_per_query, timeout=args.timeout)
            elif source_type == "duckduckgo":
                results = duckduckgo_html_search(query, count=args.max_results_per_query, timeout=args.timeout)
            else:
                raise ValueError(f"Unknown search source: {source_type}")
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            print(f"  {source_type} failed: {exc}")
            results = []
        hits.extend(rows_from_search_results(source_type, segment, country, query, results))
        if args.max_results and len(hits) >= args.max_results:
            return hits[: args.max_results]
        time.sleep(args.request_delay)
    return hits


def discover_from_seed(seed_file: Path, max_results: int) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for index, url in enumerate(load_lines(seed_file), start=1):
        normalized = normalize_url(url)
        domain = root_domain(normalized)
        if not normalized or is_excluded_domain(domain):
            continue
        hits.append(
            SearchHit(
                source_type="seed",
                segment="seed",
                country="",
                query=str(seed_file.name),
                rank=index,
                title=company_name_from_domain(domain),
                url=normalized,
                snippet="Seed agency URL",
            )
        )
        if max_results and len(hits) >= max_results:
            break
    return hits


def extract_links_from_list_page(page_url: str, timeout: float) -> list[dict[str, str]]:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.get(page_url)
        response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    page_host = root_domain(str(response.url))
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        url = normalize_url(urljoin(str(response.url), anchor.get("href", "")))
        domain = root_domain(url)
        if not url or domain == page_host or is_excluded_domain(domain) or domain in seen:
            continue
        seen.add(domain)
        links.append(
            {
                "title": clean_text(anchor.get_text(" ", strip=True)) or company_name_from_domain(domain),
                "url": base_website(url),
                "snippet": f"Outbound link from {page_url}",
            }
        )
    return links


def discover_from_list_pages(list_file: Path, args: argparse.Namespace) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for page_index, page_url in enumerate(load_lines(list_file), start=1):
        print(f"list-page extracting: {page_url}")
        try:
            links = extract_links_from_list_page(page_url, args.timeout)
        except httpx.HTTPError as exc:
            print(f"  list page failed: {exc}")
            links = []
        for index, item in enumerate(links, start=1):
            hits.append(
                SearchHit(
                    source_type="list-page",
                    segment="list-page",
                    country="",
                    query=str(list_file.name),
                    rank=index,
                    title=item["title"],
                    url=item["url"],
                    snippet=item["snippet"],
                    source_url=page_url,
                )
            )
            if args.max_results and len(hits) >= args.max_results:
                return hits
        time.sleep(args.request_delay)
        if args.max_list_pages and page_index >= args.max_list_pages:
            break
    return hits


def score_hit(hit: SearchHit) -> tuple[int, list[str]]:
    domain = root_domain(hit.url)
    haystack = f"{hit.title} {hit.snippet} {hit.query} {domain}".lower()
    reasons: list[str] = []
    score = 0

    if not is_excluded_domain(domain):
        score += 20
        reasons.append("direct-domain")
    else:
        score -= 40
        reasons.append("excluded-domain")

    segment_terms = SEGMENTS.get(hit.segment, {}).get("fit_terms", [])
    segment_matches = [term for term in segment_terms if term in haystack]
    if segment_matches:
        score += min(30, 10 * len(segment_matches))
        reasons.append(f"segment-match:{','.join(segment_matches[:3])}")

    b2b_matches = [term for term in B2B_TERMS if term in haystack]
    if b2b_matches:
        score += min(20, 5 * len(b2b_matches))
        reasons.append(f"b2b-signal:{','.join(b2b_matches[:3])}")

    agency_matches = [term for term in AGENCY_TERMS if term in haystack]
    if agency_matches:
        score += min(15, 5 * len(agency_matches))
        reasons.append(f"agency-signal:{','.join(agency_matches[:3])}")

    if hit.country and hit.country.lower() in haystack:
        score += 5
        reasons.append(f"country:{hit.country}")

    if any(term in haystack for term in LISTICLE_TERMS):
        score -= 10
        reasons.append("possible-listicle")

    if "job board" in haystack or "directory" in haystack:
        score -= 10
        reasons.append("directory-risk")

    if hit.source_type == "seed":
        score += 35
        reasons.append("curated-seed")
    elif hit.source_type == "list-page":
        score += 5
        reasons.append("list-page-source")

    return max(0, min(score, 100)), reasons


def collapse_hits(hits: list[SearchHit]) -> list[AccountCandidate]:
    grouped: dict[str, list[tuple[SearchHit, int, list[str]]]] = {}
    for hit in hits:
        url = normalize_url(hit.url)
        domain = root_domain(url)
        if not url or is_excluded_domain(domain):
            continue
        score, reasons = score_hit(hit)
        grouped.setdefault(domain, []).append((hit, score, reasons))

    accounts: list[AccountCandidate] = []
    for domain, items in grouped.items():
        best_hit, best_score, best_reasons = sorted(items, key=lambda item: item[1], reverse=True)[0]
        blended_score = min(100, best_score + min(15, 3 * (len(items) - 1)))
        if len(items) > 1:
            best_reasons = [*best_reasons, f"source-count:{len(items)}"]
        accounts.append(
            AccountCandidate(
                company_name=company_name_from_title(best_hit.title, domain),
                website=base_website(best_hit.url),
                domain=domain,
                country=best_hit.country,
                segment=best_hit.segment,
                source_count=len(items),
                best_source_type=best_hit.source_type,
                best_source_query=best_hit.query,
                best_source_url=best_hit.source_url or best_hit.url,
                best_title=best_hit.title,
                best_snippet=best_hit.snippet,
                discovery_score=blended_score,
                discovery_reasons=best_reasons,
            )
        )
    return sorted(accounts, key=lambda account: account.discovery_score, reverse=True)


def raw_row(hit: SearchHit) -> dict[str, str]:
    return {
        "source_type": hit.source_type,
        "segment": hit.segment,
        "country": hit.country,
        "query": hit.query,
        "rank": str(hit.rank),
        "title": hit.title,
        "url": hit.url,
        "domain": root_domain(hit.url),
        "snippet": hit.snippet,
        "source_url": hit.source_url,
    }


def account_row(account: AccountCandidate) -> dict[str, str]:
    reasons = "; ".join(account.discovery_reasons)
    notes = clean_text(f"{account.best_title}. {account.best_snippet}. Reasons: {reasons}")[:900]
    return {
        "company_name": account.company_name,
        "website": account.website,
        "domain": account.domain,
        "country": account.country,
        "segment": account.segment,
        "source_count": str(account.source_count),
        "best_source_type": account.best_source_type,
        "best_source_query": account.best_source_query,
        "best_source_url": account.best_source_url,
        "best_title": account.best_title,
        "best_snippet": account.best_snippet,
        "discovery_score": str(account.discovery_score),
        "discovery_reasons": reasons,
        "status": "discovered",
        "notes": notes,
    }


def queue_row(account: AccountCandidate) -> dict[str, str]:
    row = account_row(account)
    return {
        "company_name": row["company_name"],
        "website": row["website"],
        "domain": row["domain"],
        "country": row["country"],
        "segment": row["segment"],
        "source_type": row["best_source_type"],
        "source_query": row["best_source_query"],
        "source_url": row["best_source_url"],
        "discovery_score": row["discovery_score"],
        "discovery_reasons": row["discovery_reasons"],
        "notes": row["notes"],
    }


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_seed_file(path: Path, accounts: list[AccountCandidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(account.website for account in accounts) + ("\n" if accounts else ""), encoding="utf-8")


def write_runbook(path: Path, args: argparse.Namespace, accounts: list[AccountCandidate], queue: list[AccountCandidate]) -> None:
    lines = [
        "# Agency Discovery Runbook",
        "",
        f"Generated: {TODAY}",
        "",
        "## Summary",
        "",
        f"- Sources: {', '.join(args.source)}",
        f"- Discovered accounts: {len(accounts)}",
        f"- Research queue: {len(queue)}",
        f"- Minimum discovery score: {args.min_score}",
        "",
        "## Next Command",
        "",
        "```powershell",
        f"python ops\\prospecting\\build_agency_pipeline.py --no-search --input-csv data\\prospects\\agency_research_queue_{TODAY}.csv --max-sites 30 --max-pages-per-site 2 --request-delay 0.4 --min-score 70",
        "```",
        "",
        "## Notes",
        "",
        "- Discovery does not send outreach.",
        "- API keys are read from env vars or CLI flags and are never written to output files.",
        "- OpenClaw should be used after this step only for the best enrichment candidates.",
        "- Manually verify contacts before outreach.",
        "",
        "## Top Candidates",
        "",
    ]
    for index, account in enumerate(queue[:20], start=1):
        lines.extend(
            [
                f"### {index}. {account.company_name}",
                "",
                f"- Website: {account.website}",
                f"- Segment: {account.segment}",
                f"- Country: {account.country or 'unknown'}",
                f"- Discovery score: {account.discovery_score}",
                f"- Source: {account.best_source_type} / {account.best_source_query}",
                f"- Evidence: {account.best_snippet}",
                f"- Reasons: {'; '.join(account.discovery_reasons)}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def expand_sources(args: argparse.Namespace) -> list[str]:
    sources = args.source or ["seed"]
    if "all" not in sources:
        return sources
    expanded = ["seed", "list-page", "duckduckgo"]
    if args.brave_api_key:
        expanded.append("brave")
    if args.serpapi_api_key:
        expanded.append("serpapi")
    if args.google_cse_api_key and args.google_cse_id:
        expanded.append("google-cse")
    if args.serper_api_key:
        expanded.append("serper")
    if args.tavily_api_key:
        expanded.append("tavily")
    if args.exa_api_key:
        expanded.append("exa")
    return expanded


def validate_sources(args: argparse.Namespace) -> None:
    missing: list[str] = []
    if "brave" in args.source and not args.brave_api_key:
        missing.append("brave needs APERTURE_BRAVE_SEARCH_API_KEY or --brave-api-key")
    if "serpapi" in args.source and not args.serpapi_api_key:
        missing.append("serpapi needs APERTURE_SERPAPI_API_KEY or --serpapi-api-key")
    if "google-cse" in args.source and (not args.google_cse_api_key or not args.google_cse_id):
        missing.append("google-cse needs APERTURE_GOOGLE_CSE_API_KEY and APERTURE_GOOGLE_CSE_ID")
    if "serper" in args.source and not args.serper_api_key:
        missing.append("serper needs APERTURE_SERPER_API_KEY or --serper-api-key")
    if "tavily" in args.source and not args.tavily_api_key:
        missing.append("tavily needs APERTURE_TAVILY_API_KEY or --tavily-api-key")
    if "exa" in args.source and not args.exa_api_key:
        missing.append("exa needs APERTURE_EXA_API_KEY or --exa-api-key")
    if missing:
        raise SystemExit("\n".join(missing))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover B2B agency accounts from APIs, web search, seeds, and list pages.")
    parser.add_argument(
        "--source",
        action="append",
        choices=("all", "seed", "list-page", "brave", "serpapi", "google-cse", "serper", "tavily", "exa", "duckduckgo"),
    )
    parser.add_argument("--segment", action="append", choices=tuple(SEGMENTS.keys()), default=[])
    parser.add_argument("--country", action="append", default=[])
    parser.add_argument("--seed-file", type=Path, default=None)
    parser.add_argument("--list-file", type=Path, default=None)
    parser.add_argument("--max-list-pages", type=int, default=5)
    parser.add_argument("--max-queries", type=int, default=40)
    parser.add_argument("--max-results-per-query", type=int, default=10)
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument("--min-score", type=int, default=45)
    parser.add_argument("--request-delay", type=float, default=0.8)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--brave-api-key", default=env_first("APERTURE_BRAVE_SEARCH_API_KEY", "BRAVE_SEARCH_API_KEY"))
    parser.add_argument("--serpapi-api-key", default=env_first("APERTURE_SERPAPI_API_KEY", "SERPAPI_API_KEY"))
    parser.add_argument("--google-cse-api-key", default=env_first("APERTURE_GOOGLE_CSE_API_KEY", "GOOGLE_CSE_API_KEY"))
    parser.add_argument("--google-cse-id", default=env_first("APERTURE_GOOGLE_CSE_ID", "GOOGLE_CSE_ID"))
    parser.add_argument("--serper-api-key", default=env_first("APERTURE_SERPER_API_KEY", "SERPER_API_KEY"))
    parser.add_argument("--tavily-api-key", default=env_first("APERTURE_TAVILY_API_KEY", "TAVILY_API_KEY"))
    parser.add_argument("--exa-api-key", default=env_first("APERTURE_EXA_API_KEY", "EXA_API_KEY"))
    return parser.parse_args()


def main() -> None:
    load_env_file(REPO_ROOT / ".env")
    args = parse_args()
    args.source = expand_sources(args)
    args.segment = args.segment or ["b2b-lead-gen", "paid-media-seo", "revops-hubspot"]
    args.country = args.country or list(TARGET_COUNTRIES)
    seed_file = args.seed_file or (SEED_URLS_FILE if SEED_URLS_FILE.exists() else SEED_URLS_EXAMPLE_FILE)
    list_file = args.list_file or (LIST_SOURCES_FILE if LIST_SOURCES_FILE.exists() else LIST_SOURCES_EXAMPLE_FILE)
    queries = build_queries(args.segment, args.country, args.max_queries)

    if args.dry_run:
        print("Agency discovery dry run")
        print(f"Sources: {', '.join(args.source)}")
        print(f"Segments: {', '.join(args.segment)}")
        print(f"Countries: {', '.join(args.country)}")
        print(f"Queries: {len(queries)}")
        print(f"Seed file: {seed_file}")
        print(f"List file: {list_file}")
        print(f"Brave key configured: {bool(args.brave_api_key)}")
        print(f"SerpAPI key configured: {bool(args.serpapi_api_key)}")
        print(f"Google CSE configured: {bool(args.google_cse_api_key and args.google_cse_id)}")
        print(f"Serper key configured: {bool(args.serper_api_key)}")
        print(f"Tavily key configured: {bool(args.tavily_api_key)}")
        print(f"Exa key configured: {bool(args.exa_api_key)}")
        return

    validate_sources(args)

    hits: list[SearchHit] = []
    if "seed" in args.source:
        hits.extend(discover_from_seed(seed_file, args.max_results))
    if "list-page" in args.source:
        hits.extend(discover_from_list_pages(list_file, args))

    for source_type in ("brave", "serpapi", "google-cse", "serper", "tavily", "exa", "duckduckgo"):
        if source_type in args.source:
            remaining = max(0, args.max_results - len(hits)) if args.max_results else 0
            if args.max_results and remaining <= 0:
                break
            hits.extend(discover_from_search(args, source_type, queries))
            if args.max_results and len(hits) >= args.max_results:
                hits = hits[: args.max_results]
                break

    accounts = collapse_hits(hits)
    queue = [account for account in accounts if account.discovery_score >= args.min_score]

    raw_csv = OUTPUT_DIR / f"agency_discovery_raw_{TODAY}.csv"
    accounts_csv = OUTPUT_DIR / f"agency_accounts_discovered_{TODAY}.csv"
    queue_csv = OUTPUT_DIR / f"agency_research_queue_{TODAY}.csv"
    seed_out = OUTPUT_DIR / f"agency_discovered_seed_urls_{TODAY}.txt"
    runbook = OUTPUT_DIR / f"agency_discovery_runbook_{TODAY}.md"

    write_csv(raw_csv, RAW_FIELDS, [raw_row(hit) for hit in hits])
    write_csv(accounts_csv, ACCOUNT_FIELDS, [account_row(account) for account in accounts])
    write_csv(queue_csv, QUEUE_FIELDS, [queue_row(account) for account in queue])
    write_seed_file(seed_out, queue)
    write_runbook(runbook, args, accounts, queue)

    print(f"\nRaw hits: {len(hits)}")
    print(f"Discovered accounts: {len(accounts)}")
    print(f"Research queue: {len(queue)}")
    print(f"Raw CSV: {raw_csv}")
    print(f"Accounts CSV: {accounts_csv}")
    print(f"Research queue CSV: {queue_csv}")
    print(f"Seed URLs: {seed_out}")
    print(f"Runbook: {runbook}")


if __name__ == "__main__":
    main()
