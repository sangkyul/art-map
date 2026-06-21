"""
Full pipeline: pull all paintings from Wikidata with sitelinks >= MIN_SITELINKS,
score them, and save paintings.json for the map.
"""

import json, time, math, csv, re, requests

HEADERS = {"User-Agent": "ArtMapPrototype/0.1 (research project; contact: example@example.com)"}
SPARQL = "https://query.wikidata.org/sparql"
MIN_SITELINKS = 10


def sparql(query, retries=4, pause=3):
    for attempt in range(retries):
        r = requests.get(SPARQL, params={"query": query, "format": "json"}, headers=HEADERS, timeout=120)
        if r.status_code == 200:
            return r.json()["results"]["bindings"]
        print(f"  SPARQL {r.status_code}, retry {attempt+1}...")
        time.sleep(pause * (attempt + 1))
    return []


# ── 1. Candidate list ─────────────────────────────────────────────────────────
print("Fetching candidate paintings...")
candidates = sparql(f"""
SELECT ?painting ?paintingLabel ?sitelinks WHERE {{
  ?painting wdt:P31 wd:Q3305213.
  ?painting wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks >= {MIN_SITELINKS})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY DESC(?sitelinks)
""")
print(f"  {len(candidates)} candidates")

qid_to_entry = {}
for b in candidates:
    qid = b["painting"]["value"].split("/")[-1]
    qid_to_entry[qid] = {
        "qid": qid,
        "label": b["paintingLabel"]["value"],
        "sitelinks": int(b["sitelinks"]["value"]),
        "creator": None,
        "collection": None,
        "location_label": None,
        "lat": None,
        "lon": None,
        "en_article": None,
        "image": None,
        "pageviews_12mo": 0,
        "score": 0,
    }


# ── 2. Detail query (batched) ─────────────────────────────────────────────────
def parse_wkt(wkt):
    """'Point(lon lat)' → (lat, lon)"""
    m = re.match(r"Point\(([^\s]+)\s+([^\)]+)\)", wkt or "")
    if m:
        return float(m.group(2)), float(m.group(1))
    return None, None


DETAIL_QUERY = """
SELECT ?painting ?creatorLabel ?collectionLabel ?locationLabel ?coord ?enArticle ?image WHERE {{
  VALUES ?painting {{ {values} }}
  OPTIONAL {{ ?painting wdt:P170 ?creator. }}
  OPTIONAL {{ ?painting wdt:P195 ?collection. }}
  OPTIONAL {{ ?painting wdt:P276 ?location. }}
  OPTIONAL {{ ?painting wdt:P276 ?locItem. ?locItem wdt:P625 ?coord1. }}
  OPTIONAL {{ ?painting wdt:P625 ?coord2. }}
  OPTIONAL {{ ?painting wdt:P195 ?collItem. ?collItem wdt:P625 ?coord3. }}
  BIND(COALESCE(?coord1, ?coord2, ?coord3) AS ?coord)
  OPTIONAL {{ ?painting wdt:P18 ?image. }}
  OPTIONAL {{
    ?enUri schema:about ?painting ;
           schema:isPartOf <https://en.wikipedia.org/> ;
           schema:name ?enArticle.
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""

qids = list(qid_to_entry.keys())
BATCH = 15
print(f"Enriching {len(qids)} paintings in batches of {BATCH}...")

for i in range(0, len(qids), BATCH):
    batch = qids[i : i + BATCH]
    values = " ".join(f"wd:{q}" for q in batch)
    rows = sparql(DETAIL_QUERY.format(values=values))
    for b in rows:
        qid = b["painting"]["value"].split("/")[-1]
        e = qid_to_entry.get(qid)
        if not e:
            continue
        if "creatorLabel" in b:
            e["creator"] = b["creatorLabel"]["value"]
        if "collectionLabel" in b:
            e["collection"] = b["collectionLabel"]["value"]
        if "locationLabel" in b and not str(b["locationLabel"]["value"]).startswith("http"):
            e["location_label"] = b["locationLabel"]["value"]
        if "coord" in b and e["lat"] is None:
            lat, lon = parse_wkt(b["coord"]["value"])
            if lat is not None:
                e["lat"], e["lon"] = lat, lon
        if "enArticle" in b:
            e["en_article"] = b["enArticle"]["value"]
        if "image" in b:
            e["image"] = b["image"]["value"]
    pct = min(100, int((i + BATCH) / len(qids) * 100))
    print(f"  {pct}% ({i+BATCH}/{len(qids)})")
    time.sleep(0.5)


# ── 3. Pageviews ──────────────────────────────────────────────────────────────
def get_pageviews(title, months=12):
    from datetime import date, timedelta
    end = date.today().replace(day=1) - timedelta(days=1)
    start = end - timedelta(days=31 * months)
    enc = title.replace(" ", "_").replace("/", "%2F")
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/user/{enc}/monthly/"
        f"{start.strftime('%Y%m01')}/{end.strftime('%Y%m%d')}"
    )
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return sum(i["views"] for i in r.json().get("items", []))
        if r.status_code == 404:
            return 0
        time.sleep(2)
    return 0


print("Fetching pageviews...")
for i, (qid, e) in enumerate(qid_to_entry.items()):
    if e["en_article"]:
        e["pageviews_12mo"] = get_pageviews(e["en_article"])
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{len(qid_to_entry)}")
    time.sleep(0.2)


# ── 4. Score ──────────────────────────────────────────────────────────────────
entries = list(qid_to_entry.values())
max_pv = max((e["pageviews_12mo"] for e in entries), default=1) or 1
max_sl = max((e["sitelinks"] for e in entries), default=1) or 1

for e in entries:
    pv = math.log1p(e["pageviews_12mo"]) / math.log1p(max_pv)
    sl = e["sitelinks"] / max_sl
    e["score"] = round(100 * (0.6 * pv + 0.4 * sl), 1)

entries.sort(key=lambda e: -e["score"])
entries = entries[:1000]

# ── 5. Save ───────────────────────────────────────────────────────────────────
with open("paintings.json", "w", encoding="utf-8") as f:
    json.dump(entries, f, indent=2, ensure_ascii=False)

fields = ["qid","label","creator","collection","location_label","lat","lon",
          "sitelinks","pageviews_12mo","score","en_article","image"]
with open("paintings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(entries)

print(f"\nSaved {len(entries)} paintings.")
print("\nTop 20:")
for e in entries[:20]:
    loc = e["collection"] or e["location_label"] or "?"
    print(f"  {e['score']:5.1f}  {e['label']} — {loc}")
