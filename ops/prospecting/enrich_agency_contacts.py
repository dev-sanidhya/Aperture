from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "prospects"
TODAY = date.today().isoformat()

SERPER_SEARCH_URL = "https://google.serper.dev/search"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CONTACT_TEXT_CHARS = 7000
OPENCLAW_TEXT_CHARS = 700

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}")
LINKEDIN_PROFILE_RE = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9%_\-./]+", re.I)

TEXT_REPLACEMENTS = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u2192": "->",
    "â€”": "-",
    "â€“": "-",
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€": '"',
    "â†’": "->",
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
    "donotreply",
}

ROLE_KEYWORDS = {
    "founder": ("founder", "co-founder", "owner", "principal"),
    "ceo": ("ceo", "chief executive", "president"),
    "managing_director": ("managing director", "md"),
    "coo_ops": ("coo", "chief operating", "operations", "head of ops"),
    "client_services": ("client services", "account director", "delivery", "customer success"),
    "revops": ("revops", "revenue operations", "sales operations"),
}

GENERIC_NAME_TERMS = {
    "about",
    "about us",
    "team",
    "leadership",
    "contact",
    "careers",
    "approach",
    "account managers",
    "services",
    "home",
    "company",
}

CONTACT_FIELDS = [
    "company_name",
    "domain",
    "website",
    "contact_name",
    "contact_title",
    "role_fit",
    "linkedin_url",
    "email",
    "phone",
    "source_url",
    "email_source_url",
    "profile_source_url",
    "public_business_contact",
    "confidence",
    "status",
    "evidence",
    "notes",
]

PITCH_FIELDS = [
    "company_name",
    "domain",
    "website",
    "fit_score",
    "agency_type",
    "pain_angle",
    "best_contact_name",
    "best_contact_title",
    "best_contact_linkedin",
    "best_contact_email",
    "contact_confidence",
    "workflow_gap",
    "evidence",
    "assumptions",
    "linkedin_connect",
    "linkedin_followup",
    "cold_email_subject",
    "cold_email_body",
    "followup_1",
    "loom_teardown_plan",
    "call_questions",
    "manual_checks",
    "do_not_claim",
    "pitch_status",
]


@dataclass(slots=True)
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str


def clean_text(value: str) -> str:
    text = value or ""
    for needle, replacement in TEXT_REPLACEMENTS.items():
        text = text.replace(needle, replacement)
    return re.sub(r"\s+", " ", text).strip()


def clean_output_value(value: str) -> str:
    text = clean_text(value)
    return text.encode("ascii", errors="ignore").decode("ascii")


def root_domain(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


def normalize_result_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith("duckduckgo.com") and parsed.path.startswith("/y.js"):
        return ""
    if "duckduckgo.com/l/" not in url:
        return url
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{key: clean_output_value(str(value)) for key, value in row.items()} for row in rows])


def search_serper(query: str, *, api_key: str, count: int, timeout: float) -> list[SearchResult]:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": min(count, 20)}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.post(SERPER_SEARCH_URL, json=payload)
        response.raise_for_status()
    data = response.json()
    return [
        SearchResult(
            query=query,
            title=clean_text(item.get("title", "")),
            url=normalize_url(item.get("link", "")),
            snippet=clean_text(item.get("snippet", "")),
        )
        for item in data.get("organic", [])
        if item.get("link")
    ]


def search_duckduckgo(query: str, *, count: int, timeout: float) -> list[SearchResult]:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.post(DUCKDUCKGO_HTML_URL, data={"q": query})
        response.raise_for_status()
    if response.status_code == 202 or "anomaly" in response.text.lower():
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for node in soup.select(".result"):
        link = node.select_one("a.result__a")
        if not link:
            continue
        url = normalize_result_url(link.get("href", "").strip())
        if not url.startswith("http"):
            continue
        snippet_node = node.select_one(".result__snippet")
        results.append(
            SearchResult(
                query=query,
                title=clean_text(link.get_text(" ", strip=True)),
                url=url,
                snippet=clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else ""),
            )
        )
        if len(results) >= count:
            break
    return results


