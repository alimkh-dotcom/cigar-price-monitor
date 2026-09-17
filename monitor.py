#!/usr/bin/env python3
"""Scrape six Shopify cigar catalogs, diff against the last run, report what changed.

Only one file persists between runs: snapshots/state.json.gz — prices/availability/
counts keyed by variant id, names stripped (~210 KB). Names come from the live pull.
"""
import json, re, gzip, subprocess, sys, os, datetime, time
from collections import defaultdict

HERE  = os.path.dirname(os.path.abspath(__file__))
SITES = json.load(open(os.path.join(HERE, "sites.json")))
STATE = os.path.join(HERE, "snapshots", "state.json.gz")

DROP_PCT, BIG_DROP, CHEAP_RATIO, TRAP_RATIO = 0.20, 0.35, 0.70, 1.15
SEP = "␟"

# ---------------------------------------------------------------- scraping
def fetch(domain, page, tries=6):
    """(products, ok). ok=False is a failed request, not an empty page."""
    url = f"https://{domain}/products.json?limit=250&page={page}"
    for attempt in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "90", "-A", "Mozilla/5.0", url],
                           capture_output=True)
        if r.returncode == 0:
            try:
                return json.loads(r.stdout).get("products", []), True
            except Exception:
                pass
        time.sleep(min(2 ** attempt, 20))
    return [], False

def qty(title):
    """Cigars in this variant, or None when the label doesn't say."""
    t = title.strip().lower().replace("-", " ")
    if t in ("single cigar", "single", "1 cigar", "single pack", "1 tubo", "1 pack"):
        return 1
    if t == "default title":
        return None                                  # unknown - never guess
    m = re.search(r'(\d+)\s*(?:tins?|packs?)\s*of\s*(\d+)', t)
    if m: return int(m.group(1)) * int(m.group(2))
    m = re.search(r'(?:box|bundle|tin|pack|boat|chest|cabinet|packs|case)\s*(?:of\s*)?(\d+)', t)
    if m: return int(m.group(1))
    m = re.search(r'^(\d+)\s*(?:cigars?|tubos?|pack)', t)
    if m: return int(m.group(1))
    if re.match(r'^five\s*pack', t): return 5
    return None

def scrape():
    cur, names, bad = {}, {}, []
    for site, domain in SITES.items():
        n, failed = 0, False
        for page in range(1, 41):
            prods, ok = fetch(domain, page)
            if not ok:
                failed = True
                break
            if not prods:
                break
            for p in prods:
                for var in p["variants"]:
                    try: price = float(var["price"])
                    except (TypeError, ValueError): continue
                    key = f"{site}:{var['id']}"
                    cur[key]   = [price, 1 if var["available"] else 0, qty(var["title"])]
                    names[key] = f"{p['title']}{SEP}{var['title']}"
                    n += 1
            time.sleep(1.5)                          # iheart 429s without this
        print(f"  {site:14} {n:6}{'  INCOMPLETE' if failed else ''}", file=sys.stderr)
        if failed: bad.append(site)
    return cur, names, bad

# ---------------------------------------------------------------- diffing
def report(cur, names, prev, prev_ts, ts):
    per = lambda r: (r[0] / r[2]) if r[2] else None
    prod = lambda k: names[k].split(SEP)[0]

    peers = defaultdict(list)
    for k, r in cur.items():
        p = per(r)
        if p is not None and r[1]:
            peers[(k.split(":")[0], prod(k))].append(p)

    def cheapness(k):
        p = per(cur[k])
        if p is None: return None
        o = [x for x in peers[(k.split(":")[0], prod(k))] if abs(x - p) > 1e-9]
        return (p / min(o)) if o else None

    drops, restocks, news, breaks = [], [], [], []
    for k, r in cur.items():
        price, avail, q = r
        old = prev.get(k)
        if old is None:
            c = cheapness(k)
            if avail and c is not None and c <= CHEAP_RATIO:
                news.append((c, k, price, q))
            continue
        op, oa, _ = old
        if op > 0 and price < op * (1 - DROP_PCT):
            drops.append((price / op - 1, k, op, price, q, avail))
        elif not oa and avail:
            c = cheapness(k)
            if c is not None and c <= CHEAP_RATIO:
                restocks.append((c, k, price, q))
        if op > 0 and price > op * 1.20 and q:
            o = [x for x in peers[(k.split(":")[0], prod(k))] if abs(x - price / q) > 1e-9]
            if o and price / q >= min(o) * TRAP_RATIO:
                breaks.append((price / op - 1, k, op, price, q, price / q, min(o)))

    drops.sort(key=lambda x: x[0]); restocks.sort(key=lambda x: x[0])
    news.sort(key=lambda x: x[0]);  breaks.sort(key=lambda x: -x[0])

    def fmt(k, q, price):
        p, v = (names[k].split(SEP) + [""])[:2]
        return f"{p} [{v}]" + (f" = ${price/q:,.2f}/stick" if q else "")

    L = [f"# Cigar price monitor — {ts}",
         f"previous run {prev_ts} · {len(cur):,} variants tracked"]
    if not (drops or restocks or news or breaks):
        L.append("\n**No actionable changes.**")
        return "\n".join(L), 0

    if drops:
        L.append(f"\n## Price drops ≥{int(DROP_PCT*100)}%  ({len(drops)})")
        for d, k, o, p, q, av in drops[:40]:
            L.append(f"- **{-d*100:.0f}%**{' **BIG**' if -d >= BIG_DROP else ''} "
                     f"`{k.split(':')[0]}` {fmt(k,q,p)} — ${o:,.2f} → **${p:,.2f}**"
                     f"{'' if av else ' _(out of stock)_'}")
    if restocks:
        L.append(f"\n## Cheap restocks  ({len(restocks)})")
        for c, k, p, q in restocks[:20]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — back at ${p:,.2f} ({c*100:.0f}% of its next tier)")
    if news:
        L.append(f"\n## New listings below their own line  ({len(news)})")
        for c, k, p, q in news[:20]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — ${p:,.2f} ({c*100:.0f}% of its next tier)")
    if breaks:
        L.append(f"\n## Newly inflated variants  ({len(breaks)})")
        for d, k, o, p, q, ps, best in breaks[:20]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — ${o:,.2f} → ${p:,.2f}; "
                     f"now ${ps:,.2f}/stick vs ${best:,.2f} for its sibling")
    return "\n".join(L), len(drops) + len(restocks) + len(news) + len(breaks)

# ---------------------------------------------------------------- main
def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    cur, names, bad = scrape()
    if bad:
        print(f"ABORT: incomplete catalogs {bad}; state not updated", file=sys.stderr)
        print(f"# Cigar price monitor — {ts}\n\n**Run aborted** — could not fully "
              f"fetch: {', '.join(bad)}. State left untouched; next run will diff normally.")
        return 2

    prev, prev_ts = {}, None
    if os.path.exists(STATE):
        old = json.load(gzip.open(STATE, "rt"))
        prev, prev_ts = old["v"], old["ts"]

    if prev:
        text, n = report(cur, names, prev, prev_ts, ts)
    else:
        text, n = (f"# Cigar price monitor — {ts}\n\nBaseline captured "
                   f"({len(cur):,} variants). Next run will report changes."), 0
    print(text)

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with gzip.open(STATE, "wt") as f:
        json.dump({"ts": ts, "v": cur}, f, separators=(",", ":"))
    with open(os.path.join(HERE, "findings.md"), "a") as f:
        f.write("\n\n---\n\n" + text + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
