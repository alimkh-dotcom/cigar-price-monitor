#!/usr/bin/env python3
"""iheartcigars promo analysis: Weekly Burn (Friday) and Monday Madness (Monday).

    ./promos.py burn        # 10% at 5 sticks, 20% at 10 sticks; picks the best 5 and 10
    ./promos.py madness     # on-site markdowns that revert within ~24h; picks the best 5 and 10

Each run compares against three things and says which one carried the pick:
  1. the other seven retailers, per stick, in stock only
  2. iheart's own other formats for the same cigar (box / 5-pack)
  3. every previous run of the same promo, stored under archive/

Matching is deliberately conservative. Vitola confusions and box-vs-single pairs
produced most of the bad findings during manual work, so singles only ever match
singles, names are compared in full, and samplers, accessories and small formats
are excluded outright.
"""
import json, gzip, os, re, sys, datetime, subprocess
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monitor as M

HERE    = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "archive")
LUX     = "luxurycigarclub.com"

PROMOS = {
    "burn":    dict(handle="weekly-burn",    label="Weekly Burn",
                    tiers=[(5, 0.10), (10, 0.20)]),
    "madness": dict(handle="monday-madness", label="Monday Madness", tiers=[]),
}

HOUSE      = {"arturo", "fuente"}   # retailers disagree on the house name;
                                    # iheart writes "OpusX X", cigarsdirect "Arturo Fuente X"
XR_SHARED  = 3               # at least this many shared distinctive words, AND one
                             # title's words must be a superset of the other's. A
                             # straight overlap score kept pairing Rojo with Morado
                             # and Corona Edwardian with Edwardian Robusto; requiring
                             # a superset means neither side may contradict the other.
INTEREST = re.compile(r'opus|fuente|don carlos|hemingway|a[nñ]ejo|rare pink|destino|'
                      r'padr[oó]n|davidoff|liga privada|atabey|alma fuerte|\besg\b|\bvsg\b|'
                      r'winston churchill|meerapfel|plasencia', re.I)

def toks(s):
    return frozenset(w for w in M.matchtokens(s) if w not in HOUSE)

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())        # FULL name - truncating paired vitolas

# ------------------------------------------------------------------ fetching
def collection(handle, tries=6):
    out = []
    for page in range(1, 6):
        url = f"https://iheartcigars.com/collections/{handle}/products.json?limit=250&page={page}"
        got = None
        for a in range(tries):
            r = subprocess.run(["curl", "-sS", "-m", "90", "-A", "Mozilla/5.0", url],
                               capture_output=True)
            if r.returncode == 0:
                try:
                    got = json.loads(r.stdout).get("products", []); break
                except Exception: pass
            __import__("time").sleep(min(2 ** a, 20))
        if got is None:
            raise SystemExit(f"ABORT: could not fetch {handle} page {page}")
        if not got: break
        out += got
    return out

def lux_products():
    out = []
    for page in range(1, 20):
        r = subprocess.run(["curl", "-sS", "-m", "90", "-A", "Mozilla/5.0",
                            f"https://{LUX}/products.json?limit=250&page={page}"],
                           capture_output=True)
        try: ps = json.loads(r.stdout).get("products", [])
        except Exception: break
        if not ps: break
        out += ps
    return out

def fresh_cache(max_age_h=6):
    """monitor.py's pull from minutes ago, if it is recent enough to trust."""
    try:
        age = (datetime.datetime.now().timestamp() - os.path.getmtime(M.RIVALS)) / 3600
        return M.RIVALS if age <= max_age_h else None
    except OSError:
        return None

