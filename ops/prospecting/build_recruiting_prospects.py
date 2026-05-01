from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "data" / "prospects"
TODAY = date.today().isoformat()
CSV_OUT = OUTPUT_DIR / f"recruiting_prospects_{TODAY}.csv"
XLSX_OUT = OUTPUT_DIR / f"recruiting_prospects_{TODAY}.xlsx"
SEED_URLS_FILE = SCRIPT_DIR / "recruiting_seed_urls.txt"
SEED_URLS_EXAMPLE_FILE = SCRIPT_DIR / "recruiting_seed_urls.example.txt"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

SEARCH_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS_PER_QUERY = 8
MAX_PAGES_PER_SITE = 4
REQUEST_DELAY_SECONDS = 1.2

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}")

DIRECTORY_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "indeed.com",
    "glassdoor.com",
    "reed.co.uk",
    "yelp.com",
    "clutch.co",
    "sortlist.com",
    "designrush.com",
    "upcity.com",
    "agencyspotter.com",
    "duckduckgo.com",
    "bing.com",
    "google.com",
}

BAD_EMAIL_PARTS = {
    "example",
    "sentry",
    "wixpress",
    "wordpress",
    "domain",
    "godaddy",
    "privacy",
    "noreply",
    "no-reply",
}

SEARCH_QUERIES = [
    '"healthcare staffing agency" "contact" "United States"',
    '"healthcare recruitment agency" "contact" "United States"',
    '"tech recruitment agency" "contact" "United States"',
    '"engineering staffing agency" "contact" "United States"',
    '"finance recruitment agency" "contact" "United States"',
    '"sales recruitment agency" "contact" "United States"',
    '"executive search firm" "contact" "United States"',
    '"healthcare recruitment agency" "contact" "United Kingdom"',
    '"tech recruitment agency" "contact" "United Kingdom"',
    '"engineering recruitment agency" "contact" "United Kingdom"',
    '"finance recruitment agency" "contact" "United Kingdom"',
    '"executive search firm" "contact" "United Kingdom"',
    '"healthcare recruitment agency" "contact" "Australia"',
    '"tech recruitment agency" "contact" "Australia"',
    '"engineering recruitment agency" "contact" "Australia"',
    '"executive search firm" "contact" "Australia"',
]

COUNTRY_HINTS = {
    "United States": ["united states", "usa", "u.s.", "new york", "california", "texas", "florida", "+1"],
    "United Kingdom": ["united kingdom", "uk", "london", "manchester", "birmingham", "+44"],
    "Australia": ["australia", "sydney", "melbourne", "brisbane", "+61"],
}

NICHE_HINTS = {
    "Healthcare": ["healthcare", "medical", "nursing", "nurse", "clinical", "physician", "care"],
    "Technology": ["technology", "software", "developer", "it recruitment", "cybersecurity", "saas", "data"],
    "Engineering": ["engineering", "manufacturing", "construction", "civil", "mechanical", "electrical"],
    "Finance": ["finance", "accounting", "banking", "cpa", "audit", "tax"],
    "Sales": ["sales recruiter", "sales recruitment", "revenue", "account executive", "sdr", "bdr"],
    "Executive Search": ["executive search", "leadership", "c-suite", "board", "retained search"],
}

PAIN_HINTS = {
    "active hiring signal": ["submit resume", "job search", "open jobs", "search jobs", "vacancies"],
    "candidate sourcing workflow": ["candidates", "talent pool", "screening", "shortlist", "submit candidates"],
    "client acquisition workflow": ["employers", "clients", "hire talent", "staffing solutions", "recruitment solutions"],
    "manual contact workflow": ["email us", "contact us", "book a call", "request talent", "upload cv"],
}

OUTPUT_FIELDS = [
    "company_name",
    "website",
    "country",
    "niche",
    "public_email",
    "phone",
    "linkedin_url",
    "source_query",
    "source_url",
    "pain_signal",
    "personalized_angle",
    "score",
    "status",
    "notes",
]


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    query: str


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def root_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_excluded_url(url: str) -> bool:
    host = root_domain(url)
    return any(host == domain or host.endswith(f".{domain}") for domain in DIRECTORY_DOMAINS)


def normalize_result_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith("duckduckgo.com") and parsed.path.startswith("/y.js"):
        return ""
    if host.endswith("bing.com") and "/aclick" in parsed.path:
        return ""
    if "duckduckgo.com/l/" not in url:
        return url
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url


