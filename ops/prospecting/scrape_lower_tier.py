"""
Lower-tier lead scraper (Google Maps via Apify compass/crawler-google-places).

Goal: find SMALLER local operators (weak/free/missing website, modest review
count) that are stable + earning enough to pay an agency -- the opposite of the
established tier-2 firms that rank first on Google Maps.

Strategy: search smaller suburbs/localities so local operators rank top, cap
each search modestly, and save each job to disk the instant it returns. Runs are
resumable (skip jobs whose raw file already exists) and budget-guarded (hard stop
before the FREE-plan $5 cap).

Token is read from env APIFY_TOKEN -- never hardcode it here.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

ACTOR_ID = "nwua9Gu5YrADL7ZDj"  # compass/crawler-google-places (Google Maps Scraper)
TOKEN = os.environ["APIFY_TOKEN"]
BASE = "https://api.apify.com/v2"
RAW_DIR = os.path.join("data", "prospects", "raw")
BUDGET_HARD_STOP = 4.60  # stop before the $5 monthly cap; leaves a buffer

# Each job = one Apify run, saved to its own file the moment it finishes.
JOBS = [
    # ---- US ROOFING (lower-tier), Houston / Dallas / Tampa / Phoenix suburbs ----
    {"cat": "roofing", "niche": "roofing", "metro": "houston", "cap": 16, "searches": [
        "roofing contractor Humble TX", "roofing contractor Katy TX",
        "roofing contractor Pasadena TX", "roofing contractor Spring TX"]},
    {"cat": "roofing", "niche": "roofing", "metro": "dallas", "cap": 16, "searches": [
        "roofing contractor Garland TX", "roofing contractor Mesquite TX",
        "roofing contractor Irving TX", "roofing contractor Grand Prairie TX"]},
    {"cat": "roofing", "niche": "roofing", "metro": "tampa", "cap": 16, "searches": [
        "roofing contractor Brandon FL", "roofing contractor Riverview FL",
        "roofing contractor Plant City FL", "roofing contractor Largo FL"]},
    {"cat": "roofing", "niche": "roofing", "metro": "phoenix", "cap": 16, "searches": [
        "roofing contractor Mesa AZ", "roofing contractor Glendale AZ",
        "roofing contractor Avondale AZ", "roofing contractor Peoria AZ"]},

    # ---- INDIA INTERIOR (lower-tier), Bangalore / Delhi / Gurgaon localities ----
    {"cat": "interior", "niche": "interior", "metro": "bangalore", "cap": 14, "searches": [
        "interior designer Whitefield Bangalore", "modular kitchen Marathahalli Bangalore",
        "interior designer Electronic City Bangalore"]},
    {"cat": "interior", "niche": "interior", "metro": "delhi", "cap": 14, "searches": [
        "interior designer Rohini Delhi", "modular kitchen Dwarka Delhi",
        "interior designer Pitampura Delhi"]},
    {"cat": "interior", "niche": "interior", "metro": "gurgaon", "cap": 14, "searches": [
        "interior designer Sohna Road Gurgaon", "modular kitchen Sector 56 Gurgaon",
        "interior designer New Gurgaon"]},

    # ---- INDIA AESTHETIC CLINICS (lower-tier) ----
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "bangalore", "cap": 16, "searches": [
        "aesthetic clinic Whitefield Bangalore", "skin clinic Marathahalli Bangalore",
        "cosmetic clinic Jayanagar Bangalore", "dermatology clinic Electronic City Bangalore"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "delhi", "cap": 16, "searches": [
        "aesthetic clinic Rohini Delhi", "skin clinic Dwarka Delhi",
        "cosmetic clinic Lajpat Nagar Delhi"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "gurgaon", "cap": 16, "searches": [
        "aesthetic clinic Sohna Road Gurgaon", "skin clinic Sector 56 Gurgaon",
        "cosmetic clinic New Gurgaon"]},
]


def api_get(path):
    url = "%s%s%stoken=%s" % (BASE, path, "&" if "?" in path else "?", TOKEN)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def usage_usd():
    d = api_get("/users/me/limits")["data"]
    return float(d.get("current", {}).get("monthlyUsageUsd", 0.0))


def start_run(job):
    body = json.dumps({
        "searchStringsArray": job["searches"],
        "maxCrawledPlacesPerSearch": job["cap"],
        "language": "en",
        "skipClosedPlaces": True,
    }).encode()
    url = "%s/acts/%s/runs?token=%s" % (BASE, ACTOR_ID, TOKEN)
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)["data"]
    return d["id"], d["defaultDatasetId"]


def wait_run(run_id, max_wait=600):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        d = api_get("/actor-runs/%s" % run_id)["data"]
        st = d["status"]
        if st in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return st, d.get("usageTotalUsd")
        time.sleep(8)
    return "WAIT-TIMEOUT", None


def fetch_items(dataset_id):
    out, offset = [], 0
    while True:
        d = api_get("/datasets/%s/items?format=json&clean=true&limit=1000&offset=%d" % (dataset_id, offset))
        if not d:
            break
        out.extend(d)
        if len(d) < 1000:
            break
        offset += 1000
    return out


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    print("Start usage: $%.4f | hard stop at $%.2f" % (usage_usd(), BUDGET_HARD_STOP), flush=True)
    for job in JOBS:
        out_path = os.path.join(RAW_DIR, "%s_%s.json" % (job["cat"], job["metro"]))
        if os.path.exists(out_path):
            print("SKIP (already saved): %s" % out_path, flush=True)
            continue
        u = usage_usd()
        if u >= BUDGET_HARD_STOP:
            print("STOP: usage $%.4f >= hard stop $%.2f. Remaining jobs left un-run." % (u, BUDGET_HARD_STOP), flush=True)
            break
        print("RUN %s/%s (%d searches x %d) | usage $%.4f" % (
            job["cat"], job["metro"], len(job["searches"]), job["cap"], u), flush=True)
        try:
            run_id, ds_id = start_run(job)
            st, cost = wait_run(run_id)
            items = fetch_items(ds_id)
            # tag each record with our job metadata, then persist immediately
            for it in items:
                it["_metro"] = job["metro"]
                it["_niche"] = job["niche"]
                it["_cat"] = job["cat"]
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False)
            print("  -> %s | %d places | run cost ~$%s | saved %s" % (
                st, len(items), cost, out_path), flush=True)
        except urllib.error.HTTPError as e:
            print("  HTTP ERROR %s: %s" % (e.code, e.read()[:300]), flush=True)
        except Exception as e:
            print("  ERROR: %r" % e, flush=True)
    print("Final usage: $%.4f" % usage_usd(), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