def search_web(query: str, args: argparse.Namespace) -> list[SearchResult]:
    if args.source == "serper":
        return search_serper(query, api_key=args.serper_api_key, count=args.max_results_per_query, timeout=args.timeout)
    if args.source == "duckduckgo":
        return search_duckduckgo(query, count=args.max_results_per_query, timeout=args.timeout)
    if args.serper_api_key:
        return search_serper(query, api_key=args.serper_api_key, count=args.max_results_per_query, timeout=args.timeout)
    return search_duckduckgo(query, count=args.max_results_per_query, timeout=args.timeout)


def fetch_html(url: str, timeout: float) -> tuple[str, str]:
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(url)
        response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return str(response.url), ""
    return str(response.url), response.text


def internal_contact_pages(website: str, soup: BeautifulSoup, limit: int) -> list[str]:
    wanted = ("contact", "about", "team", "leadership", "people", "company")
    domain = root_domain(website)
    pages: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        text = anchor.get_text(" ", strip=True).lower()
        lowered = href.lower()
        if not any(term in lowered or term in text for term in wanted):
            continue
        absolute = urljoin(website, href).split("#")[0]
        if root_domain(absolute) != domain:
            continue
        if absolute not in pages:
            pages.append(absolute)
        if len(pages) >= limit:
            break
    return pages


def extract_public_emails(text: str) -> list[str]:
    emails: list[str] = []
    for email in EMAIL_RE.findall(text):
        lowered = email.lower()
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


def extract_linkedin_profiles(text: str) -> list[str]:
    profiles: list[str] = []
    for match in LINKEDIN_PROFILE_RE.findall(text):
        cleaned = match.rstrip("/,.")
        if cleaned not in profiles:
            profiles.append(cleaned)
    return profiles


def role_fit_from_text(text: str) -> str:
    lowered = text.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return role
    return ""


def title_from_text(text: str) -> str:
    lowered = text.lower()
    title_patterns = (
        "co-founder",
        "founder",
        "chief executive officer",
        "ceo",
        "president",
        "managing director",
        "chief operating officer",
        "coo",
        "head of operations",
        "head of client services",
        "revenue operations",
    )
    for title in title_patterns:
        if title in lowered:
            return title.title() if title not in {"ceo", "coo"} else title.upper()
    return ""


def likely_name_from_result(result: SearchResult, company_name: str) -> str:
    title = result.title
    if re.search(r"(\bpost\b|#\w+)", title, flags=re.I):
        return ""
    if "linkedin.com/in/" in result.url.lower():
        title = re.split(r"\s+[|-]\s+", title, maxsplit=1)[0]
    title = re.sub(r"\s+\|\s+LinkedIn.*$", "", title, flags=re.I)
    title = re.sub(r"\s+-\s+LinkedIn.*$", "", title, flags=re.I)
    title = re.sub(re.escape(company_name), "", title, flags=re.I)
    for token in company_name.split():
        if len(token) > 3:
            title = re.sub(rf"\s+-\s+{re.escape(token)}.*$", "", title, flags=re.I)
    title = re.sub(r"\b(founder|co-founder|ceo|president|managing director|owner|chief operating officer|coo)\b", "", title, flags=re.I)
    title = re.sub(r"\s+-?\s+at\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+-?\s+at\s+", " ", title, flags=re.I)
    title = re.sub(r"^meet\s+", "", title, flags=re.I)
    title = clean_text(title.strip(" -|,"))
    lowered = title.lower()
    if lowered in GENERIC_NAME_TERMS or any(term == lowered for term in GENERIC_NAME_TERMS):
        return ""
    if any(term in lowered for term in ("about us", "our team", "leadership team", "account managers")):
        return ""
    if 2 <= len(title.split()) <= 4 and len(title) <= 80 and re.search(r"[A-Za-z]{2,}", title):
        return title.title() if title.isupper() else title
    return ""


def contact_confidence(row: dict[str, str]) -> int:
    score = 20
    if row["contact_name"]:
        score += 20
    if row["role_fit"] in {"founder", "ceo", "managing_director", "coo_ops"}:
        score += 25
    elif row["role_fit"]:
        score += 15
    if row["linkedin_url"]:
        score += 20
    if row["email"]:
        score += 10
    if row["source_url"]:
        score += 5
    return min(100, score)


