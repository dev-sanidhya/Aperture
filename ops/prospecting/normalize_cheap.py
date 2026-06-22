"""Normalize cheap-actor (S3TUPOWUK8RoocPjh) clinic datasets into the standard
shape build_lists.py expects, and write to raw/clinic_cheap.json."""
import glob
import json
import os

REC = os.path.join("data", "prospects", "raw_recover")
RAW = os.path.join("data", "prospects", "raw")


def metro_from(s):
    return (s or "").split()[-1].lower() if s else ""


out = []
seen = set()
for fp in glob.glob(os.path.join(REC, "cheap_clinics*.json")):
    try:
        data = json.load(open(fp, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(data, list):
        continue
    for x in data:
        pid = x.get("place_id") or x.get("cid") or x.get("title")
        if pid in seen:
            continue
        seen.add(pid)
        out.append({
            "title": x.get("title"),
            "phone": x.get("phone"),                    # valid_phone strips spaces
            "website": x.get("website") or "",
            "reviewsCount": x.get("review_count"),
            "totalScore": x.get("rating") or x.get("review_rating"),
            "city": metro_from(x.get("searchString")),
            "address": (x.get("address") or "").replace("\n", " "),
            "placeId": pid,
            "_cat": "clinic", "_niche": "aesthetic_clinic",
            "_metro": metro_from(x.get("searchString")),
        })

dest = os.path.join(RAW, "clinic_cheap.json")
json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False)
print("normalized %d cheap-actor clinic places -> %s" % (len(out), dest))