def rivals(cached=None):
    """[(tokens, per_stick, site, label, unitclass, in_stock)] for countable rivals.

    Out-of-stock listings are kept, but only ever used as context: a cigar nobody
    has in stock still tells you whether iheart's price is sane. Out-of-stock
    prices never drive a recommendation - they cannot be acted on."""
    cached = cached or fresh_cache()
    if cached:
        live = json.load(gzip.open(cached, "rt")); cur, names = live["cur"], live["names"]
        print(f"  rivals: reusing {os.path.basename(cached)}", file=sys.stderr)
    else:
        cur, names, bad = M.scrape()
        if bad: raise SystemExit(f"ABORT: incomplete catalogs {bad}")
    rows = []
    def add(full, price, q, site, avail):
        if not q: return
        if M.NONCIGAR.search(full) or M.BUNDLE.search(full) or M.SMALL.search(full): return
        t = toks(full)
        if len(t) < XR_SHARED: return
        rows.append((t, price / q, site, full.replace(M.SEP, " | "), M.unitclass(q), bool(avail)))
    for k, (p, a, q) in cur.items():
        if k.startswith("iheart:"): continue
        add(names[k], p, q, k.split(":")[0], a)
    for pr in lux_products():
        for v in pr["variants"]:
            try: p = float(v["price"])
            except Exception: continue
            add(f"{pr['title']}{M.SEP}{v['title']}", p, M.qty(v["title"]), "luxurycigar", v["available"])
    return rows

def indexed(rows):
    idx = defaultdict(set)
    for i, r in enumerate(rows):
        for w in r[0]: idx[w].add(i)
    return idx

def best_rival(t, cls, rows, idx, in_stock=True):
    cand = defaultdict(int)
    for w in t:
        for i in idx.get(w, ()): cand[i] += 1
    out = None
    for i, sh in cand.items():
        ot = rows[i][0]
        if sh < XR_SHARED or not (t <= ot or ot <= t): continue
        if cls and rows[i][4] != cls: continue
        if in_stock and not rows[i][5]: continue
        if out is None or rows[i][1] < out[1]: out = (i, rows[i][1])
    return rows[out[0]] if out else None

# ------------------------------------------------------------------ archive
def archive_path(promo): return os.path.join(ARCHIVE, promo)

def archive_load(promo, exclude=None):
    """Previous runs, oldest first. Today's own entry is excluded so a re-run
    does not compare the report against itself."""
    d = archive_path(promo)
    if not os.path.isdir(d): return []
    out = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json") or fn[:-5] == exclude: continue
        try: out.append((fn[:-5], json.load(open(os.path.join(d, fn)))))
        except Exception: pass
    return out

def archive_save(promo, date, items):
    d = archive_path(promo); os.makedirs(d, exist_ok=True)
    json.dump(items, open(os.path.join(d, f"{date}.json"), "w"), separators=(",", ":"))

# ------------------------------------------------------------------ analysis
def singles_and_alts(prods):
    """{product title: (single_price, cheapest_other_format_per_stick, in_stock)}"""
    out = {}
    for p in prods:
        sing, alt = None, []
        for v in p["variants"]:
            q = M.qty(v["title"])
            if not q or not v["available"]: continue
            try: price = float(v["price"])
            except Exception: continue
            if q == 1: sing = price
            else: alt.append(price / q)
        if sing is not None:
            out[p["title"]] = (sing, min(alt) if alt else None)
    return out

def seen_before(name, hist):
    """[(date, price)] for this exact cigar in previous runs of the promo."""
    n = norm(name)
    return [(d, items[k]) for d, items in hist for k in items if norm(k) == n]