def contact_from_search_result(account: dict[str, str], result: SearchResult) -> dict[str, str] | None:
    if re.search(r"(\bpost\b|#\w+)", result.title, flags=re.I):
        return None
    haystack = f"{result.title} {result.snippet}"
    role_fit = role_fit_from_text(haystack)
    linkedin_profiles = extract_linkedin_profiles(result.url + " " + haystack)
    contact_name = likely_name_from_result(result, account["company_name"])
    if not linkedin_profiles and (not role_fit or not contact_name):
        return None
    contact = {
        "company_name": account["company_name"],
        "domain": account["domain"],
        "website": account["website"],
        "contact_name": contact_name,
        "contact_title": title_from_text(haystack),
        "role_fit": role_fit,
        "linkedin_url": linkedin_profiles[0] if linkedin_profiles else "",
        "email": "",
        "phone": "",
        "source_url": result.url,
        "email_source_url": "",
        "profile_source_url": result.url,
        "public_business_contact": "true",
        "confidence": "0",
        "status": "needs_manual_verification",
        "evidence": clean_text(haystack)[:500],
        "notes": f"Found from query: {result.query}",
    }
    contact["confidence"] = str(contact_confidence(contact))
    return contact


def business_contact_rows(account: dict[str, str], emails: list[str], phone: str, source_url: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for email in emails:
        rows.append(
            {
                "company_name": account["company_name"],
                "domain": account["domain"],
                "website": account["website"],
                "contact_name": "",
                "contact_title": "Business contact",
                "role_fit": "business_contact",
                "linkedin_url": "",
                "email": email,
                "phone": phone,
                "source_url": source_url,
                "email_source_url": source_url,
                "profile_source_url": "",
                "public_business_contact": "true",
                "confidence": "60",
                "status": "needs_manual_verification",
                "evidence": f"Public email found on {source_url}",
                "notes": "Use only if no decision-maker email is found; LinkedIn-first is better for founders.",
            }
        )
    return rows


def dedupe_contacts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("domain", "").lower(),
            row.get("contact_name", "").lower() or row.get("linkedin_url", "").lower(),
            row.get("email", "").lower() if not row.get("contact_name") and not row.get("linkedin_url") else "",
        )
        if key in deduped:
            existing = deduped[key]
            for field in ("contact_title", "role_fit", "linkedin_url", "email", "phone", "email_source_url", "profile_source_url"):
                if not existing.get(field) and row.get(field):
                    existing[field] = row[field]
            if row.get("evidence") and row["evidence"] not in existing.get("evidence", ""):
                existing["evidence"] = clean_text(f"{existing.get('evidence', '')}; {row['evidence']}")[:500]
            if row.get("source_url") and row["source_url"] not in existing.get("source_url", ""):
                existing["source_url"] = clean_text(f"{existing.get('source_url', '')}; {row['source_url']}")[:500]
            existing["confidence"] = str(contact_confidence(existing))
            continue
        if int(row.get("confidence", "0") or 0) >= 40:
            deduped[key] = row
    return sorted(deduped.values(), key=lambda row: int(row.get("confidence", "0") or 0), reverse=True)


def build_contact_queries(account: dict[str, str], max_queries: int) -> list[str]:
    company = account["company_name"]
    domain = account["domain"]
    queries = [
        f'site:{domain} founder CEO team',
        f'site:{domain} leadership OR team OR about',
        f'"{company}" founder LinkedIn',
        f'"{company}" CEO LinkedIn',
        f'"{company}" COO OR "head of operations" LinkedIn',
        f'site:{domain} contact email',
    ]
    return queries[:max_queries]


