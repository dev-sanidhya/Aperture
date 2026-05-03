from __future__ import annotations

import argparse
import csv
import json
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
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "data" / "prospects"
TODAY = date.today().isoformat()

SEED_URLS_FILE = SCRIPT_DIR / "agency_seed_urls.txt"
SEED_URLS_EXAMPLE_FILE = SCRIPT_DIR / "agency_seed_urls.example.txt"
SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TARGET_COUNTRIES = {"United States", "United Kingdom", "Canada", "Australia"}
MAX_TEXT_CHARS = 12000
OPENCLAW_TEXT_CHARS = 1800

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}")

DIRECTORY_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
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
    "B2B lead generation agency case studies United States",
    "B2B lead generation agency case studies United Kingdom",
    "B2B SaaS growth agency case studies",
    "paid media agency B2B SaaS case studies",
    "PPC agency B2B case studies",
    "SEO agency B2B SaaS case studies",
    "HubSpot partner agency growth case studies",
    "RevOps agency HubSpot case studies",
    "demand generation agency B2B case studies",
    "appointment setting agency B2B case studies",
    "technology recruitment agency clients United States",
    "technology staffing agency clients United Kingdom",
    "executive search firm technology clients",
]

COUNTRY_HINTS = {
    "United States": ["united states", "usa", "u.s.", "new york", "california", "texas", "florida", "+1"],
    "United Kingdom": ["united kingdom", "uk", "london", "manchester", "birmingham", "+44"],
    "Canada": ["canada", "toronto", "vancouver", "ontario", "british columbia", "+1"],
    "Australia": ["australia", "sydney", "melbourne", "brisbane", "+61"],
}

AGENCY_TYPE_HINTS = {
    "B2B Lead Gen / Growth": [
        "b2b lead generation",
        "appointment setting",
        "demand generation",
        "pipeline generation",
        "outbound",
        "sdr",
        "sales development",
        "growth agency",
    ],
    "Paid Media / SEO": [
        "paid media",
        "ppc",
        "google ads",
        "meta ads",
        "linkedin ads",
        "seo",
        "search engine optimization",
        "performance marketing",
    ],
    "HubSpot / RevOps": [
        "hubspot",
        "revops",
        "revenue operations",
        "salesforce",
        "crm implementation",
        "marketing automation",
    ],
    "Recruiting / Staffing": [
        "recruiting agency",
        "recruitment agency",
        "staffing agency",
        "executive search",
        "candidate",
        "talent acquisition",
    ],
    "Product / Dev Agency": [
        "software development agency",
        "web development agency",
        "product studio",
        "app development",
        "design and development",
    ],
    "Marketing / Creative Agency": [
        "marketing agency",
        "creative agency",
        "content marketing",
        "brand strategy",
        "social media agency",
    ],
}

B2B_HINTS = [
    "b2b",
    "saas",
    "software companies",
    "technology companies",
    "founders",
    "revenue teams",
    "sales teams",
    "professional services",
    "startups",
]

CASE_STUDY_HINTS = ["case study", "case studies", "results", "client results", "success story", "portfolio"]

PAIN_ANGLE_HINTS = {
    "call_to_proposal": [
        "discovery call",
        "strategy call",
        "consultation",
        "proposal",
        "sales call",
        "brief",
        "audit",
    ],
    "client_reporting_insights": [
        "reporting",
        "dashboard",
        "analytics",
        "monthly report",
        "performance report",
        "insights",
        "google ads",
        "meta ads",
        "seo",
    ],
    "lead_intake_crm_followup": [
        "lead generation",
        "appointment setting",
        "outbound",
        "inbound",
        "crm",
        "hubspot",
        "salesforce",
        "pipeline",
        "follow-up",
    ],
    "delivery_handoff_ops": [
        "client onboarding",
        "account management",
        "project management",
        "workflow",
        "implementation",
        "delivery",
    ],
    "recruiting_ops": [
        "candidate",
        "shortlist",
        "sourcing",
        "screening",
        "ats",
        "resume",
        "cv",
        "job order",
    ],
}

OUTPUT_FIELDS = [
    "company_name",
    "website",
    "domain",
    "country",
    "agency_type",
    "employee_count",
    "public_email",
    "phone",
    "linkedin_url",
    "source_type",
    "source_query",
    "source_url",
    "b2b_signal",
    "pain_angle",
    "pain_evidence",
    "fit_score",
    "confidence",
    "status",
    "recommended_contact_titles",
    "cold_email_opener",
    "loom_idea",
    "ai_enriched",
    "ai_summary",
    "ai_risk",
    "notes",
]


