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
MAXQTY    = 200     # larger than any real box; beyond this the label is not a count
XR_GAP    = 0.25    # cross-retailer per-stick gap worth reporting
XR_MATCH  = 0.90    # Jaccard on distinctive tokens; below this we do not claim a match
XR_MINTOK = 3       # fewer distinctive words than this and the match means nothing
NEW_CAP   = 30      # new arrivals listed per section
SEP = "␟"

# Small formats sold inside a premium line are NOT the parent cigar. Matching a
# Coronet tin against a Belicoso box produced a string of bogus 60%+ "discounts"
# during manual analysis; never cross-match anything here.
SMALL = re.compile(r'papas fritas|coronet|ponies|cigarrito|cigarillo|petit |petite|'
                   r'puritos|senoritas|half corona|short story|\bminis?\b|breve|'
                   r'aperitif|prelude|prontos|amores|romeos|miniature|purito|chico|shorty|'
                   r'cubanito|junior|demi|\btins? of\b|x.press', re.I)
NONCIGAR = re.compile(r'ashtray|lighter|cutter|humidor|boveda|hygrometer|magazine|'
                      r'\bcase\b|wallet|keychain|mug|glass|solution|torch|\bpen\b|'
                      r'\bhat\b|shirt|book|\bbag\b|match|gift card', re.I)
BUNDLE = re.compile(r'sampler|assort|collection|gift|taster|taste of| \+ |combo|variety', re.I)
STOP = {"the","of","by","cigar","cigars","and","le","natural","maduro","edicion",
        "serie","series","discontinued","original","release","box","pack","packs",
        "single","singles","tin","tins","boxes","bundle","count","each","boat",
        "cabinet","chest","case","sampler","pk"}
SYN = {"af":"arturo","opus":"opusx","ffox":"opusx","x":"","no":"","number":""}

def keytokens(title, keep_nums=True):
    """Distinctive words only. Parenthesised sizes and ring gauges are dropped.

    Numbers are KEPT in product titles: 858, No.5 and Fifty Five are what separate
    one cigar from another, and stripping them matched Perfecxion No.5 to No.4.
    They are dropped from variant titles, where every number is a pack count.
    """
    t = re.sub(r'\(.*?\)', ' ', title.lower())
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    out = set()
    for w in t.split():
        if w[0].isdigit():
            if not keep_nums or len(w) > 4: continue   # 4-digit+ = a year or a size
            out.add(w); continue
        w = SYN.get(w, w)
        if w and w not in STOP and len(w) > 1:
            out.add(w)
    return frozenset(out)

def matchtokens(full):
    """Tokens for cross-retailer matching: product title PLUS the variant label.

    GT and tccigar put the vitola in the variant, not the product title, so matching
    on the product alone read Winston Churchill Petit Panetela as plain Churchill.
    """
    p, _, v = full.partition(SEP)
    return keytokens(p) | keytokens(v, keep_nums=False)

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
    # "6 Pack of 320 Gram" is a Boveda humidity pack, not 1,920 cigars
    if re.search(r'\d+\s*(?:grams?|\bg\b|oz|ounces?|ml|percent|%)', t):
        return None
    m = re.search(r'(\d+)\s*(?:tins?|packs?)\s*of\s*(\d+)', t)
    if m:
        n = int(m.group(1)) * int(m.group(2))
        return n if n <= MAXQTY else None
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

# ---------------------------------------------------------------- cross-retailer
def unitclass(q):
    """Singles and multipacks are different markets; never compare across them.

    A box is meant to cost less per stick than a single, so a box-vs-single gap is
    the normal shape of the market, not a mispricing. 2-4 counts are too ambiguous
    to place, so they are left out of matching entirely.
    """
    if q == 1: return "1"
    if q >= 5: return "m"
    return None

def xr_eligible(k, cur, names):
    """(tokens, unitclass, per-stick) for a listing safe to cross-match, else None."""
    price, avail, q = cur[k]
    if not avail or not q: return None
    cls = unitclass(q)
    if cls is None: return None
    full = names[k]
    if NONCIGAR.search(full) or BUNDLE.search(full) or SMALL.search(full): return None
    toks = matchtokens(full)
    if len(toks) < XR_MINTOK: return None
    return toks, cls, price / q

def build_xindex(cur, names):
    """Cheapest in-stock per-stick price per (site, tokens, unit class).

    Deliberately narrow: known cigar counts only, no samplers, no accessories,
    no small formats. Everything it cannot be sure about is left out.
    """
    best, tok2rows = {}, defaultdict(set)
    for k in cur:
        e = xr_eligible(k, cur, names)
        if not e: continue
        toks, cls, ps = e
        ident = (k.split(":")[0], toks, cls)
        if ident not in best or ps < best[ident][0]:
            best[ident] = (ps, k)
    rows = [(site, toks, cls, ps, k) for (site, toks, cls), (ps, k) in best.items()]
    for i, (_, toks, _, _, _) in enumerate(rows):
        for t in toks:
            tok2rows[t].add(i)
    return rows, tok2rows

def xr_check(k, cur, names, rows, tok2rows):
    """Best same-cigar price at another retailer, or None. Conservative by design."""
    e = xr_eligible(k, cur, names)
    if not e: return None
    toks, cls, mine = e
    site = k.split(":")[0]
    cand = defaultdict(int)
    for t in toks:
        for i in tok2rows.get(t, ()): cand[i] += 1
    out = None
    for i, shared in cand.items():
        osite, otoks, ocls, ops, ok_ = rows[i]
        if osite == site or ocls != cls or shared < XR_MINTOK: continue
        if shared / len(toks | otoks) < XR_MATCH: continue
        if out is None or ops < out[0]: out = (ops, osite, ok_)
    if out is None: return None
    return out if mine <= out[0] * (1 - XR_GAP) else None