def search(query: str) -> list[SearchResult]:
    response = requests.post(
        SEARCH_URL,
        data={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for node in soup.select(".result"):
        link = node.select_one("a.result__a")
        if not link:
            continue
        url = normalize_result_url(link.get("href", "").strip())
        if not url.startswith("http") or is_excluded_url(url):
            continue
        snippet_node = node.select_one(".result__snippet")
        results.append(
            SearchResult(
                title=clean_text(link.get_text(" ", strip=True)),
                url=url,
                snippet=clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else ""),
                query=query,
            )
        )
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break
    return results


def fetch(url: str) -> tuple[str, str]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25, allow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return str(response.url), ""
    return str(response.url), response.text


def find_internal_pages(base_url: str, soup: BeautifulSoup) -> list[str]:
    wanted = ("contact", "about", "team", "employer", "client", "hire", "jobs")
    pages: list[str] = []
    base_host = root_domain(base_url)
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        text = anchor.get_text(" ", strip=True).lower()
        if not href:
            continue
        lowered = href.lower()
        if not any(term in lowered or term in text for term in wanted):
            continue
        absolute = urljoin(base_url, href)
        if root_domain(absolute) != base_host:
            continue
        clean = absolute.split("#")[0]
        if clean not in pages:
            pages.append(clean)
        if len(pages) >= MAX_PAGES_PER_SITE - 1:
            break
    return pages


def extract_public_emails(text: str) -> list[str]:
    emails = []
    for email in EMAIL_RE.findall(text):
        lowered = email.lower()
        if not lowered[0].isalnum():
            continue
        if any(part in lowered for part in BAD_EMAIL_PARTS):
            continue
        if lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")):
            continue
        emails.append(lowered)
    return sorted(set(emails))


def extract_phone(text: str) -> str:
    for match in PHONE_RE.findall(text):
        digits = re.sub(r"\D", "", match)
        if len(digits) >= 10:
            return clean_text(match)
    return ""


def extract_linkedin(soup: BeautifulSoup) -> str:
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        lowered = href.lower()
        if "linkedin.com/company" in lowered or "linkedin.com/in/" in lowered:
            return href
    return ""


def choose_email(emails: list[str], website: str) -> str:
    if not emails:
        return ""
    host = root_domain(website)
    domain_parts = host.split(".")
    likely_domain = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else host
    preferred_prefixes = (
        "info@",
        "contact@",
        "hello@",
        "team@",
        "recruitment@",
        "recruiting@",
        "careers@",
        "jobs@",
        "healthcareteam@",
    )

    def email_score(email: str) -> tuple[int, str]:
        score = 0
        if email.endswith(likely_domain) or email.endswith(host):
            score += 30
        if email.startswith(preferred_prefixes):
            score += 20
        if any(bad in email for bad in ("design", "press", "media", "support", "webmaster")):
            score -= 10
        return (-score, email)

    return sorted(set(emails), key=email_score)[0]


def infer_country(text: str, query: str) -> str:
    lowered = f"{query} {text}".lower()
    for country, hints in COUNTRY_HINTS.items():
        if any(hint in lowered for hint in hints):
            return country
    return ""


def infer_country_from_url(url: str) -> str:
    host = root_domain(url)
    if host.endswith(".com.au") or host.endswith(".au"):
        return "Australia"
    if host.endswith(".co.uk") or host.endswith(".uk"):
        return "United Kingdom"
    return ""


def infer_niche(text: str, query: str) -> str:
    lowered = f"{query} {text}".lower()
    matches = []
    for niche, hints in NICHE_HINTS.items():
        if any(hint in lowered for hint in hints):
            matches.append(niche)
    return ", ".join(matches[:2]) if matches else "Recruiting/Staffing"


def infer_pain_signal(text: str) -> str:
    lowered = text.lower()
    signals = []
    for signal, hints in PAIN_HINTS.items():
        if any(hint in lowered for hint in hints):
            signals.append(signal)
    return "; ".join(signals[:3]) if signals else "repetitive sourcing/outreach/admin workflow likely"


def company_name_from_soup(soup: BeautifulSoup, fallback: str) -> str:
    og_site = soup.select_one('meta[property="og:site_name"]')
    if og_site and og_site.get("content"):
        return clean_text(og_site["content"])
    if soup.title:
        title = soup.title.get_text(" ", strip=True)
        title = re.split(r"\s+[|–-]\s+", title)[0]
        if title:
            return clean_text(title)
    return clean_text(fallback)


def build_angle(company: str, niche: str, pain_signal: str) -> str:
    return (
        f"{company} appears to run {niche.lower()} recruiting workflows where AI can reduce manual "
        f"sourcing, outreach personalization, follow-ups, CRM updates, and candidate/client summaries."
    )


def score_row(row: dict[str, str]) -> int:
    score = 0
    if row["country"] in {"United States", "United Kingdom", "Australia"}:
        score += 20
    if row["niche"] and row["niche"] != "Recruiting/Staffing":
        score += 20
    if row["public_email"]:
        score += 15
    if row["linkedin_url"]:
        score += 10
    if "active hiring signal" in row["pain_signal"]:
        score += 15
    if "client acquisition workflow" in row["pain_signal"]:
        score += 10
    if "candidate sourcing workflow" in row["pain_signal"]:
        score += 10
    return score


def analyze_site(result: SearchResult) -> dict[str, str] | None:
    try:
        final_url, html = fetch(result.url)
    except requests.RequestException:
        return None
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    pages = [final_url] + find_internal_pages(final_url, soup)
    all_text_parts = [soup.get_text(" ", strip=True), result.title, result.snippet]
    all_emails: list[str] = []
    phone = ""
    linkedin_url = extract_linkedin(soup)

    for page_url in pages[1:]:
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            _, page_html = fetch(page_url)
        except requests.RequestException:
            continue
        page_soup = BeautifulSoup(page_html, "html.parser")
        page_text = page_soup.get_text(" ", strip=True)
        all_text_parts.append(page_text)
        all_emails.extend(extract_public_emails(page_text))
        phone = phone or extract_phone(page_text)
        linkedin_url = linkedin_url or extract_linkedin(page_soup)

    all_text = clean_text(" ".join(all_text_parts))
    all_emails.extend(extract_public_emails(all_text))
    phone = phone or extract_phone(all_text)
    company = company_name_from_soup(soup, result.title)
    website = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}"
    country = infer_country_from_url(final_url) or infer_country(all_text, result.query)
    niche = infer_niche(all_text, result.query)
    pain_signal = infer_pain_signal(all_text)

    if "recruit" not in all_text.lower() and "staffing" not in all_text.lower() and "search firm" not in all_text.lower():
        return None

    row = {
        "company_name": company,
        "website": website,
        "country": country,
        "niche": niche,
        "public_email": choose_email(all_emails, website),
        "phone": phone,
        "linkedin_url": linkedin_url,
        "source_query": result.query,
        "source_url": result.url,
        "pain_signal": pain_signal,
        "personalized_angle": build_angle(company, niche, pain_signal),
        "score": "0",
        "status": "sourced",
        "notes": result.snippet,
    }
    row["score"] = str(score_row(row))
    return row