def collect_website_evidence(account: dict[str, str], args: argparse.Namespace) -> tuple[list[dict[str, str]], str]:
    website = normalize_url(account["website"])
    rows: list[dict[str, str]] = []
    text_parts: list[str] = []
    try:
        final_url, html = fetch_html(website, args.timeout)
    except (httpx.HTTPError, ValueError):
        return rows, ""
    if not html:
        return rows, ""
    soup = BeautifulSoup(html, "html.parser")
    pages = [final_url] + internal_contact_pages(final_url, soup, args.max_contact_pages)
    for page_url in pages:
        page_html = html if page_url == final_url else ""
        if page_url != final_url:
            time.sleep(args.request_delay)
            try:
                _, page_html = fetch_html(page_url, args.timeout)
            except (httpx.HTTPError, ValueError):
                continue
        page_soup = BeautifulSoup(page_html, "html.parser")
        text = clean_text(page_soup.get_text(" ", strip=True))
        text_parts.append(text[:1800])
        emails = extract_public_emails(text)
        phone = extract_phone(text)
        rows.extend(business_contact_rows(account, emails, phone, page_url))
    return rows, clean_text(" ".join(text_parts))[:CONTACT_TEXT_CHARS]


def discover_contacts_for_account(account: dict[str, str], args: argparse.Namespace) -> tuple[list[dict[str, str]], str]:
    contacts, website_evidence = collect_website_evidence(account, args)
    if args.max_contact_queries > 0:
        for query in build_contact_queries(account, args.max_contact_queries):
            print(f"  searching: {query}")
            try:
                results = search_web(query, args)
            except httpx.HTTPError as exc:
                print(f"    search failed: {exc}")
                results = []
            for result in results:
                contact = contact_from_search_result(account, result)
                if contact:
                    contacts.append(contact)
            time.sleep(args.request_delay)
    return dedupe_contacts(contacts), website_evidence


def best_contact(contacts: list[dict[str, str]]) -> dict[str, str]:
    if not contacts:
        return {}
    return sorted(contacts, key=lambda row: int(row.get("confidence", "0") or 0), reverse=True)[0]


def default_pitch_pack(account: dict[str, str], contacts: list[dict[str, str]], website_evidence: str) -> dict[str, str]:
    contact = best_contact(contacts)
    contact_name = contact.get("contact_name", "")
    title = contact.get("contact_title", "")
    opener_target = contact_name or "there"
    workflow_gap = account.get("ai_summary") or account.get("cold_email_opener") or account.get("pain_evidence", "")
    email_gap = workflow_gap
    email_gap = re.sub(rf"^Saw {re.escape(account['company_name'])} appears to do [^.]+\. One workflow that may be worth tightening is ", "", email_gap)
    evidence = account.get("pain_evidence", "") or account.get("notes", "")[:300]
    linkedin_connect = (
        f"Hey {opener_target}, noticed {account['company_name']} works around {account.get('agency_type', 'agency')} workflows. "
        "Open to me sending 2-3 specific AI workflow ideas that may reduce manual ops?"
    )
    linkedin_followup = (
        f"One idea for {account['company_name']}: turn calls/forms/reports into CRM notes, follow-ups, proposals, tasks, "
        "or client-ready insights before the team reviews them. Worth sending a short teardown?"
    )
    cold_email_body = (
        f"Hey {contact_name or 'team'},\n\n"
        f"Saw {account['company_name']} appears to handle {account.get('agency_type', 'agency')} work. "
        f"The workflow gap I would look at first is {email_gap[:220]}.\n\n"
        "I build practical AI workflows for agencies: lead intake, CRM updates, proposals, reporting summaries, and delivery handoffs.\n\n"
        "Open to me sending 2-3 specific automation ideas for your team?"
    )
    return {
        "company_name": account["company_name"],
        "domain": account["domain"],
        "website": account["website"],
        "fit_score": account.get("fit_score", ""),
        "agency_type": account.get("agency_type", ""),
        "pain_angle": account.get("pain_angle", ""),
        "best_contact_name": contact_name,
        "best_contact_title": title,
        "best_contact_linkedin": contact.get("linkedin_url", ""),
        "best_contact_email": contact.get("email", ""),
        "contact_confidence": contact.get("confidence", "0") if contact else "0",
        "workflow_gap": workflow_gap[:500],
        "evidence": clean_text(evidence or website_evidence[:350])[:500],
        "assumptions": "Manual ops pain is inferred from public positioning and service model; verify on call.",
        "linkedin_connect": linkedin_connect[:500],
        "linkedin_followup": linkedin_followup[:700],
        "cold_email_subject": f"Idea for {account['company_name']} ops"[:120],
        "cold_email_body": cold_email_body[:1200],
        "followup_1": (
            f"Quick follow-up - I can make this concrete for {account['company_name']} with a short teardown of one workflow "
            "before suggesting any build."
        )[:700],
        "loom_teardown_plan": (account.get("loom_idea") or "Record a short teardown of one manual workflow and show the before/after draft output.")[:800],
        "call_questions": (
            "Which workflow takes the most manual copy-paste today?; "
            "Where do follow-ups or client updates get delayed?; "
            "What tools do calls, forms, CRM, and reporting currently pass through?"
        ),
        "manual_checks": "Verify best contact, email deliverability, LinkedIn profile, and opt-out footer before outreach.",
        "do_not_claim": "Do not claim proven hours saved, internal tools used, current CRM/reporting stack, or confirmed founder pain.",
        "pitch_status": (
            "needs_manual_review"
            if contact and contact.get("contact_name") and contact.get("role_fit") != "business_contact"
            else "needs_person_contact"
        ),
    }


