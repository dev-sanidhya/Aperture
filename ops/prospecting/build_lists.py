"""
Build final cold-calling lists from raw Google Maps scrapes.

Pipeline per category:
  1. Load all raw/<cat>_<metro>.json files.
  2. Validate + normalize phone (E.164) -> drop invalid/missing.
  3. Classify website quality (none / weak / http / own) -- lower-tier signal.
  4. Drop national chains and high-review giants (established tier-2).
  5. Score "lower-tier-ness" and keep the best up to the target count.
  6. Dedupe within batch AND against the existing supplied lists.

Outputs CSVs to data/prospects/.
"""
import csv
import json
import os
import re
import glob

RAW_DIR = os.path.join("data", "prospects", "raw")
OUT_DIR = os.path.join("data", "prospects")

TARGETS = {"roofing": 200, "interior": 100, "clinic": 150}
OUT_FILES = {
    "roofing": "us_roofing_lower_tier.csv",
    "interior": "india_interior_lower_tier.csv",
    "clinic": "india_aesthetic_clinics_lower_tier.csv",
}

# review ceiling above which a business is treated as an established giant
REVIEW_CEIL = {"roofing": 100, "interior": 60, "clinic": 60}


def is_lower_tier(rec, cat):
    """STRICT gate (user choice): only firms with a genuinely weak web presence
    -- no website, a free-builder/social site, or http-only. Custom-domain
    ('own') sites are excluded entirely. Also drop established giants by reviews."""
    rc = rec["reviews_count"] or 0
    wq = rec["website_quality"]
    if wq == "own":
        return False  # has a real website -> not the target tier
    if rc > REVIEW_CEIL[cat]:
        return False  # established giant
    return True

# national chains / franchises / aggregators to exclude (lowercased substrings)
CHAIN_KEYWORDS = [
    "servpro", "puroclean", "belfor", "roto-rooter", "rotorooter", "ati restoration",
    "jenkins restoration", "911 restoration", "erie home", "constellation",
    "kaya", "oliva", "vlcc", "kosmoderma", "skinnsi", "clinikally", "cult",
    "justdial", "sulekha", "urbancompany", "urban company", "housejoy",
    "homelane", "livspace", "designcafe", "design cafe",  # interior unicorns/big chains
]

WEAK_HOSTS = [
    "facebook.", "instagram.", "wixsite.", "wix.com", "business.site",
    "godaddysites.", "weebly.", "blogspot.", "wordpress.com", "sites.google.",
    "linktr.ee", "justdial.", "sulekha.", "wordpress.org", "blogger.",
    "google.com/maps", "yelp.", "indiamart.", "limbu.ai", "carrd.co",
    "grexa.site", "nowfloats", "webnode.", "site123.", "blogspot.",
    "book.healthplix", "healthplix.com", "practo.com", "page.link", "/g.page",
    "mystrikingly", "strikingly.com", "yola.", "jimdo.", "weebly",
]


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def valid_phone(raw, country):
    if not raw:
        return None
    p = re.sub(r"[^\d+]", "", raw)
    if country == "US":
        if re.fullmatch(r"\+1[2-9]\d{2}[2-9]\d{6}", p):
            return p
    elif country == "IN":
        if re.fullmatch(r"\+91[6-9]\d{9}", p):
            return p
    return None


def website_quality(url):
    if not url or not url.strip():
        return "none"
    u = url.strip().lower()
    if any(h in u for h in WEAK_HOSTS):
        return "weak"
    if u.startswith("http://"):
        return "http"
    return "own"


def score(rec, cat):
    s = 0
    wq = rec["website_quality"]
    s += {"none": 4, "weak": 3, "http": 1, "own": 0}[wq]
    rc = rec["reviews_count"]
    if rc is None:
        rc = 0
    if 5 <= rc <= 40:
        s += 3
    elif (2 <= rc <= 4) or (41 <= rc <= 80):
        s += 2
    elif 81 <= rc <= REVIEW_CEIL[cat]:
        s += 1
    elif rc > REVIEW_CEIL[cat]:
        s -= 3
    if (rec["rating"] or 0) >= 3.8:
        s += 1
    return s


EXISTING_FILES = [
    r"C:\Users\shish\Downloads\vapi_contacts.csv",
    r"C:\Users\shish\Downloads\india_call_list_personalized.csv",
]


def load_existing_keys():
    """Phone + name keys from the user's supplied lists, to dedupe against."""
    phones, names = set(), set()
    for fn in EXISTING_FILES:
        if not os.path.exists(fn):
            print("  WARN: existing file not found: %s" % fn)
            continue
        with open(fn, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                num = re.sub(r"[^\d+]", "", row.get("number", ""))
                if num:
                    phones.add(num)
                nm = norm_name(row.get("businessName", ""))
                if nm:
                    names.add(nm)
    return phones, names


def build(cat, country, ex_phones, ex_names):
    files = glob.glob(os.path.join(RAW_DIR, "%s_*.json" % cat))
    raw = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            raw.extend(json.load(f))

    seen_phone, seen_name = set(), set()
    cands = []
    for it in raw:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        low = title.lower()
        if any(k in low for k in CHAIN_KEYWORDS):
            continue
        phone = valid_phone(it.get("phoneUnformatted") or it.get("phone"), country)
        if not phone:
            continue
        nm = norm_name(title)
        # dedupe: within batch + against existing supplied lists
        if phone in seen_phone or nm in seen_name:
            continue
        if phone in ex_phones or nm in ex_names:
            continue
        seen_phone.add(phone)
        seen_name.add(nm)
        rec = {
            "number": phone,
            "businessName": title,
            "niche": it.get("_niche", cat),
            "metro": it.get("_metro", ""),
            "locality": it.get("city") or it.get("neighborhood") or "",
            "reviews_count": it.get("reviewsCount"),
            "rating": it.get("totalScore"),
            "website": it.get("website") or "",
            "website_quality": website_quality(it.get("website")),
            "address": (it.get("address") or "").replace("\n", " "),
        }
        if not is_lower_tier(rec, cat):
            continue
        rec["_score"] = score(rec, cat)
        cands.append(rec)

    # prefer weak/missing-website + modest-review (lower-tier), drop clearly big
    cands = [c for c in cands if c["_score"] > 0]
    cands.sort(key=lambda c: (c["_score"], -(c["reviews_count"] or 0)), reverse=True)
    keep = cands[:TARGETS[cat]]

    out_path = os.path.join(OUT_DIR, OUT_FILES[cat])
    cols = ["number", "businessName", "niche", "metro", "locality",
            "reviews_count", "rating", "website", "website_quality", "address"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in keep:
            w.writerow(r)

    wq = {}
    for r in keep:
        wq[r["website_quality"]] = wq.get(r["website_quality"], 0) + 1
    print("%-9s raw=%-4d candidates=%-4d kept=%-4d  -> %s" % (
        cat, len(raw), len(cands), len(keep), out_path))
    print("           website mix: %s" % wq)
    return len(keep)


def main():
    ex_phones, ex_names = load_existing_keys()
    print("Deduping against %d existing phones / %d existing names\n" % (
        len(ex_phones), len(ex_names)))
    countries = {"roofing": "US", "interior": "IN", "clinic": "IN"}
    for cat in ["roofing", "interior", "clinic"]:
        build(cat, countries[cat], ex_phones, ex_names)


if __name__ == "__main__":
    main()