def write_csv(rows: list[dict[str, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(rows: list[dict[str, str]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Recruiting Prospects"
    sheet.append(OUTPUT_FIELDS)
    for row in rows:
        sheet.append([row.get(field, "") for field in OUTPUT_FIELDS])
    for column in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(max_length + 2, 12), 60)
    workbook.save(XLSX_OUT)


def main() -> None:
    rows_by_domain: dict[str, dict[str, str]] = {}
    seed_file = SEED_URLS_FILE if SEED_URLS_FILE.exists() else SEED_URLS_EXAMPLE_FILE
    if seed_file.exists():
        for line in seed_file.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            domain = root_domain(url)
            if domain in rows_by_domain or is_excluded_url(url):
                continue
            print(f"Seed analyzing: {domain}")
            row = analyze_site(SearchResult(title=domain, url=url, snippet="", query="manual seed"))
            if row:
                rows_by_domain[root_domain(row["website"])] = row
            time.sleep(REQUEST_DELAY_SECONDS)

    for query in SEARCH_QUERIES:
        print(f"Searching: {query}")
        try:
            results = search(query)
        except requests.RequestException as exc:
            print(f"  search failed: {exc}")
            continue
        for result in results:
            domain = root_domain(result.url)
            if domain in rows_by_domain:
                continue
            print(f"  analyzing: {domain}")
            row = analyze_site(result)
            if row:
                rows_by_domain[root_domain(row["website"])] = row
            time.sleep(REQUEST_DELAY_SECONDS)

    rows = sorted(rows_by_domain.values(), key=lambda item: int(item["score"]), reverse=True)
    write_csv(rows)
    write_xlsx(rows)
    print(f"\nSaved {len(rows)} prospects")
    print(f"CSV:  {CSV_OUT}")
    print(f"XLSX: {XLSX_OUT}")


if __name__ == "__main__":
    main()
