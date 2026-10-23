#!/usr/bin/env python3
"""Pull tobacconistofgreenwich.com into snapshots/greenwich.json.gz.

    ./greenwich.py              # pull now
    ./greenwich.py --if-stale   # pull only when the cache is older than 10 hours

The Tobacconist of Greenwich is a BigCommerce shop with a deep rare-Fuente and
Davidoff list, which is exactly where the six Shopify sites are thin. It has no
products.json, but every page it serves carries a public storefront token for its
own GraphQL endpoint, and that returns each product's variants (Single / Box of N)
with price and stock - 50 products a request instead of one page per product.

robots.txt asks AI agents for a 10-second crawl delay, so requests are spaced at
PAUSE seconds. The catalogue is ~2,700 products, so a pull is ~55 requests and
about ten minutes - hence --if-stale, which keeps it to twice a day.

Stock is real here (inventory.isInStock per variant), unlike tampasweethearts.

A variant priced at $0 while in stock is kept and reported: on 2026-10-23 the
Destino al Siglo de Familias box of 13 (normally $535) listed at $0.00 and took an
order. That is a data error on their side, not a price, so promos.py never uses a
zero as a rival price - it only reports it.
"""
import json, gzip, os, re, sys, time, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monitor as M

HERE  = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "snapshots", "greenwich.json.gz")
HOST  = "https://tobacconistofgreenwich.com"
PAUSE, STALE_HOURS, MIN_ROWS = 10, 10, 500

QUERY = """query($after: String) { site { products(first: 50, after: $after) {
  pageInfo { hasNextPage endCursor }
  edges { node { name path brand { name }
    variants(first: 25) { edges { node {
      inventory { isInStock }
      prices { price { value } }
      options { edges { node { displayName values { edges { node { label } } } } } }
    } } } } } } } }"""

def curl(args, tries=4):
    for a in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "60", "-A", "Mozilla/5.0"] + args,
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
        time.sleep(min(2 ** a, 8))
    return ""

def token():
    """The storefront token every visitor's browser is handed; it lasts ~2 days."""
    page = curl([HOST + "/"])
    m = re.search(r'eyJ0eXAiOiJKV1Qi[\w-]*\.[\w-]+\.[\w-]+', page)
    if not m:
        raise SystemExit("ABORT: no storefront token on the home page")
    return m.group(0)

def cache_age_hours(path=None):
    """Age from the ts inside the file - git clone resets mtime (see tampa.py)."""
    try:
        ts = json.load(gzip.open(path or CACHE, "rt"))["ts"]
        then = datetime.datetime.fromisoformat(ts)
        return (datetime.datetime.now(datetime.timezone.utc) - then).total_seconds() / 3600
    except (OSError, KeyError, ValueError):
        return None

def pull():
    tok, rows, after, n = token(), [], None, 0
    while True:
        body = json.dumps({"query": QUERY, "variables": {"after": after}})
        raw = curl([HOST + "/graphql", "-H", f"Authorization: Bearer {tok}",
                    "-H", "Content-Type: application/json", "-d", body])
        try:
            prods = json.loads(raw)["data"]["site"]["products"]
        except (ValueError, KeyError, TypeError):
            raise SystemExit(f"ABORT: bad GraphQL page after {n} products: {raw[:200]}")
        for e in prods["edges"]:
            p = e["node"]; n += 1
            for ve in p["variants"]["edges"]:
                v = ve["node"]
                fmt = " ".join(vv["node"]["label"] for o in v["options"]["edges"]
                               for vv in o["node"]["values"]["edges"]) or "Default Title"
                price = v["prices"]["price"]["value"] if v["prices"] else None
                if price is None: continue
                q = M.qty(fmt) or M.qty(p["name"])
                rows.append([p["name"], fmt, float(price), q,
                             bool(v["inventory"]["isInStock"]), HOST + p["path"]])
        print(f"  {n} products, {len(rows)} variants", file=sys.stderr)
        if not prods["pageInfo"]["hasNextPage"]: break
        after = prods["pageInfo"]["endCursor"]
        time.sleep(PAUSE)
    return rows

def main():
    if "--if-stale" in sys.argv:
        age = cache_age_hours()
        if age is not None and age < STALE_HOURS:
            print(f"greenwich cache is {age:.1f} hours old, under {STALE_HOURS} - skipping")
            return 0
    rows = pull()
    if len(rows) < MIN_ROWS:
        print(f"ABORT: only {len(rows)} variants; not overwriting the cache", file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with gzip.open(CACHE, "wt") as fh:
        json.dump({"ts": ts, "rows": sorted(rows)}, fh, separators=(",", ":"))
    zero = [r for r in rows if r[4] and r[2] <= 0]
    print(f"greenwich: {len(rows)} variants, {sum(r[4] for r in rows)} in stock, "
          f"{sum(1 for r in rows if r[3])} with a usable count -> {CACHE}")
    for r in zero:
        print(f"  $0 IN STOCK: {r[0]} [{r[1]}] {r[5]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
