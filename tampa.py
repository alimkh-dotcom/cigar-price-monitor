#!/usr/bin/env python3
"""Scrape tampasweethearts.com into snapshots/tampa.json.gz for promos.py to use.

    ./tampa.py              # crawl now
    ./tampa.py --if-stale   # crawl only when the cache is older than 6 days

Tampa Sweethearts is the Fuente family's own shop, so for OpusX, Anejo, Don Carlos
and Destino it is one of the more relevant price references - and the only tracked
retailer that is not Shopify or WooCommerce. There is no JSON API and no XML
sitemap, so this walks the category tree.

Two things make it cheap enough to be worth doing:
  * listing pages already carry name + price, so most products need no detail fetch
  * only multi-format products show "From $X to $Y", and only those get fetched,
    where <option> Box of 25 / $342.50 </option> gives format and price together

Weekly is the right cadence. Their prices barely move: across 20 twice-daily
snapshots the Shopify sites changed 2% of variants in nine days, and this shop is
slower still, so a daily crawl would spend hundreds of requests to learn nothing.

LIMITATION: the site publishes no stock status - no "out of stock" marker appears
anywhere in the markup. Sold-out items appear to be delisted instead, so a listing
is treated as available. That is an assumption, not an observation, and anything
this feed wins on should be confirmed on the site before buying.
"""
import json, gzip, os, re, sys, time, html, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monitor as M

HERE  = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "snapshots", "tampa.json.gz")
HOST  = "https://www.tampasweethearts.com"
SEEDS = ["/cigars.aspx", "/newarrivals.aspx"]
MAXPAGES, PAUSE, STALE_DAYS = 600, 0.4, 6

# robots.txt Disallow list - do not fetch these
BLOCKED = re.compile(r'^/(search|account|cart|change-password|checkout|custom\.css|'
                     r'download|email-a-friend|list-create|list-edit|list-search|'
                     r'list-view|offline|order-detail|order-history|RecurringEvent)', re.I)
SKIP = re.compile(r'(accessor|humidor|lighter|cutter|ashtray|apparel|gift-?card)', re.I)

def get(path, tries=4):
    url = path if path.startswith("http") else HOST + path
    for a in range(tries):
        r = subprocess.run(["curl", "-sSL", "-m", "60", "-A", "Mozilla/5.0", url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
        time.sleep(min(2 ** a, 8))
    return ""

def links(page):
    out = set()
    for h in re.findall(r'href="([^"#]+\.aspx[^"]*)"', page, re.I):
        h = html.unescape(h).split("?")[0]
        h = re.sub(r'^(?:\.\./)+', '/', h)
        if h.startswith("http"):
            if HOST not in h: continue
            h = h[len(HOST):]
        elif not h.startswith("/"):
            h = "/" + h
        if BLOCKED.match(h) or SKIP.search(h): continue
        out.add(h)
    return out

BLOCK = re.compile(r'<div class="product-list-item".*?(?=<div class="product-list-item"|\Z)', re.S)
NAME  = re.compile(r'<h5><a[^>]*>(.*?)</a>', re.S)
COST  = re.compile(r'product-list-cost-value">([^<]+)')
HREF  = re.compile(r'href="(/[^"]+\.aspx)"')
OPT   = re.compile(r'<option value="\d+">\s*([^<]+?)\s*/\s*\$([\d,]+\.\d\d)\s*</option>')
ONE   = re.compile(r'^\s*\$([\d,]+\.\d\d)\s*$')

def money(s): return float(s.replace(",", ""))

def crawl():
    # Product URLs must never be queued as listing pages. Expanding every link on a
    # category page swept the product pages into the frontier too, which pushed the
    # queue past 1,300 and tripped the page cap with most of the catalogue unseen.
    seen, queue, rows, detail, products = set(), list(SEEDS), {}, [], set()
    while queue and len(seen) < MAXPAGES:
        path = queue.pop(0)
        if path in seen: continue
        seen.add(path)
        page = get(path)
        time.sleep(PAUSE)
        if not page: continue
        found = 0
        for b in BLOCK.findall(page):
            n, c, u = NAME.search(b), COST.search(b), HREF.search(b)
            if not (n and c and u): continue
            found += 1
            name = re.sub(r'\s+', ' ', html.unescape(n.group(1))).strip()
            cost = html.unescape(c.group(1)).strip()
            url  = u.group(1)
            products.add(url)
            m = ONE.match(cost)
            if m:
                rows[(name, "")] = (money(m.group(1)), M.qty(name), url)
            elif "from" in cost.lower():
                detail.append((name, url))          # multi-format: needs its own page
        for l in links(page):
            if l not in seen and l not in products and l not in queue:
                queue.append(l)
        print(f"  {len(seen):3}/{len(seen)+len(queue):3} {path[:48]:50} {found} products",
              file=sys.stderr)
    print(f"  listing pages: {len(seen)} | single-price products: {len(rows)} | "
          f"multi-format to fetch: {len(detail)}", file=sys.stderr)
    for name, url in detail:
        page = get(url)
        time.sleep(PAUSE)
        for fmt, price in OPT.findall(page):
            fmt = re.sub(r'\s+', ' ', html.unescape(fmt)).strip()
            rows[(name, fmt)] = (money(price), M.qty(fmt) or M.qty(name), url)
    return rows

def main():
    if "--if-stale" in sys.argv:
        try:
            age = (time.time() - os.path.getmtime(CACHE)) / 86400
            if age < STALE_DAYS:
                print(f"tampa cache is {age:.1f} days old, under {STALE_DAYS} - skipping")
                return 0
        except OSError:
            pass
    rows = crawl()
    if len(rows) < 50:
        print(f"ABORT: only {len(rows)} products; not overwriting the cache", file=sys.stderr)
        return 2
    out = [[n, f, p, q, u] for (n, f), (p, q, u) in sorted(rows.items())]
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with gzip.open(CACHE, "wt") as fh:
        json.dump({"ts": ts, "rows": out}, fh, separators=(",", ":"))
    withq = sum(1 for r in out if r[3])
    print(f"tampasweethearts: {len(out)} listings ({withq} with a usable cigar count) -> {CACHE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