def assess(name, price, own_alt, rows, idx, hist, tier):
    """Return (score, reasons[], rival) for one candidate at its best tier price."""
    t = toks(f"{name}{M.SEP}Single")
    paid = price * (1 - tier)
    rival = best_rival(t, "1", rows, idx) if len(t) >= XR_SHARED else None
    reasons, score = [], 0.0
    if rival:
        gap = paid / rival[1] - 1
        score += -gap * 100
        reasons.append(f"{gap:+.0%} vs ${rival[1]:,.2f} at {rival[2]} (in stock)")
    else:
        score += 4
        oos = best_rival(t, "1", rows, idx, in_stock=False) if len(t) >= XR_SHARED else None
        if oos:
            reasons.append(f"sole in-stock source; nearest listing {money(oos[1])} at "
                           f"{oos[2]} (out of stock)")
            if paid < oos[1]: score += 6
        else:
            reasons.append("no listing at all at the other seven")
    if own_alt:
        g = paid / own_alt - 1
        # box and single are normally the same per stick, so a gap equal to the tier
        # says nothing about this cigar. Only flag a box that is genuinely overpriced.
        if g < -tier - 0.03:
            score += (-g - tier) * 80
            reasons.append(f"beats iheart's own box/5-pack ({money(own_alt)}/stick) by {-g-tier:.0%} "
                           f"more than the discount")
        elif g > 0.02:
            score -= 10
            reasons.append(f"iheart's own box is cheaper per stick ({money(own_alt)})")
    prev = seen_before(name, hist)
    if prev:
        old = prev[-1][1]
        if abs(old - price) < 0.005:
            reasons.append(f"same list price in {len(prev)} previous run{'s' if len(prev)>1 else ''}")
        else:
            reasons.append(f"list was ${old:,.2f} on {prev[-1][0]} ({price/old-1:+.0%})")
            score += (old / price - 1) * 60
    else:
        reasons.append("first appearance")
        score += 3
    if INTEREST.search(name):
        score += 25                      # he collects these; a 20% cut on a line he
        score += min(price / 8.0, 10)    # wants beats a 38% cut on one he does not
        if not rival and price >= 30:
            score += 10
            reasons[-1] = reasons[-1]    # sole source on a collectible is the point
    return score, reasons, rival

def pick(cands, n):
    return sorted(cands, key=lambda c: -c["score"])[:n]

def money(x): return f"${x:,.2f}"

def render_burn(date, items, rows, idx, hist, label):
    tiers = PROMOS["burn"]["tiers"]
    cands = []
    for name, (price, own_alt) in items.items():
        sc, why, rival = assess(name, price, own_alt, rows, idx, hist, tiers[-1][1])
        cands.append(dict(name=name, list=price, score=sc, why=why, rival=rival,
                          t10=price * 0.9, t20=price * 0.8))
    L = [f"# {label} — {date}",
         f"{len(items)} in-stock singles · tiers: 5 sticks = 10% off, 10 sticks = 20% off",
         f"compared against 7 retailers, iheart's own formats, and {len(hist)} previous {label} runs"]
    for n, tier, key in ((10, "20%", "t20"), (5, "10%", "t10")):
        chosen = pick(cands, n)
        total = sum(c[key] for c in chosen)
        gross = sum(c["list"] for c in chosen)
        L.append(f"\n## Best {n} — the {tier} tier · {money(total)} (list {money(gross)})\n")
        L.append(f"| # | cigar | list | @{tier} | why |")
        L.append("|---|---|---|---|---|")
        for i, c in enumerate(chosen, 1):
            L.append(f"| {i} | {c['name'][:46]} | {money(c['list'])} | **{money(c[key])}** | "
                     + "; ".join(c["why"]) + " |")
    weak = [c for c in cands if c["rival"] and c["t20"] / c["rival"][1] - 1 > -0.02]
    if weak:
        L.append(f"\n## Priced at or above the market even after 20% ({len(weak)}) — skip")
        for c in sorted(weak, key=lambda c: -(c["t20"] / c["rival"][1]))[:8]:
            L.append(f"- {c['name'][:46]} — {money(c['t20'])} vs {money(c['rival'][1])} "
                     f"at {c['rival'][2]}")
    return "\n".join(L), {c["name"]: c["list"] for c in cands}

