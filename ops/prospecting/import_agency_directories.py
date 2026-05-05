from __future__ import annotations

import argparse
import csv
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "prospects"
ACTIVE_OUTPUT_DIR = OUTPUT_DIR / "current"
TODAY = date.today().isoformat()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DIRECTORY_FIELDS = [
    "company_name",
    "website",
    "domain",
    "directory",
    "category",
    "profile_url",
    "rank",
    "status",
    "notes",
]

NOISE_DOMAINS = {
    "agencyreview.dev",
    "agencysort.com",
    "schema.org",
    "googletagmanager.com",
    "google-analytics.com",
    "cdn.sanity.io",
    "cookiebot.com",
    "googlesyndication.com",
    "google.com",
    "clutch.co",
    "hubspot.com",
    "agencyloft.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",
}


@dataclass
class DirectoryProfile:
    company_name: str
    profile_url: str
    directory: str
    category: str
    rank: int
    notes: str = ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def root_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def base_website(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def category_from_profile_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if "/" not in path:
        return ""
    return path.split("/", 1)[0].replace("-", " ")


def fetch(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    response.raise_for_status()
    return response.text


def fetch_optional(client: httpx.Client, url: str) -> tuple[str, str]:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return "", f"fetch failed: {exc}"
    return response.text, ""


def slug_name_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"\s+", " ", slug.replace("-", " ").replace("_", " ")).strip().title()


def xml_locs(xml_text: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    locs: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            locs.append(clean_text(element.text))
    return locs


def parse_json_ld_blocks(html: str) -> list[object]:
    soup = BeautifulSoup(html, "html.parser")
    blocks: list[object] = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        text = script.string or script.get_text()
        if not text:
            continue
        try:
            blocks.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return blocks


def agencyreview_profiles(client: httpx.Client) -> list[DirectoryProfile]:
    urls = [
        "https://agencyreview.dev/lead-gen-agencies",
        "https://agencyreview.dev/marketing-agencies",
        "https://agencyreview.dev/software-agencies",
    ]
    profiles: list[DirectoryProfile] = []
    seen: set[str] = set()
    for url in urls:
        html = fetch(client, url)
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if not re.match(r"^/[a-z-]+-agencies/[^/]+$", href):
                continue
            profile_url = urljoin(url, href)
            if profile_url in seen:
                continue
            seen.add(profile_url)
            name = ""
            heading = anchor.find(["h2", "h3"])
            if heading:
                name = clean_text(heading.get_text(" ", strip=True))
            if not name:
                card = anchor.find_parent(["article", "div"])
                if card:
                    heading = card.find(["h2", "h3"])
                    name = clean_text(heading.get_text(" ", strip=True) if heading else "")
            if not name:
                slug = urlparse(profile_url).path.rsplit("/", 1)[-1]
                name = slug.replace("-", " ").title()
            profiles.append(
                DirectoryProfile(
                    company_name=name,
                    profile_url=profile_url,
                    directory="agencyreview",
                    category=category_from_profile_url(profile_url),
                    rank=len(profiles) + 1,
                )
            )
    return profiles


def agencysort_profiles(client: httpx.Client) -> list[DirectoryProfile]:
    url = "https://agencysort.com/agencies"
    html = fetch(client, url)
    soup = BeautifulSoup(html, "html.parser")
    profiles: list[DirectoryProfile] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if not href.startswith("/agencies/"):
            continue
        profile_url = urljoin(url, href)
        if profile_url in seen:
            continue
        seen.add(profile_url)
        card = anchor.find_parent(attrs={"data-slot": "card"})
        name = ""
        if card:
            heading = card.find(["h2", "h3"])
            name = clean_text(heading.get_text(" ", strip=True) if heading else "")
        if not name:
            name = clean_text(anchor.get_text(" ", strip=True)).replace("View listing", "").strip()
        if not name:
            slug = urlparse(profile_url).path.rsplit("/", 1)[-1]
            name = slug.replace("-", " ").title()
        profiles.append(
            DirectoryProfile(
                company_name=name,
                profile_url=profile_url,
                directory="agencysort",
                category="agency directory",
                rank=len(profiles) + 1,
            )
        )
    return profiles


def agencyloft_profiles(client: httpx.Client) -> list[DirectoryProfile]:
    sitemap_url = "https://www.agencyloft.com/job_listing-sitemap.xml"
    html = fetch(client, sitemap_url)
    profiles: list[DirectoryProfile] = []
    seen: set[str] = set()
    for loc in xml_locs(html):
        if "/listing/" not in loc or loc.rstrip("/").endswith("/listings"):
            continue
        if loc in seen:
            continue
        seen.add(loc)
        profiles.append(
            DirectoryProfile(
                company_name=slug_name_from_url(loc),
                profile_url=loc,
                directory="agencyloft",
                category="marketing agency directory",
                rank=len(profiles) + 1,
            )
        )
    return profiles


def clutch_sitemap_profiles(client: httpx.Client, *, max_sitemaps: int) -> list[DirectoryProfile]:
    sitemap_index = fetch(client, "https://clutch.co/sitemap.xml")
    profile_sitemaps = [
        loc
        for loc in xml_locs(sitemap_index)
        if "/sitemap-profile-" in loc
    ][:max_sitemaps]
    profiles: list[DirectoryProfile] = []
    seen: set[str] = set()
    for sitemap_url in profile_sitemaps:
        sitemap_text, error = fetch_optional(client, sitemap_url)
        if error:
            print(f"  clutch sitemap skipped: {sitemap_url} ({error})")
            continue
        for loc in xml_locs(sitemap_text):
            if "/profile/" not in loc or loc in seen:
                continue
            seen.add(loc)
            profiles.append(
                DirectoryProfile(
                    company_name=slug_name_from_url(loc),
                    profile_url=loc,
                    directory="clutch-sitemap",
                    category="clutch profile",
                    rank=len(profiles) + 1,
                )
            )
    return profiles


def hubspot_solution_profiles(client: httpx.Client, *, max_profiles: int) -> list[DirectoryProfile]:
    url = (
        "https://api.hubspot.com/marketplace-search/public/v1/profiles/search"
        "?hs_static_app=ecosystem-marketplace-solutions-public-ui"
        "&hs_static_app_version=1.17972"
    )
    profiles: list[DirectoryProfile] = []
    seen: set[str] = set()
    page_size = min(100, max_profiles or 100)
    offset = 0
    while not max_profiles or len(profiles) < max_profiles:
        payload = [{"limit": page_size, "offset": offset}]
        response = client.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://ecosystem.hubspot.com",
                "Referer": "https://ecosystem.hubspot.com/marketplace/solutions/all",
            },
        )
        response.raise_for_status()
        batches = response.json()
        batch = batches[0] if isinstance(batches, list) and batches else {}
        items = batch.get("items", []) if isinstance(batch, dict) else []
        if not items:
            break
        for item in items:
            if not isinstance(item, dict):
                continue
            slug = clean_text(str(item.get("slug", "")))
            name = clean_text(str(item.get("name", "")))
            if not slug or slug in seen:
                continue
            seen.add(slug)
            review_summary = item.get("reviewSummary", {}) if isinstance(item.get("reviewSummary"), dict) else {}
            tier = clean_text(str(item.get("tier", "")))
            reviews = clean_text(str(review_summary.get("reviewCount", "")))
            profiles.append(
                DirectoryProfile(
                    company_name=name or slug_name_from_url(slug),
                    profile_url=f"https://ecosystem.hubspot.com/marketplace/solutions/{slug}",
                    directory="hubspot-solutions",
                    category=f"hubspot {tier.lower()} partner".strip(),
                    rank=len(profiles) + 1,
                    notes=f"tier={tier}; reviews={reviews}".strip("; "),
                )
            )
            if max_profiles and len(profiles) >= max_profiles:
                break
        offset += len(items)
        if offset >= int(batch.get("total", offset)):
            break
    return profiles


