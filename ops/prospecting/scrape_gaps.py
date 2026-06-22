"""
Gap scraper -- fills the missing/short metros to maximise STRICT lower-tier
yield within the remaining FREE-plan budget.

Reliability fixes vs the first attempt:
  - Uses curl + run-sync-get-dataset-items (one blocking call, returns items
    directly). The earlier failures were urllib timeouts + abandoned async runs
    piling up against the 8 GB memory cap. run-sync completes before the next
    job starts, so there is never concurrency.
  - Pins memory=2048 MB so a run can never approach the FREE 8 GB ceiling.
  - Validates JSON and saves each job to disk the instant it returns.
  - Budget-guarded (hard stop) and resumable (skips jobs already saved).

Token from env APIFY_TOKEN.
"""
import json
import os
import subprocess
import tempfile

ACTOR = "nwua9Gu5YrADL7ZDj"
TOKEN = os.environ["APIFY_TOKEN"]
RAW = os.path.join("data", "prospects", "raw")
HARD_STOP = 4.50  # leaves >$0.40 headroom under the $5 cap

# Outer suburbs / smaller localities -> where small weak-web operators rank top.
# Priority order: fill obvious gaps first (phoenix roofing, clinic metros).
JOBS = [
    {"cat": "roofing", "niche": "roofing", "metro": "phoenix", "cap": 16, "searches": [
        "roofing contractor Surprise AZ", "roofing contractor Buckeye AZ",
        "roofing contractor Apache Junction AZ", "roofing contractor Maricopa AZ"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "bangalore2", "cap": 16, "searches": [
        "skin clinic KR Puram Bangalore", "cosmetic clinic Bommanahalli Bangalore",
        "aesthetic clinic RR Nagar Bangalore", "skin care clinic Yelahanka Bangalore"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "delhi2", "cap": 16, "searches": [
        "skin clinic Uttam Nagar Delhi", "cosmetic clinic Najafgarh Delhi",
        "aesthetic clinic Janakpuri Delhi", "skin care clinic Burari Delhi"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "gurgaon2", "cap": 16, "searches": [
        "skin clinic Palam Vihar Gurgaon", "cosmetic clinic Sector 10 Gurgaon",
        "aesthetic clinic Manesar"]},
    {"cat": "interior", "niche": "interior", "metro": "bangalore2", "cap": 14, "searches": [
        "interior decorator KR Puram Bangalore", "modular kitchen Bommanahalli Bangalore",
        "interior designer RR Nagar Bangalore"]},
    {"cat": "interior", "niche": "interior", "metro": "delhi2", "cap": 14, "searches": [
        "interior decorator Uttam Nagar Delhi", "modular kitchen Najafgarh Delhi",
        "interior designer Burari Delhi"]},
    {"cat": "roofing", "niche": "roofing", "metro": "houston2", "cap": 14, "searches": [
        "roofing contractor Conroe TX", "roofing contractor Baytown TX",
        "roofing contractor Rosenberg TX"]},
    {"cat": "roofing", "niche": "roofing", "metro": "dallas2", "cap": 14, "searches": [
        "roofing contractor Cleburne TX", "roofing contractor Waxahachie TX",
        "roofing contractor Terrell TX"]},
]


def curl_json(args, timeout):
    p = subprocess.run(["curl", "-s"] + args, capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout)
    except Exception:
        return None


def usage():
    d = curl_json(["--max-time", "40",
                   "https://api.apify.com/v2/users/me/limits?token=%s" % TOKEN], 60)
    try:
        return float(d["data"]["current"]["monthlyUsageUsd"])
    except Exception:
        return None


def run_job(job):
    body = {
        "searchStringsArray": job["searches"],
        "maxCrawledPlacesPerSearch": job["cap"],
        "language": "en",
        "skipClosedPlaces": True,
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(body, f)
    url = ("https://api.apify.com/v2/acts/%s/run-sync-get-dataset-items"
           "?token=%s&format=json&clean=true&memory=2048" % (ACTOR, TOKEN))
    try:
        items = curl_json(["--max-time", "290", "-X", "POST",
                           "-H", "Content-Type: application/json",
                           "-d", "@" + path, url], 320)
    finally:
        os.remove(path)
    return items


def main():
    os.makedirs(RAW, exist_ok=True)
    u0 = usage()
    print("Start usage: $%.4f | hard stop $%.2f" % (u0 or -1, HARD_STOP), flush=True)
    for job in JOBS:
        out = os.path.join(RAW, "%s_%s.json" % (job["cat"], job["metro"]))
        if os.path.exists(out):
            print("SKIP saved: %s" % out, flush=True)
            continue
        u = usage()
        if u is None:
            print("WARN: usage check failed; proceeding cautiously", flush=True)
        elif u >= HARD_STOP:
            print("STOP: usage $%.4f >= $%.2f. Remaining jobs left." % (u, HARD_STOP), flush=True)
            break
        print("RUN %s/%s | usage $%s" % (job["cat"], job["metro"], ("%.4f" % u) if u else "?"), flush=True)
        items = run_job(job)
        if not isinstance(items, list):
            print("  FAILED (no items / bad response) -- skipping", flush=True)
            continue
        for it in items:
            it["_cat"], it["_niche"], it["_metro"] = job["cat"], job["niche"], job["metro"]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
        print("  -> %d places saved %s" % (len(items), out), flush=True)
    print("Final usage: $%s" % ("%.4f" % usage() if usage() else "?"), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