def parse_json_like_output(raw: str) -> dict[str, object]:
    text = raw.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"items": parsed}
    except json.JSONDecodeError:
        pass
    for line in reversed([line for line in text.splitlines() if line.strip()]):
        try:
            parsed = json.loads(line)
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        except json.JSONDecodeError:
            continue
    return {"raw": text}


def shell_safe_text(value: str) -> str:
    replacements = {"&": " and ", "|": " ", "<": " ", ">": " ", "^": " ", "%": " percent "}
    safe = value
    for needle, replacement in replacements.items():
        safe = safe.replace(needle, replacement)
    return clean_text(safe)


def shell_safe_payload(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): shell_safe_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [shell_safe_payload(item) for item in value]
    if isinstance(value, str):
        return shell_safe_text(value)
    return value


def openclaw_output_payload(response: dict[str, object]) -> dict[str, object]:
    if isinstance(response.get("output"), dict):
        return response["output"]  # type: ignore[return-value]
    payloads = response.get("payloads")
    if isinstance(payloads, list):
        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                return parse_json_like_output(text)
    return response


def compact_contacts_for_openclaw(contacts: list[dict[str, str]]) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for contact in contacts[:4]:
        compact.append(
            {
                "name": contact.get("contact_name", "")[:80],
                "title": contact.get("contact_title", "")[:80],
                "role_fit": contact.get("role_fit", "")[:40],
                "linkedin_url": contact.get("linkedin_url", "")[:160],
                "email": contact.get("email", "")[:120],
                "confidence": contact.get("confidence", ""),
                "evidence": contact.get("evidence", "")[:180],
            }
        )
    return compact


def compact_pitch_for_openclaw(pitch: dict[str, str]) -> dict[str, str]:
    return {
        "workflow_gap": pitch.get("workflow_gap", "")[:220],
        "linkedin_connect": pitch.get("linkedin_connect", "")[:240],
        "cold_email_subject": pitch.get("cold_email_subject", "")[:80],
        "cold_email_body": pitch.get("cold_email_body", "")[:450],
        "loom_teardown_plan": pitch.get("loom_teardown_plan", "")[:240],
    }