def extract_external_website(client: httpx.Client, profile_url: str) -> str:
    html = fetch(client, profile_url)
    soup = BeautifulSoup(html, "html.parser")

    candidates: list[str] = []
    for block in parse_json_ld_blocks(html):
        nodes = block.get("@graph", [block]) if isinstance(block, dict) else []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            for key in ("url", "sameAs"):
                value = node.get(key)
                values = value if isinstance(value, list) else [value]
                for item in values:
                    if isinstance(item, str) and item.startswith("http"):
                        candidates.append(item)

    preferred_candidates: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(profile_url, anchor.get("href", ""))
        text = clean_text(anchor.get_text(" ", strip=True)).lower()
        if href.startswith("http") and any(term in text for term in ("visit agency website", "visit website", "website")):
            preferred_candidates.append(href)
        if href.startswith("http"):
            candidates.append(href)

    for candidate in [*preferred_candidates, *candidates]:
        domain = root_domain(candidate)
        if not domain or domain in NOISE_DOMAINS:
            continue
        return base_website(candidate)
    return ""


def rows_from_profiles(
    client: httpx.Client,
    profiles: list[DirectoryProfile],
    *,
    max_profiles: int,
    request_delay: float,
    fetch_websites: bool,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    for profile in profiles[:max_profiles]:
        website = ""
        status = "needs_website"
        notes = ""
        if fetch_websites:
            try:
                website = extract_external_website(client, profile.profile_url)
                if website:
                    status = "discovered"
            except httpx.HTTPError as exc:
                notes = f"profile fetch failed: {exc}"
                status = "profile_fetch_failed"
        else:
            notes = "website not fetched for this source; resolve in a later search/enrichment pass"
        domain = root_domain(website)
        if domain and domain in seen_domains:
            continue
        if domain:
            seen_domains.add(domain)
        rows.append(
            {
                "company_name": profile.company_name,
                "website": website,
                "domain": domain,
                "directory": profile.directory,
                "category": profile.category,
                "profile_url": profile.profile_url,
                "rank": str(profile.rank),
                "status": status,
                "notes": "; ".join(part for part in (profile.notes, notes) if part),
            }
        )
        time.sleep(request_delay)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DIRECTORY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_seed_file(path: Path, rows: list[dict[str, str]]) -> None:
    websites = [row["website"] for row in rows if row.get("website")]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(websites) + ("\n" if websites else ""), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import public agency directory profiles.")
    parser.add_argument(
        "--source",
        action="append",
        choices=("agencyreview", "agencysort", "agencyloft", "clutch-sitemap", "hubspot-solutions", "all"),
        default=[],
        help="Directory source to import. Repeat to import multiple sources.",
    )
    parser.add_argument("--max-profiles", type=int, default=200)
    parser.add_argument("--max-sitemaps", type=int, default=1, help="Maximum profile sitemaps to read for sitemap-backed sources.")
    parser.add_argument("--no-profile-fetch", action="store_true", help="Do not fetch profile pages to resolve websites.")
    parser.add_argument("--request-delay", type=float, default=0.25)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output-csv", type=Path, default=ACTIVE_OUTPUT_DIR / "01_directory_accounts.csv")
    parser.add_argument("--output-seed-file", type=Path, default=ACTIVE_OUTPUT_DIR / "01_seed_urls.txt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = args.source or ["agencyreview", "agencysort", "agencyloft"]
    if "all" in sources:
        sources = ["agencyreview", "agencysort", "agencyloft", "hubspot-solutions", "clutch-sitemap"]
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    all_rows: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    with httpx.Client(timeout=args.timeout, follow_redirects=True, headers=headers) as client:
        for source in sources:
            if source == "agencyreview":
                profiles = agencyreview_profiles(client)
            elif source == "agencysort":
                profiles = agencysort_profiles(client)
            elif source == "agencyloft":
                profiles = agencyloft_profiles(client)
            elif source == "clutch-sitemap":
                profiles = clutch_sitemap_profiles(client, max_sitemaps=args.max_sitemaps)
            elif source == "hubspot-solutions":
                profiles = hubspot_solution_profiles(client, max_profiles=args.max_profiles)
            else:
                profiles = []
            print(f"{source}: found {len(profiles)} profiles")
            fetch_websites = not args.no_profile_fetch and source not in {"clutch-sitemap", "hubspot-solutions"}
            rows = rows_from_profiles(
                client,
                profiles,
                max_profiles=args.max_profiles,
                request_delay=args.request_delay,
                fetch_websites=fetch_websites,
            )
            for row in rows:
                domain = row.get("domain", "")
                key = domain or row.get("profile_url", "")
                if key in seen_domains:
                    continue
                seen_domains.add(key)
                all_rows.append(row)
    write_csv(args.output_csv, all_rows)
    write_seed_file(args.output_seed_file, all_rows)
    print(f"Rows written: {len(all_rows)}")
    print(f"CSV: {args.output_csv}")
    print(f"Seed URLs: {args.output_seed_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
