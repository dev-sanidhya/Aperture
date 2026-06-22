"""
Clinic blast: pull as many aesthetic-clinic lower-tier leads as the Apify token
allows -- run until the account hits its real usage cap (user says ~$7), then stop.

Fresh localities AND new Indian metros (Mumbai, Pune, Hyderabad, Chennai, Noida,
Ahmedabad, Jaipur, Kolkata) so the dedupe step doesn't eat results.

Reliability: curl writes dataset to a UTF-8 file (-o); memory=2048. run-sync
timeouts that fail local save are fine -- the run still bills + stores its data
on Apify, recovered afterwards by re-fetching dataset ids.

Stops when: Apify returns a usage-limit error, OR a safety backstop is hit, OR
several consecutive jobs fail. Token from env APIFY_TOKEN.
"""
import json
import os
import subprocess
import tempfile

ACTOR = "nwua9Gu5YrADL7ZDj"
TOKEN = os.environ["APIFY_TOKEN"]
RAW = os.path.join("data", "prospects", "raw")
BACKSTOP = 7.20  # safety only; real stop is Apify's limit error

T = ["skin clinic", "cosmetic clinic", "aesthetic clinic", "skin care clinic",
     "dermatology clinic"]


def J(metro, *areas):
    # build a job: one search term per area, cycling through term variants
    searches = ["%s %s" % (T[i % len(T)], a) for i, a in enumerate(areas)]
    return {"metro": metro, "cap": 18, "searches": searches}


JOBS = [
    J("bangalore4", "Koramangala Bangalore", "Indiranagar Bangalore", "JP Nagar Bangalore", "Malleshwaram Bangalore"),
    J("delhi4", "Saket Delhi", "Punjabi Bagh Delhi", "Greater Kailash Delhi", "Mayur Vihar Delhi"),
    J("gurgaon4", "MG Road Gurgaon", "Sector 31 Gurgaon", "Sector 50 Gurgaon"),
    J("noida", "Sector 18 Noida", "Sector 62 Noida", "Greater Noida"),
    J("mumbai", "Andheri Mumbai", "Bandra Mumbai", "Borivali Mumbai", "Thane Mumbai"),
    J("pune", "Kothrud Pune", "Viman Nagar Pune", "Baner Pune", "Aundh Pune"),
    J("hyderabad", "Banjara Hills Hyderabad", "Madhapur Hyderabad", "Kukatpally Hyderabad", "Gachibowli Hyderabad"),
    J("chennai", "Adyar Chennai", "Anna Nagar Chennai", "Velachery Chennai", "T Nagar Chennai"),
    J("ahmedabad", "Satellite Ahmedabad", "Bopal Ahmedabad", "Maninagar Ahmedabad"),
    J("jaipur", "Vaishali Nagar Jaipur", "Malviya Nagar Jaipur", "C Scheme Jaipur"),
    J("kolkata", "Salt Lake Kolkata", "Ballygunge Kolkata", "Park Street Kolkata"),
    J("bangalore5", "Hebbal Bangalore", "Sarjapur Bangalore", "Kammanahalli Bangalore"),
    J("delhi5", "Vikaspuri Delhi", "Preet Vihar Delhi", "Model Town Delhi"),
    J("mumbai2", "Mulund Mumbai", "Goregaon Mumbai", "Vashi Navi Mumbai"),
    J("pune2", "Hadapsar Pune", "Wakad Pune", "Hinjewadi Pune"),
]


def curl_to_obj(args, timeout):
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


def is_limit_error(obj):
    if isinstance(obj, dict):
        err = json.dumps(obj).lower()
        return any(k in err for k in ("limit", "exceed", "usage", "payment", "402"))
    return False


def main():
    os.makedirs(RAW, exist_ok=True)
    print("Start usage: $%s | backstop $%.2f" % (usage(), BACKSTOP), flush=True)
    consecutive_fail = 0
    for job in JOBS:
        out = os.path.join(RAW, "clinic_%s.json" % job["metro"])
        if os.path.exists(out):
            print("SKIP saved: %s" % out, flush=True)
            continue
        u = usage()
        if u is not None and u >= BACKSTOP:
            print("STOP backstop: usage $%.4f >= $%.2f" % (u, BACKSTOP), flush=True)
            break
        print("RUN clinic/%s | usage $%s" % (job["metro"], u), flush=True)
        obj = run_job(job)
        if is_limit_error(obj):
            print("STOP: Apify usage limit hit -> %s" % json.dumps(obj)[:200], flush=True)
            break
        if not isinstance(obj, list) or not obj:
            consecutive_fail += 1
            print("  FAILED/empty (run still billed; recoverable). consecutive=%d" % consecutive_fail, flush=True)
            if consecutive_fail >= 4:
                print("STOP: too many consecutive failures (likely cap or network).", flush=True)
                break
            continue
        consecutive_fail = 0
        for it in obj:
            it["_cat"], it["_niche"], it["_metro"] = "clinic", "aesthetic_clinic", job["metro"].rstrip("0123456789")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        print("  -> %d places saved %s" % (len(obj), out), flush=True)
    print("Final usage: $%s\nDONE" % usage(), flush=True)


if __name__ == "__main__":
    main()