# ---------------------------------------------------------------- diffing
def report(cur, names, prev, prev_ts, ts):
    per  = lambda r: (r[0] / r[2]) if r[2] else None
    prod = lambda k: names[k].split(SEP)[0]

    peers = defaultdict(list)
    groups = defaultdict(list)
    for k, r in cur.items():
        site = k.split(":")[0]
        groups[(site, prod(k))].append(k)
        p = per(r)
        if p is not None and r[1]:
            peers[(site, prod(k))].append(p)

    def cheapness(k):
        p = per(cur[k])
        if p is None: return None
        o = [x for x in peers[(k.split(":")[0], prod(k))] if abs(x - p) > 1e-9]
        return (p / min(o)) if o else None

    # --- A: every new listing, split by whether the product itself is new
    new_prod, new_var = [], []
    for (site, title), keys in groups.items():
        fresh = [k for k in keys if k not in prev]
        if not fresh: continue
        if NONCIGAR.search(title): continue
        bucket = new_prod if all(k not in prev for k in keys) else new_var
        for k in fresh:
            price, avail, q = cur[k]
            bucket.append((price, k, q, avail, cheapness(k)))

    drops, restocks, breaks = [], [], []
    for k, r in cur.items():
        price, avail, q = r
        old = prev.get(k)
        if old is None: continue
        if NONCIGAR.search(names[k]): continue   # ashtrays, lighters, Boveda, gift cards
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

    # --- B: cross-retailer, only for things that just changed
    rows, tok2rows = build_xindex(cur, names)
    seen, xr = set(), []
    for k in ([x[1] for x in new_prod] + [x[1] for x in new_var] +
              [x[1] for x in drops]    + [x[1] for x in restocks]):
        if k in seen: continue
        seen.add(k)
        hit = xr_check(k, cur, names, rows, tok2rows)
        if hit:
            ops, osite, ok_ = hit
            mine = cur[k][0] / cur[k][2]
            xr.append((mine / ops - 1, k, mine, osite, ops, ok_))

    drops.sort(key=lambda x: x[0]);     restocks.sort(key=lambda x: x[0])
    breaks.sort(key=lambda x: -x[0]);   xr.sort(key=lambda x: x[0])
    new_prod.sort(key=lambda x: -x[0]); new_var.sort(key=lambda x: -x[0])

    def fmt(k, q, price):
        p, v = (names[k].split(SEP) + [""])[:2]
        return f"{p} [{v}]" + (f" = ${price/q:,.2f}/stick" if q else "")

    def tail(c, avail):
        s = "" if avail else " _(out of stock)_"
        return s + (f" · **{c*100:.0f}% of its next tier**" if c is not None and c <= CHEAP_RATIO else "")

    L = [f"# Cigar price monitor — {ts}",
         f"previous run {prev_ts} · {len(cur):,} variants tracked"]
    total = len(drops) + len(restocks) + len(breaks) + len(new_prod) + len(new_var) + len(xr)
    if not total:
        L.append("\n**No actionable changes.**")
        return "\n".join(L), 0

    if drops:
        L.append(f"\n## Price drops ≥{int(DROP_PCT*100)}%  ({len(drops)})")
        for d, k, o, p, q, av in drops[:40]:
            L.append(f"- **{-d*100:.0f}%**{' **BIG**' if -d >= BIG_DROP else ''} "
                     f"`{k.split(':')[0]}` {fmt(k,q,p)} — ${o:,.2f} → **${p:,.2f}**"
                     f"{'' if av else ' _(out of stock)_'}")
    if new_prod:
        L.append(f"\n## New products  ({len(new_prod)})")
        for p, k, q, av, c in new_prod[:NEW_CAP]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — ${p:,.2f}{tail(c, av)}")
        if len(new_prod) > NEW_CAP: L.append(f"- _…{len(new_prod)-NEW_CAP} more_")
    if new_var:
        L.append(f"\n## New variants on existing products  ({len(new_var)})")
        for p, k, q, av, c in new_var[:NEW_CAP]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — ${p:,.2f}{tail(c, av)}")
        if len(new_var) > NEW_CAP: L.append(f"- _…{len(new_var)-NEW_CAP} more_")
    if restocks:
        L.append(f"\n## Cheap restocks  ({len(restocks)})")
        for c, k, p, q in restocks[:20]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — back at ${p:,.2f} ({c*100:.0f}% of its next tier)")
    if xr:
        L.append(f"\n## Cheaper than the same cigar elsewhere  ({len(xr)}) — _unverified, check the vitola_")
        for d, k, mine, osite, ops, ok_ in xr[:20]:
            oname = names[ok_].split(SEP)[0]
            L.append(f"- **{-d*100:.0f}% under** `{k.split(':')[0]}` {fmt(k, cur[k][2], cur[k][0])} "
                     f"vs ${ops:,.2f}/stick at `{osite}` ({oname})")
    if breaks:
        L.append(f"\n## Newly inflated variants  ({len(breaks)})")
        for d, k, o, p, q, ps, best in breaks[:20]:
            L.append(f"- `{k.split(':')[0]}` {fmt(k,q,p)} — ${o:,.2f} → ${p:,.2f}; "
                     f"now ${ps:,.2f}/stick vs ${best:,.2f} for its sibling")
    return "\n".join(L), total

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