def render_madness(date, prods, rows, idx, hist, label, prev_state):
    moved = []
    for p in prods:
        for v in p["variants"]:
            k = f"iheart:{v['id']}"
            if k not in prev_state: continue
            try: now = float(v["price"])
            except Exception: continue
            was = prev_state[k][0]
            if was <= 0 or now >= was * 0.98 or not v["available"]: continue
            q = M.qty(v["title"])
            moved.append(dict(name=p["title"], variant=v["title"], was=was, now=now,
                              q=q, ps=(now / q) if q else None, cut=now / was - 1))
    cands = []
    for m in moved:
        if m["ps"] is None: continue
        t = toks(f"{m['name']}{M.SEP}{m['variant']}")
        cls = M.unitclass(m["q"])
        rival = best_rival(t, cls, rows, idx) if cls and len(t) >= XR_SHARED else None
        why, score = [f"{m['cut']:+.0%} on-site ({money(m['was'])} → {money(m['now'])})"], -m["cut"] * 60
        if rival:
            gap = m["ps"] / rival[1] - 1
            score += -gap * 100
            why.append(f"{gap:+.0%} vs {money(rival[1])}/stick at {rival[2]} (in stock)")
        else:
            score += 4
            oos = best_rival(t, cls, rows, idx, in_stock=False) if cls and len(t) >= XR_SHARED else None
            why.append(f"sole in-stock source; nearest {money(oos[1])} at {oos[2]} (out)"
                       if oos else "no listing at all at the other seven")
        prev = seen_before(m["name"], hist)
        if prev:
            why.append(f"also discounted on {prev[-1][0]} at {money(prev[-1][1])}")
            score += (prev[-1][1] / m["ps"] - 1) * 60
        else:
            why.append("first time discounted")
        if INTEREST.search(m["name"]): score += 12
        cands.append(dict(score=score, why=why, **m))
    L = [f"# {label} — {date}",
         f"{len(moved)} variants marked down on-site · these revert within ~24h",
         f"compared against 7 retailers and {len(hist)} previous {label} runs"]
    if not cands:
        L.append("\n**No markdowns detected this week.**")
        return "\n".join(L), {}
    for n in (10, 5):
        chosen = pick(cands, n)
        total = sum(c["now"] for c in chosen)
        # these are boxes and 5-packs, not a 5/10-stick tier - the total is only
        # what all of them together would cost, not a basket you have to buy
        L.append(f"\n## Top {n} picks · {money(total)} if you took every one\n")
        L.append(f"| # | cigar | was → now | per stick | why |")
        L.append("|---|---|---|---|---|")
        for i, c in enumerate(chosen, 1):
            L.append(f"| {i} | {c['name'][:42]} [{c['variant'][:14]}] | "
                     f"{money(c['was'])} → **{money(c['now'])}** | {money(c['ps'])} | "
                     + "; ".join(c["why"]) + " |")
    return "\n".join(L), {c["name"]: c["ps"] for c in cands}

# ------------------------------------------------------------------ main
def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PROMOS:
        print(__doc__); return 1
    promo = sys.argv[1]
    cached = sys.argv[sys.argv.index("--rivals") + 1] if "--rivals" in sys.argv else None
    cfg  = PROMOS[promo]
    date = datetime.date.today().isoformat()
    prods = collection(cfg["handle"])
    print(f"  {cfg['label']}: {len(prods)} products", file=sys.stderr)
    rows = rivals(cached); idx = indexed(rows)
    print(f"  rivals indexed: {len(rows)}", file=sys.stderr)
    hist = archive_load(promo, exclude=date)

    if promo == "burn":
        text, snap = render_burn(date, singles_and_alts(prods), rows, idx, hist, cfg["label"])
    else:
        prev = {}
        if os.path.exists(M.STATE):
            prev = json.load(gzip.open(M.STATE, "rt"))["v"]
        text, snap = render_madness(date, prods, rows, idx, hist, cfg["label"], prev)
    print(text)
    archive_save(promo, date, snap)
    with open(os.path.join(HERE, f"{promo}_findings.md"), "a") as f:
        f.write("\n\n---\n\n" + text + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