def refine_pitch_with_openclaw(
    account: dict[str, str],
    contacts: list[dict[str, str]],
    pitch: dict[str, str],
    website_evidence: str,
    args: argparse.Namespace,
) -> dict[str, str]:
    payload = shell_safe_payload(
        {
            "task": "agency_contact_pitch_pack",
            "instructions": (
                "Use only provided evidence. Return strict JSON with keys: workflow_gap, evidence, assumptions, "
                "best_contact_name, best_contact_title, best_contact_linkedin, best_contact_email, linkedin_connect, "
                "linkedin_followup, cold_email_subject, cold_email_body, followup_1, loom_teardown_plan, "
                "call_questions, manual_checks, do_not_claim, pitch_status. Do not invent contacts or email addresses."
            ),
            "account": {
                "company_name": account.get("company_name", ""),
                "website": account.get("website", ""),
                "domain": account.get("domain", ""),
                "agency_type": account.get("agency_type", ""),
                "fit_score": account.get("fit_score", ""),
                "pain_angle": account.get("pain_angle", ""),
                "pain_evidence": account.get("pain_evidence", ""),
                "cold_email_opener": account.get("cold_email_opener", ""),
                "loom_idea": account.get("loom_idea", ""),
                "ai_summary": account.get("ai_summary", ""),
                "ai_risk": account.get("ai_risk", ""),
                "notes_excerpt": account.get("notes", "")[:OPENCLAW_TEXT_CHARS],
            },
            "contacts": compact_contacts_for_openclaw(contacts),
            "website_evidence_excerpt": website_evidence[:OPENCLAW_TEXT_CHARS],
            "draft_to_improve": compact_pitch_for_openclaw(pitch),
        }
    )
    session_safe_domain = re.sub(r"[^a-zA-Z0-9_-]+", "-", account["domain"])[:80]
    command = [
        args.openclaw_command,
        "agent",
        "--agent",
        args.openclaw_agent,
        "--session-id",
        f"agency-pitch-pack-{TODAY}-{session_safe_domain}",
        "--message",
        json.dumps(payload, ensure_ascii=True),
        "--thinking",
        args.openclaw_thinking,
        "--json",
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.openclaw_timeout,
        )
    except subprocess.TimeoutExpired:
        pitch["manual_checks"] = f"{pitch['manual_checks']} OpenClaw timed out after {args.openclaw_timeout}s."
        return pitch
    if result.returncode != 0:
        pitch["manual_checks"] = f"{pitch['manual_checks']} OpenClaw failed: {clean_text(result.stderr)[:300]}"
        return pitch
    output = openclaw_output_payload(parse_json_like_output(result.stdout))
    if not isinstance(output, dict):
        pitch["manual_checks"] = f"{pitch['manual_checks']} OpenClaw returned non-dict output."
        return pitch
    contact_owned_fields = {
        "best_contact_name",
        "best_contact_title",
        "best_contact_linkedin",
        "best_contact_email",
        "contact_confidence",
        "pitch_status",
    }
    for key in PITCH_FIELDS:
        if key in contact_owned_fields:
            continue
        if key in output and output[key] is not None:
            value = output[key]
            if isinstance(value, list):
                pitch[key] = "; ".join(clean_text(str(item)) for item in value if clean_text(str(item)))
            else:
                pitch[key] = clean_text(str(value))
    return pitch


def write_review(path: Path, contacts: list[dict[str, str]], pitches: list[dict[str, str]], args: argparse.Namespace) -> None:
    top = pitches[: min(12, len(pitches))]
    lines = [
        "# Agency Contact + Pitch Review",
        "",
        f"Generated: {TODAY}",
        "",
        "## Output Files",
        "",
        f"- Contacts CSV: `{OUTPUT_DIR / f'agency_contacts_{TODAY}.csv'}`",
        f"- Pitch pack CSV: `{OUTPUT_DIR / f'agency_pitch_pack_{TODAY}.csv'}`",
        f"- Review Markdown: `{path}`",
        "",
        "## Operating Rules",
        "",
        "- Do not send automatically from these outputs.",
        "- Verify the contact, email source, LinkedIn profile, and opt-out footer before outreach.",
        "- Treat guessed or generic emails as manual-review only.",
        f"- OpenClaw pitch refinement cap for this run: {args.openclaw_top_n}.",
        "",
        "## Summary",
        "",
        f"- Accounts reviewed: {len(pitches)}",
        f"- Contact rows found: {len(contacts)}",
        f"- Pitch rows ready for manual review: {sum(1 for row in pitches if row['pitch_status'] == 'needs_manual_review')}",
        f"- Pitch rows needing person contact: {sum(1 for row in pitches if row['pitch_status'] == 'needs_person_contact')}",
        "",
        "## Top Pitch Packs",
        "",
    ]
    for index, row in enumerate(top, start=1):
        lines.extend(
            [
                f"### {index}. {row['company_name']}",
                "",
                f"- Website: {row['website']}",
                f"- Best contact: {row['best_contact_name'] or 'unknown'} ({row['best_contact_title'] or 'unknown title'})",
                f"- LinkedIn: {row['best_contact_linkedin'] or 'not found'}",
                f"- Email: {row['best_contact_email'] or 'not found'}",
                f"- Workflow gap: {row['workflow_gap']}",
                f"- LinkedIn connect: {row['linkedin_connect']}",
                f"- Email subject: {row['cold_email_subject']}",
                f"- Manual checks: {row['manual_checks']}",
                "",
            ]
        )
    path.write_text("\n".join(clean_output_value(line) for line in lines), encoding="utf-8")


