"""
Top-up scraper: MORE India interior + aesthetic-clinic lower-tier leads.

Fresh localities (not previously scraped) in Bangalore / Delhi / Gurgaon so the
dedupe step doesn't eat the results. Fixes vs scrape_gaps.py:
  - curl writes the dataset straight to a UTF-8 file (-o), then Python reads it
    as utf-8 -> no more cp1252 decode crash on Indian business names.
  - memory=2048 so even an orphaned slow run can't hit the FREE 8 GB cap.
Budget-guarded (hard stop) and resumable. Token from env APIFY_TOKEN.
"""
import json
import os
import subprocess
import tempfile

ACTOR = "nwua9Gu5YrADL7ZDj"
TOKEN = os.environ["APIFY_TOKEN"]
RAW = os.path.join("data", "prospects", "raw")
HARD_STOP = 4.50

# clinic first (weakest category), then interior; interleaved so both grow.
JOBS = [
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "bangalore3", "cap": 18, "searches": [
        "skin clinic HSR Layout Bangalore", "cosmetic clinic BTM Layout Bangalore",
        "aesthetic clinic Banashankari Bangalore", "skin care clinic Rajajinagar Bangalore"]},
    {"cat": "interior", "niche": "interior", "metro": "bangalore3", "cap": 16, "searches": [
        "interior decorator HSR Layout Bangalore", "modular kitchen BTM Layout Bangalore",
        "interior designer Banashankari Bangalore"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "delhi3", "cap": 18, "searches": [
        "skin clinic Karol Bagh Delhi", "cosmetic clinic Laxmi Nagar Delhi",
        "aesthetic clinic Paschim Vihar Delhi", "skin care clinic Kalkaji Delhi"]},
    {"cat": "interior", "niche": "interior", "metro": "delhi3", "cap": 16, "searches": [
        "interior decorator Karol Bagh Delhi", "modular kitchen Laxmi Nagar Delhi",
        "interior designer Paschim Vihar Delhi"]},
    {"cat": "clinic", "niche": "aesthetic_clinic", "metro": "gurgaon3", "cap": 18, "searches": [
        "skin clinic DLF Phase 3 Gurgaon", "cosmetic clinic Sushant Lok Gurgaon",
        "aesthetic clinic Sector 14 Gurgaon"]},
    {"cat": "interior", "niche": "interior", "metro": "gurgaon3", "cap": 16, "searches": [
        "interior decorator Sushant Lok Gurgaon", "modular kitchen Sector 45 Gurgaon",
        "interior designer DLF Phase 3 Gurgaon"]},
]


def curl_to_obj(args, timeout):
    """Run curl writing to a temp file, then read+parse it as UTF-8."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        subprocess.run(["curl", "-s", "-o", path] + args, timeout=timeout)
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
    finally:
        if os.path.exists(path):
            os.remove(path)


def usage():
    d = curl_to_obj(["--max-time", "40",
                     "https://api.apify.com/v2/users/me/limits?token=%s" % TOKEN], 60)
    try:
        return float(d["data"]["current"]["monthlyUsageUsd"])
    except Exception:
        return None


def run_job(job):
    body = {"searchStringsArray": job["searches"],
            "maxCrawledPlacesPerSearch": job["cap"],
            "language": "en", "skipClosedPlaces": True}
    fd, inp = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(body, f)
    url = ("https://api.apify.com/v2/acts/%s/run-sync-get-dataset-items"
           "?token=%s&format=json&clean=true&memory=2048" % (ACTOR, TOKEN))
    try:
        return curl_to_obj(["--max-time", "290", "-X", "POST",
                            "-H", "Content-Type: application/json",
                            "-d", "@" + inp, url], 320)
    finally:
        os.remove(inp)


def main():
    os.makedirs(RAW, exist_ok=True)
    print("Start usage: $%s | hard stop $%.2f" % (usage(), HARD_STOP), flush=True)
    for job in JOBS:
        out = os.path.join(RAW, "%s_%s.json" % (job["cat"], job["metro"]))
        if os.path.exists(out):
            print("SKIP saved: %s" % out, flush=True)
            continue
        u = usage()
        if u is not None and u >= HARD_STOP:
            print("STOP: usage $%.4f >= $%.2f" % (u, HARD_STOP), flush=True)
            break
        print("RUN %s/%s | usage $%s" % (job["cat"], job["metro"], u), flush=True)
        items = run_job(job)
        if not isinstance(items, list):
            print("  FAILED (no items) -- skipping", flush=True)
            continue
        clean_metro = job["metro"].rstrip("0123456789")
        for it in items:
            it["_cat"], it["_niche"], it["_metro"] = job["cat"], job["niche"], clean_metro
        with open(out, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
        print("  -> %d places saved %s" % (len(items), out), flush=True)
    print("Final usage: $%s\nDONE" % usage(), flush=True)


if __name__ == "__main__":
    main()
