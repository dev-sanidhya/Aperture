"""Classify recovered Apify datasets by searchString -> raw/<cat>_<metro>.json"""
import glob
import json
import os

REC = os.path.join("data", "prospects", "raw_recover")
RAW = os.path.join("data", "prospects", "raw")
os.makedirs(RAW, exist_ok=True)

METRO_TOKENS = {
    "houston": ["humble", "katy", "pasadena", "spring tx", " spring ", "conroe",
                "baytown", "rosenberg", "texas city"],
    "dallas": ["garland", "mesquite", "irving", "grand prairie", "cleburne",
               "waxahachie", "terrell", "denton"],
    "tampa": ["brandon", "riverview", "plant city", "largo", "zephyrhills",
              "dade city", "ruskin", "lutz"],
    "phoenix": ["mesa", "glendale", "avondale", "peoria", "surprise", "buckeye",
                "apache junction", "maricopa"],
    "bangalore": ["bangalore", "bengaluru", "whitefield", "marathahalli",
                  "electronic city", "jayanagar", "kr puram", "bommanahalli",
                  "rr nagar", "yelahanka", "hsr layout", "btm layout",
                  "banashankari", "rajajinagar"],
    "delhi": ["delhi", "rohini", "dwarka", "pitampura", "lajpat", "uttam nagar",
              "najafgarh", "burari", "janakpuri", "karol bagh", "laxmi nagar",
              "paschim vihar", "kalkaji"],
    "gurgaon": ["gurgaon", "gurugram", "sohna", "sector 56", "palam vihar",
                "sector 10", "manesar", "new gurgaon", "dlf phase", "sushant lok",
                "sector 14", "sector 45"],
}


def classify(s):
    s = (s or "").lower()
    if "roofing" in s:
        cat, niche = "roofing", "roofing"
    elif "interior designer" in s or "modular kitchen" in s or "interior decorator" in s:
        cat, niche = "interior", "interior"
    elif ("aesthetic clinic" in s or "skin clinic" in s or "cosmetic clinic" in s
          or "dermatology" in s or "med spa" in s):
        cat, niche = "clinic", "aesthetic_clinic"
    else:
        return None, None, None
    metro = ""
    for m, toks in METRO_TOKENS.items():
        if any(t in s for t in toks):
            metro = m
            break
    return cat, niche, metro


buckets = {}
for fp in glob.glob(os.path.join(REC, "*.json")):
    if os.path.basename(fp).startswith("_"):
        continue
    try:
        data = json.load(open(fp, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(data, list):
        continue
    for it in data:
        cat, niche, metro = classify(it.get("searchString"))
        if not cat:
            continue
        it["_cat"], it["_niche"], it["_metro"] = cat, niche, metro
        buckets.setdefault((cat, metro), []).append(it)

# dedupe by placeId within each bucket, write files
total = 0
for (cat, metro), items in sorted(buckets.items()):
    seen, uniq = set(), []
    for it in items:
        pid = it.get("placeId") or it.get("title")
        if pid in seen:
            continue
        seen.add(pid)
        uniq.append(it)
    out = os.path.join(RAW, "%s_%s.json" % (cat, metro or "unknown"))
    json.dump(uniq, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    total += len(uniq)
    print("%-8s %-10s %3d -> %s" % (cat, metro, len(uniq), out))
print("TOTAL unique places: %d" % total)