@dataclass(slots=True)
class Candidate:
    title: str
    url: str
    snippet: str
    source_type: str
    source_query: str
    source_url: str = ""


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


def search(query: str, max_results: int) -> list[Candidate]:
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = client.post(SEARCH_URL, data={"q": query})
        response.raise_for_status()
    if response.status_code == 202 or "anomaly" in response.text.lower():
        print("  search returned a throttle/anomaly page; continuing with other sources")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[Candidate] = []
    for node in soup.select(".result"):
        link = node.select_one("a.result__a")
        if not link:
            continue
        url = normalize_result_url(link.get("href", "").strip())
        if not url.startswith("http") or is_excluded_url(url):
            continue
        snippet_node = node.select_one(".result__snippet")
        results.append(
            Candidate(
                title=clean_text(link.get_text(" ", strip=True)),
                url=url,
                snippet=clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else ""),
                source_type="search",
                source_query=query,
            )
        )
        if len(results) >= max_results:
            break
    return results


def fetch(url: str) -> tuple[str, str]:
    with httpx.Client(timeout=25, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(url)
        response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return str(response.url), ""
    return str(response.url), response.text


def load_seed_candidates(seed_file: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    if not seed_file.exists():
        return candidates
    for line in seed_file.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#") or is_excluded_url(url):
            continue
        candidates.append(
            Candidate(
                title=root_domain(url),
                url=url,
                snippet="manual seed",
                source_type="seed",
                source_query="manual seed",
            )
        )
    return candidates


def first_present(row: dict[str, str], names: tuple[str, ...]) -> str:
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for name in names:
        value = clean_text(normalized.get(name, ""))
        if value:
            return value
    return ""


def load_csv_candidates(path: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            website = first_present(row, ("website", "domain", "company website", "company_website", "url"))
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            if not website or is_excluded_url(website):
                continue
            company = first_present(row, ("company_name", "company", "name", "account name", "organization"))
            notes = first_present(row, ("description", "services", "industry", "notes"))
            source_query = first_present(row, ("source_query", "query", "segment", "campaign"))
            source_url = first_present(row, ("source_url", "best_source_url", "url_source"))
            candidates.append(
                Candidate(
                    title=company or root_domain(website),
                    url=website,
                    snippet=notes,
                    source_type="csv",
                    source_query=source_query or str(path.name),
                    source_url=source_url,
                )
            )
    return candidates


def find_internal_pages(base_url: str, soup: BeautifulSoup, max_pages: int) -> list[str]:
    wanted = (
        "contact",
        "about",
        "services",
        "work",
        "case",
        "results",
        "clients",
        "report",
        "insights",
        "hubspot",
        "growth",
    )
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
        if len(pages) >= max_pages - 1:
            break
    return pages


def extract_public_emails(text: str) -> list[str]:
    emails = []
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
    preferred_prefixes = ("hello@", "contact@", "info@", "team@", "sales@", "growth@", "newbusiness@")

    def email_score(email: str) -> tuple[int, str]:
        score = 0
        if email.endswith(likely_domain) or email.endswith(host):
            score += 30
        if email.startswith(preferred_prefixes):
            score += 20
        if any(bad in email for bad in ("support", "careers", "jobs", "press", "media", "billing")):
            score -= 10
        return (-score, email)

    return sorted(set(emails), key=email_score)[0]


def shorten_company_name(value: str) -> str:
    name = clean_text(value)
    for separator in (" | ", " - ", " / "):
        if separator in name:
            name = name.split(separator, 1)[0]
    return clean_text(name)


def company_name_from_soup(soup: BeautifulSoup, fallback: str) -> str:
    og_site = soup.select_one('meta[property="og:site_name"]')
    if og_site and og_site.get("content"):
        return shorten_company_name(og_site["content"])
    if soup.title:
        title = soup.title.get_text(" ", strip=True)
        title = re.split(r"\s+[|-]\s+", title)[0]
        if title:
            return shorten_company_name(title)
    return shorten_company_name(fallback)


def infer_country(text: str, source_query: str, url: str) -> str:
    host = root_domain(url)
    if host.endswith(".com.au") or host.endswith(".au"):
        return "Australia"
    if host.endswith(".co.uk") or host.endswith(".uk"):
        return "United Kingdom"
    lowered = f"{source_query} {text}".lower()
    for country, hints in COUNTRY_HINTS.items():
        if any(hint in lowered for hint in hints):
            return country
    return ""


def infer_agency_type(text: str) -> str:
    lowered = text.lower()
    matches: list[tuple[int, str]] = []
    for agency_type, hints in AGENCY_TYPE_HINTS.items():
        count = sum(1 for hint in hints if hint in lowered)
        if count:
            matches.append((count, agency_type))
    if not matches:
        if "agency" in lowered or "we help" in lowered:
            return "Marketing / Creative Agency"
        return "Unknown"
    return sorted(matches, reverse=True)[0][1]


def infer_b2b_signal(text: str) -> str:
    lowered = text.lower()
    matches = [hint for hint in B2B_HINTS if hint in lowered]
    return "; ".join(matches[:4])


def infer_pain_angle(text: str, agency_type: str) -> tuple[str, str]:
    lowered = text.lower()
    matches: list[tuple[int, str, list[str]]] = []
    for angle, hints in PAIN_ANGLE_HINTS.items():
        hit_hints = [hint for hint in hints if hint in lowered]
        if hit_hints:
            matches.append((len(hit_hints), angle, hit_hints))
    if not matches:
        if agency_type == "Recruiting / Staffing":
            return "recruiting_ops", "agency type implies candidate/client workflow"
        return "call_to_proposal", "agency model implies sales calls, follow-ups, proposals, and handoffs"
    _, angle, hit_hints = sorted(matches, reverse=True)[0]
    return angle, "; ".join(hit_hints[:5])


def parse_employee_count(value: str) -> int | None:
    if not value:
        return None
    numbers = [int(num.replace(",", "")) for num in re.findall(r"\d[\d,]*", value)]
    if not numbers:
        return None
    return max(numbers)


def recommended_titles(agency_type: str) -> str:
    if agency_type == "Recruiting / Staffing":
        return "Founder; CEO; Managing Director; Head of Operations; Head of Recruitment"
    if agency_type == "HubSpot / RevOps":
        return "Founder; CEO; COO; Head of RevOps; Operations Lead"
    return "Founder; CEO; COO; Head of Client Services; Operations Lead"


def build_opener(company: str, agency_type: str, pain_angle: str) -> str:
    angle_copy = {
        "call_to_proposal": "turning sales/client calls into CRM notes, follow-ups, proposal outlines, and internal tasks",
        "client_reporting_insights": "turning campaign/reporting data into client-ready insights and account-manager drafts",
        "lead_intake_crm_followup": "qualifying leads, enriching accounts, updating CRM, and drafting follow-ups",
        "delivery_handoff_ops": "turning client intake into project briefs, tasks, owners, and handoff updates",
        "recruiting_ops": "turning candidate/client notes into shortlists, outreach, follow-ups, and ATS updates",
    }
    return (
        f"Saw {company} appears to do {agency_type} work. One workflow that may be worth tightening is "
        f"{angle_copy.get(pain_angle, angle_copy['call_to_proposal'])}."
    )


def build_loom_idea(agency_type: str, pain_angle: str) -> str:
    if pain_angle == "client_reporting_insights":
        return "Record a 3-minute teardown showing how their reporting workflow could produce insights, anomalies, and next-step drafts before account-manager review."
    if pain_angle == "lead_intake_crm_followup":
        return "Record a 3-minute teardown showing lead form/email intake routed into enrichment, fit scoring, CRM updates, and follow-up drafts."
    if pain_angle == "delivery_handoff_ops":
        return "Record a 3-minute teardown showing client intake converted into a project brief, task list, owners, and a Slack/client-ready update."
    if pain_angle == "recruiting_ops" or agency_type == "Recruiting / Staffing":
        return "Record a 3-minute teardown showing job/candidate notes converted into candidate summaries, outreach drafts, follow-ups, and ATS updates."
    return "Record a 3-minute teardown showing a sales call transcript converted into CRM notes, follow-up email, proposal outline, and internal tasks."


def score_row(row: dict[str, str]) -> tuple[int, float]:
    score = 0
    if row["agency_type"] != "Unknown":
        score += 25
    if row["b2b_signal"]:
        score += 15
    if row["country"] in TARGET_COUNTRIES:
        score += 10
    if row["public_email"]:
        score += 10
    if row["linkedin_url"]:
        score += 5
    if row["pain_evidence"]:
        score += 15
    if any(hint in row["notes"].lower() for hint in CASE_STUDY_HINTS):
        score += 10

    employee_count = parse_employee_count(row.get("employee_count", ""))
    if employee_count is not None:
        if 10 <= employee_count <= 100:
            score += 15
        elif 2 <= employee_count < 10:
            score += 5
        elif 100 < employee_count <= 250:
            score += 5
        elif employee_count > 250:
            score -= 10

    lowered_notes = row["notes"].lower()
    if "restaurant" in lowered_notes or "dentist" in lowered_notes or "real estate agent" in lowered_notes:
        score -= 15
    if row["agency_type"] == "Unknown":
        score -= 20

    score = max(0, min(score, 100))
    confidence = round(min(0.95, 0.35 + score / 150), 2)
    return score, confidence


def analyze_site(candidate: Candidate, max_pages: int, request_delay: float) -> dict[str, str] | None:
    try:
        final_url, html = fetch(candidate.url)
    except (httpx.HTTPError, ValueError):
        return None
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    website = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}"
    pages = [final_url] + find_internal_pages(final_url, soup, max_pages)
    text_parts = [soup.get_text(" ", strip=True), candidate.title, candidate.snippet]
    emails = extract_public_emails(text_parts[0])
    phone = extract_phone(text_parts[0])
    linkedin_url = extract_linkedin(soup)

    for page_url in pages[1:]:
        time.sleep(request_delay)
        try:
            _, page_html = fetch(page_url)
        except (httpx.HTTPError, ValueError):
            continue
        page_soup = BeautifulSoup(page_html, "html.parser")
        page_text = page_soup.get_text(" ", strip=True)
        text_parts.append(page_text)
        emails.extend(extract_public_emails(page_text))
        phone = phone or extract_phone(page_text)
        linkedin_url = linkedin_url or extract_linkedin(page_soup)

    site_text = clean_text(" ".join(text_parts))[:MAX_TEXT_CHARS]
    agency_type = infer_agency_type(site_text)
    if agency_type == "Unknown":
        return None

    company = company_name_from_soup(soup, candidate.title)
    country = infer_country(site_text, candidate.source_query, final_url)
    b2b_signal = infer_b2b_signal(site_text)
    pain_angle, pain_evidence = infer_pain_angle(site_text, agency_type)
    row = {
        "company_name": company,
        "website": website,
        "domain": root_domain(website),
        "country": country,
        "agency_type": agency_type,
        "employee_count": "",
        "public_email": choose_email(emails, website),
        "phone": phone,
        "linkedin_url": linkedin_url,
        "source_type": candidate.source_type,
        "source_query": candidate.source_query,
        "source_url": candidate.source_url or candidate.url,
        "b2b_signal": b2b_signal,
        "pain_angle": pain_angle,
        "pain_evidence": pain_evidence,
        "fit_score": "0",
        "confidence": "0",
        "status": "researched",
        "recommended_contact_titles": recommended_titles(agency_type),
        "cold_email_opener": "",
        "loom_idea": "",
        "ai_enriched": "false",
        "ai_summary": "",
        "ai_risk": "",
        "notes": site_text[:900],
    }
    score, confidence = score_row(row)
    row["fit_score"] = str(score)
    row["confidence"] = str(confidence)
    row["cold_email_opener"] = build_opener(company, agency_type, pain_angle)
    row["loom_idea"] = build_loom_idea(agency_type, pain_angle)
    return row


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


def shell_safe_openclaw_text(value: str) -> str:
    replacements = {
        "&": " and ",
        "|": " ",
        "<": " ",
        ">": " ",
        "^": " ",
        "%": " percent ",
    }
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
        return shell_safe_openclaw_text(value)
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
                parsed = parse_json_like_output(text)
                return parsed if isinstance(parsed, dict) else {"raw": text}
    return response


def enrich_with_openclaw(row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    payload = shell_safe_payload({
        "task": "enrich_b2b_agency_lead",
        "instructions": (
            "Use only the provided evidence. Return strict JSON with keys: "
            "company_summary, likely_workflow_pain, best_offer_angle, outreach_opener, "
            "loom_teardown_idea, priority_score, risk_flags, rationale. "
            "Do not invent client names, contacts, metrics, or compliance status."
        ),
        "company": {
            "name": row["company_name"],
            "website": row["website"],
            "country": row["country"],
            "agency_type": row["agency_type"],
            "b2b_signal": row["b2b_signal"],
            "pain_angle": row["pain_angle"],
            "pain_evidence": row["pain_evidence"],
            "notes_excerpt": row["notes"][:OPENCLAW_TEXT_CHARS],
        },
    })
    session_safe_domain = re.sub(r"[^a-zA-Z0-9_-]+", "-", row["domain"])[:80]
    command = [
        args.openclaw_command,
        "agent",
        "--agent",
        args.openclaw_agent,
        "--session-id",
        f"agency-enrichment-{TODAY}-{session_safe_domain}",
        "--message",
        json.dumps(payload, ensure_ascii=True),
        "--thinking",
        args.openclaw_thinking,
        "--json",
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.openclaw_timeout,
    )
    if result.returncode != 0:
        row["ai_risk"] = clean_text(result.stderr)[:500] or f"OpenClaw exited with {result.returncode}"
        return row

    response = parse_json_like_output(result.stdout)
    output = openclaw_output_payload(response)
    if not isinstance(output, dict):
        row["ai_risk"] = "OpenClaw returned non-dict output"
        return row

    row["ai_enriched"] = "true"
    summary_parts = [
        clean_text(str(output.get("company_summary", ""))),
        clean_text(str(output.get("likely_workflow_pain", ""))),
        clean_text(str(output.get("best_offer_angle", ""))),
        clean_text(str(output.get("rationale", ""))),
    ]
    row["ai_summary"] = " | ".join(part for part in summary_parts if part)[:700]

    risk_flags = output.get("risk_flags", "")
    if isinstance(risk_flags, list):
        risk = "; ".join(clean_text(str(flag)) for flag in risk_flags if clean_text(str(flag)))
    else:
        risk = clean_text(str(risk_flags))
    if risk:
        row["ai_risk"] = risk[:500]
    opener = clean_text(str(output.get("outreach_opener", "")))
    loom_idea = clean_text(str(output.get("loom_teardown_idea", "")))
    if opener:
        row["cold_email_opener"] = opener[:700]
    if loom_idea:
        row["loom_idea"] = loom_idea[:700]
    return row


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_runbook(path: Path, rows: list[dict[str, str]], approval_rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    top_rows = approval_rows[:15]
    lines = [
        "# B2B Agency Prospecting Runbook",
        "",
        f"Generated: {TODAY}",
        "",
        "## Operating Rules",
        "",
        "- Do not send messages automatically from this batch.",
        "- Manually verify the decision-maker and contact before outreach.",
        "- Use the listed opener as a starting point, not final copy.",
        "- Keep the CTA low-friction: ask whether they want 2-3 specific automation ideas.",
        "- Respect opt-outs and add them to the suppression list before any follow-up.",
        "",
        "## Cost Controls",
        "",
        f"- OpenClaw enrichment was capped at {args.openclaw_top_n} leads for this run.",
        "- The deterministic score runs without paid APIs.",
        "- Use paid data/sending APIs only after a reply angle proves useful.",
        "",
        "## Output Files",
        "",
        f"- Full pipeline CSV: `{path.parent / f'agency_pipeline_{TODAY}.csv'}`",
        f"- Approval CSV: `{path.parent / f'agency_outreach_approval_{TODAY}.csv'}`",
        "",
        "## Top Approval Candidates",
        "",
    ]
    for index, row in enumerate(top_rows, start=1):
        lines.extend(
            [
                f"### {index}. {row['company_name']}",
                "",
                f"- Website: {row['website']}",
                f"- Agency type: {row['agency_type']}",
                f"- Country: {row['country'] or 'unknown'}",
                f"- Fit score: {row['fit_score']}",
                f"- Pain angle: {row['pain_angle']}",
                f"- Evidence: {row['pain_evidence']}",
                f"- Contact titles: {row['recommended_contact_titles']}",
                f"- Opener: {row['cold_email_opener']}",
                f"- Loom idea: {row['loom_idea']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_candidates(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    seed_file = args.seed_file or (SEED_URLS_FILE if SEED_URLS_FILE.exists() else SEED_URLS_EXAMPLE_FILE)
    candidates.extend(load_seed_candidates(seed_file))
    for input_csv in args.input_csv:
        candidates.extend(load_csv_candidates(input_csv))
    if args.search:
        for query in SEARCH_QUERIES[: args.query_limit]:
            print(f"Searching: {query}")
            try:
                candidates.extend(search(query, args.max_results_per_query))
            except httpx.HTTPError as exc:
                print(f"  search failed: {exc}")
            time.sleep(args.request_delay)
    return candidates


def build_pipeline(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    candidates = build_candidates(args)
    rows_by_domain: dict[str, dict[str, str]] = {}
    for candidate in candidates:
        domain = root_domain(candidate.url)
        if not domain or domain in rows_by_domain:
            continue
        if args.max_sites and len(rows_by_domain) >= args.max_sites:
            break
        print(f"Analyzing: {domain}")
        row = analyze_site(candidate, args.max_pages_per_site, args.request_delay)
        if row:
            rows_by_domain[row["domain"]] = row
        time.sleep(args.request_delay)

    rows = sorted(rows_by_domain.values(), key=lambda item: int(item["fit_score"]), reverse=True)
    if args.openclaw_top_n > 0:
        enrichable = [row for row in rows if int(row["fit_score"]) >= args.min_score][: args.openclaw_top_n]
        for row in enrichable:
            print(f"OpenClaw enriching: {row['domain']}")
            enrich_with_openclaw(row, args)
            time.sleep(args.request_delay)

    approval_rows = [row for row in rows if int(row["fit_score"]) >= args.min_score]
    for row in approval_rows:
        row["status"] = "needs_manual_review"
    return rows, approval_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a low-cost B2B agency lead pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned config without network calls.")
    parser.add_argument("--no-search", dest="search", action="store_false", help="Skip public search and use seeds/CSV only.")
    parser.set_defaults(search=True)
    parser.add_argument("--seed-file", type=Path, default=None, help="Seed URL file. Defaults to agency_seed_urls.txt or example.")
    parser.add_argument("--input-csv", type=Path, action="append", default=[], help="Optional Apollo/CSV export to import.")
    parser.add_argument("--query-limit", type=int, default=len(SEARCH_QUERIES), help="Number of search queries to run.")
    parser.add_argument("--max-results-per-query", type=int, default=6, help="Search results to inspect per query.")
    parser.add_argument("--max-sites", type=int, default=80, help="Maximum unique sites to analyze.")
    parser.add_argument("--max-pages-per-site", type=int, default=4, help="Maximum internal pages to fetch per site.")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum fit score for outreach approval CSV.")
    parser.add_argument("--request-delay", type=float, default=1.0, help="Delay between public requests.")
    parser.add_argument("--openclaw-top-n", type=int, default=0, help="Top qualified leads to enrich with OpenClaw. Default off.")
    parser.add_argument("--openclaw-command", default="openclaw", help="OpenClaw command path.")
    parser.add_argument("--openclaw-agent", default="lead-enrichment-copilot", help="OpenClaw agent id for enrichment.")
    parser.add_argument("--openclaw-thinking", default="low", choices=("low", "medium", "high"), help="OpenClaw thinking level.")
    parser.add_argument("--openclaw-timeout", type=int, default=90, help="OpenClaw invocation timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_file = args.seed_file or (SEED_URLS_FILE if SEED_URLS_FILE.exists() else SEED_URLS_EXAMPLE_FILE)
    if args.dry_run:
        print("B2B agency pipeline dry run")
        print(f"Seed file: {seed_file}")
        print(f"Search enabled: {args.search}")
        print(f"Queries: {min(args.query_limit, len(SEARCH_QUERIES))}")
        print(f"Max sites: {args.max_sites}")
        print(f"OpenClaw top N: {args.openclaw_top_n}")
        return

    rows, approval_rows = build_pipeline(args)
    full_csv = OUTPUT_DIR / f"agency_pipeline_{TODAY}.csv"
    approval_csv = OUTPUT_DIR / f"agency_outreach_approval_{TODAY}.csv"
    runbook = OUTPUT_DIR / f"agency_pipeline_runbook_{TODAY}.md"
    write_csv(full_csv, rows)
    write_csv(approval_csv, approval_rows)
    write_runbook(runbook, rows, approval_rows, args)
    print(f"\nSaved {len(rows)} researched agencies")
    print(f"Approval-ready: {len(approval_rows)}")
    print(f"Full CSV: {full_csv}")
    print(f"Approval CSV: {approval_csv}")
    print(f"Runbook: {runbook}")


if __name__ == "__main__":
    main()