def build_outputs(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    accounts = read_csv(args.input_csv)
    accounts = accounts[: args.max_accounts] if args.max_accounts else accounts
    all_contacts: list[dict[str, str]] = []
    pitch_rows: list[dict[str, str]] = []
    for index, account in enumerate(accounts, start=1):
        if not account.get("website") or not account.get("domain"):
            continue
        print(f"[{index}/{len(accounts)}] Contact discovery: {account['domain']}")
        contacts, website_evidence = discover_contacts_for_account(account, args)
        all_contacts.extend(contacts)
        pitch = default_pitch_pack(account, contacts, website_evidence)
        if args.openclaw_top_n > 0 and len(pitch_rows) < args.openclaw_top_n:
            print(f"  OpenClaw pitch refining: {account['domain']}")
            pitch = refine_pitch_with_openclaw(account, contacts, pitch, website_evidence, args)
        pitch_rows.append(pitch)
        time.sleep(args.request_delay)
    all_contacts = dedupe_contacts(all_contacts)
    return all_contacts, pitch_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find agency contacts and produce outreach pitch packs.")
    parser.add_argument("--input-csv", type=Path, default=OUTPUT_DIR / f"agency_outreach_approval_{TODAY}.csv")
    parser.add_argument("--source", choices=("auto", "serper", "duckduckgo"), default="auto")
    parser.add_argument("--max-accounts", type=int, default=10)
    parser.add_argument("--max-contact-queries", type=int, default=4)
    parser.add_argument("--max-results-per-query", type=int, default=5)
    parser.add_argument("--max-contact-pages", type=int, default=4)
    parser.add_argument("--request-delay", type=float, default=0.8)
    parser.add_argument("--timeout", type=float, default=25)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--serper-api-key", default=env_first("APERTURE_SERPER_API_KEY", "SERPER_API_KEY"))
    parser.add_argument("--openclaw-top-n", type=int, default=0)
    parser.add_argument("--openclaw-command", default="openclaw")
    parser.add_argument("--openclaw-agent", default="draft-email-copilot")
    parser.add_argument("--openclaw-thinking", default="low", choices=("low", "medium", "high"))
    parser.add_argument("--openclaw-timeout", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    load_env_file(REPO_ROOT / ".env")
    args = parse_args()
    if args.dry_run:
        print("Agency contact enrichment dry run")
        print(f"Input CSV: {args.input_csv}")
        print(f"Source: {args.source}")
        print(f"Serper configured: {bool(args.serper_api_key)}")
        print(f"Max accounts: {args.max_accounts}")
        print(f"Contact queries/account: {args.max_contact_queries}")
        print(f"OpenClaw top N: {args.openclaw_top_n}")
        return
    contacts, pitches = build_outputs(args)
    contacts_csv = OUTPUT_DIR / f"agency_contacts_{TODAY}.csv"
    pitch_csv = OUTPUT_DIR / f"agency_pitch_pack_{TODAY}.csv"
    review_md = OUTPUT_DIR / f"agency_contact_pitch_review_{TODAY}.md"
    write_csv(contacts_csv, CONTACT_FIELDS, contacts)
    write_csv(pitch_csv, PITCH_FIELDS, pitches)
    write_review(review_md, contacts, pitches, args)
    print(f"\nAccounts reviewed: {len(pitches)}")
    print(f"Contact rows: {len(contacts)}")
    print(f"Contacts CSV: {contacts_csv}")
    print(f"Pitch pack CSV: {pitch_csv}")
    print(f"Review Markdown: {review_md}")


if __name__ == "__main__":
    main()
