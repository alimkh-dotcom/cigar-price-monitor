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
TAMPA   = os.path.join(HERE, "snapshots", "tampa.json.gz")
TAMPA_STALE_DAYS = 10   # weekly crawl; beyond this the prices are too old to cite

PROMOS = {
    "errors":  dict(handle=None, label="iheart pricing errors", tiers=[]),
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

# He prefers cigars that take less time. Smoke time tracks tobacco VOLUME, which
# goes as length x ring^2 - so ring gauge dominates and length alone misleads. A
# Hemingway Work of Art is 4 7/8 x 60: shorter than a robusto, yet 94% of a 6x50
# toro by volume, and it smokes for over an hour. Scoring on length, or on shape
# words like "perfecto" and "belicoso", called that one a quick smoke. Shape is
# not size.
#
# This is taste. The SMALL regex in monitor.py separately bars small formats from
# cross-retailer MATCHING, because a Coronet is not a Belicoso whatever he enjoys.
SMALLVIT = re.compile(r'entreacto|petit|demi[\s-]?tasse|half corona|coronet|'
                      r'short story|\bminutos?\b|chico|exquisito|panetela|'
                      r'\bcorona\b(?!.*(gorda|grande|larga))', re.I)
BIGVIT   = re.compile(r'toro|double corona|gran corona|lonsdale|salomon|presidente|'
                      r'churchill(?!.*petit)|\bgordo\b|magnum|double r\b', re.I)
DIMS     = re.compile(r'(\d+(?:\s+\d/\d|\.\d+)?)\s*[x×]\s*(\d{2})\b', re.I)

def smoke_size(name):
    """Tobacco volume in cubic inches if the title states dimensions, else None.

    Thresholds come from measuring 32,984 catalogue titles rather than guessing:
    the median toro is 6.00x52 = 3.11 cu.in (not the 6x50 = 2.88 assumed first),
    robusto 2.52, corona 2.18. So "short" is set below a typical corona.

    This is a plain cylinder and ignores shape - for a figurado it overstates by
    roughly a fifth. It is a ranking heuristic, not a burn-time model: a 7x48
    churchill and a 4 7/8x60 perfecto hold the same tobacco and do not take the
    same time, because a narrow ring burns slower."""
    m = DIMS.search(name)
    if not m:
        return None
    raw, rg = m.group(1).strip(), int(m.group(2))
    try:
        if "/" in raw:
            whole, frac = raw.split()
            num, den = frac.split("/")
            L = float(whole) + float(num) / float(den)
        else:
            L = float(raw)
    except (ValueError, ZeroDivisionError):
        return None
    if not (3 <= L <= 10 and 25 <= rg <= 70):
        return None
    return 3.14159 * ((rg / 128.0) ** 2) * L

# Wrapper words are identity, not noise. monitor.py drops "maduro" and "natural" as
# stop-words, which made "22 Minutes to Midnight Connecticut Radiante Robusto" a
# superset of "22 Minutes to Midnight Maduro Robusto" - a confident 39% gap between
# two different cigars. Put them back for matching, and treat a wrapper the other
# title lacks as a conflict, exactly like a vitola word.
WRAPPER = {"maduro","natural","connecticut","habano","corojo","criollo","sumatra",
           "rosado","oscuro","claro","colorado","cameroon","broadleaf","candela",
           "sungrown","shade","mexican","ecuador","ecuadorian","radiante","oro"}

def toks(s):
    raw = set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())
    return frozenset({w for w in M.matchtokens(s) if w not in HOUSE} | (raw & WRAPPER))

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
    # tampasweethearts, from its own weekly crawl. It is the Fuente family's shop,
    # so it matters most for exactly the lines Ali buys. It publishes no stock
    # status, so listings are taken as available - see tampa.py.
    try:
        t = json.load(gzip.open(TAMPA, "rt"))
        # age from the crawl timestamp inside the file - git clone resets mtime
        crawled = datetime.datetime.fromisoformat(t["ts"])
        age = (datetime.datetime.now(datetime.timezone.utc) - crawled).total_seconds() / 86400
        if age <= TAMPA_STALE_DAYS:
            n0 = len(rows)
            for name, fmt, price, q, _url in t["rows"]:
                add(f"{name}{M.SEP}{fmt or 'Default Title'}", price, q, "tampasweet", True)
            print(f"  tampasweet: +{len(rows)-n0} listings (crawled {t['ts'][:10]})",
                  file=sys.stderr)
        else:
            print(f"  tampasweet: cache {age:.0f} days old, skipped", file=sys.stderr)
    except (OSError, KeyError, ValueError):
        print("  tampasweet: no usable cache; run ./tampa.py", file=sys.stderr)
    return rows

def indexed(rows):
    idx = defaultdict(set)
    for i, r in enumerate(rows):
        for w in r[0]: idx[w].add(i)
    return idx

# Words that name or modify a vitola. If the longer of two titles adds one of these,
# the cigars are different sizes even though one title is a subset of the other:
# "Meir Robusto" is a subset of "Meir Master Blend Double Robusto", and "Winston
# Churchill Late Hour Churchill" collapses to the same token set as the Late Hour
# Petit Panetela once the brand's "Churchill" absorbs the vitola's. Both produced
# confident, wrong 58% gaps on the Oct 21 full scrape.
VITOLA = {"robusto","toro","churchill","corona","petit","petite","panetela","panatela",
          "lancero","belicoso","belicosos","torpedo","figurado","perfecto","piramide",
          "double","gordo","gran","grande","short","half","lonsdale","salomon","salomones",
          "presidente","magnum","gigante","chico","culebra","diadema","perfecxion",
          "entreacto","demi","tasse","minuto","especial","no","especiales","toro"}

def vitola_conflict(a, b):
    """True if the larger title adds a size or wrapper word the smaller one lacks."""
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    return bool((big - small) & (VITOLA | WRAPPER))

def best_rival(t, cls, rows, idx, in_stock=True):
    cand = defaultdict(int)
    for w in t:
        for i in idx.get(w, ()): cand[i] += 1
    out = None
    for i, sh in cand.items():
        ot = rows[i][0]
        if sh < XR_SHARED or not (t <= ot or ot <= t): continue
        if vitola_conflict(t, ot): continue
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
            score += 10                  # sole source on a collectible is the point
    vol = smoke_size(name)
    if vol is not None:                  # stated dimensions beat any guess from words
        if vol <= 2.0:
            score += 8
            reasons.append(f"short smoke, ~{vol:.1f} cu.in against 3.1 for a toro")
        elif vol >= 2.9:
            score -= 4
    elif SMALLVIT.search(name) and not BIGVIT.search(name):
        score += 8
        reasons.append("shorter than a toro")
    elif BIGVIT.search(name):
        score -= 4
    return score, reasons, rival

def pick(cands, n, dedupe=None):
    """Top n by score. With dedupe, at most one entry per cigar - the Sixto I box
    and the same box in tubos are not two picks, they are one cigar twice."""
    out, seen = [], set()
    for c in sorted(cands, key=lambda c: -c["score"]):
        k = norm(c[dedupe]) if dedupe else id(c)
        if k in seen: continue
        seen.add(k); out.append(c)
        if len(out) == n: break
    return out

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
        chosen = pick(cands, n, dedupe="name")
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

MAX_CUT = 0.60      # deeper than this and compare_at_price is a data-entry slip,
                    # not a sale: the Late Hour "Box of 4" carries the Box of 20's
                    # compare_at, which reads as -79% off

def markdowns(prods, prev_state):
    """Discounted variants, preferring Shopify's own compare_at_price.

    Diffing against snapshots/state.json.gz alone was wrong: monitor.py runs first
    and rewrites that baseline WITH the sale prices in it, so by the time this ran
    there was nothing left to see. It reported "no markdowns" through a live sale.
    compare_at_price is the shop's own before-price and needs no baseline, so it
    holds whatever order things run in.
    """
    out = []
    for p in prods:
        for v in p["variants"]:
            if not v["available"]: continue
            try: now = float(v["price"])
            except (TypeError, ValueError): continue
            was, src = None, None
            cap = v.get("compare_at_price")
            if cap:
                try: cap = float(cap)
                except (TypeError, ValueError): cap = None
            if cap and cap > now and (now / cap - 1) >= -MAX_CUT:
                was, src = cap, "compare_at"
            else:
                prior = prev_state.get(f"iheart:{v['id']}")
                if prior and prior[0] > now * 1.02:
                    was, src = prior[0], "vs last run"
            if not was: continue
            q = M.qty(v["title"])
            out.append(dict(name=p["title"], variant=v["title"], was=was, now=now, src=src,
                            q=q, ps=(now / q) if q else None, cut=now / was - 1))
    return out

def render_madness(date, prods, rows, idx, hist, label, prev_state):
    moved = markdowns(prods, prev_state)
    cands = []
    for m in moved:
        if m["ps"] is None: continue
        t = toks(f"{m['name']}{M.SEP}{m['variant']}")
        cls = M.unitclass(m["q"])
        rival = best_rival(t, cls, rows, idx) if cls and len(t) >= XR_SHARED else None
        why = [f"{m['cut']:+.0%} on-site ({money(m['was'])} → {money(m['now'])}, {m['src']})"]
        score = -m["cut"] * 60
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
        chosen = pick(cands, n, dedupe="name")
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


# ------------------------------------------------------------------ pricing errors
# The detector that was missing. Everything else here reports CHANGE, so an error
# that predates the first snapshot stays invisible forever: the AJ Fernandez Dorado
# Figurado sat at half its own box price and half the market from 2026-09-17 to at
# least 10-21 without one mention. This compares every in-stock iheart price to the
# market directly, whatever its history.
#
# Raw gaps mislead because retailers carry systematic markups, and not uniformly:
# measured on the 10-21 scrape, cigarsdirect runs 1.41x iheart on Fuente/OpusX but
# 0.98x on everything else, while tccigar and tampasweet sit ~10% under on both. So
# each rival price is first divided by that site's measured premium for the brand
# group, recomputed every run, and only what survives that counts.
FUENTE    = re.compile(r'opus|fuente|don carlos|hemingway|a[nñ]ejo|rare pink|destino|'
                       r'8-5-8|chateau|casa fuente', re.I)
ERR_LIKELY, ERR_CHEAP = 0.60, 0.75        # of the premium-adjusted cheapest rival
ERR_MIN_SAVING = 0.20                     # and a real saving vs the cheapest place to buy

def site_premiums(cur, names, rows, idx):
    """{(site, group): median rival/iheart price ratio}, same unit class, in stock."""
    import statistics
    acc = defaultdict(list)
    for k, (p, a, q) in cur.items():
        if not k.startswith("iheart:") or not a or not q: continue
        full = names[k]
        if M.NONCIGAR.search(full) or M.BUNDLE.search(full) or M.SMALL.search(full): continue
        t, cls = toks(full), M.unitclass(q)
        if not cls or len(t) < XR_SHARED: continue
        grp = "fuente" if FUENTE.search(full) else "other"
        cand = defaultdict(int)
        for w in t:
            for i in idx.get(w, ()): cand[i] += 1
        best = {}
        for i, sh in cand.items():
            ot, ps, site, _l, c, av = rows[i]
            if sh < XR_SHARED or not (t <= ot or ot <= t) or vitola_conflict(t, ot): continue
            if c != cls or not av: continue
            if site not in best or ps < best[site]: best[site] = ps
        for site, ps in best.items():
            acc[(site, grp)].append(ps / (p / q))
    return {k: statistics.median(v) for k, v in acc.items() if len(v) >= 5}

def find_errors(cur, names, rows, idx):
    prem = site_premiums(cur, names, rows, idx)
    hits = {}
    for k, (p, a, q) in cur.items():
        if not k.startswith("iheart:") or not a or not q: continue
        full = names[k]
        if M.NONCIGAR.search(full) or M.BUNDLE.search(full) or M.SMALL.search(full): continue
        t, cls = toks(full), M.unitclass(q)
        if not cls or len(t) < XR_SHARED: continue
        r = best_rival(t, cls, rows, idx)
        if not r: continue
        grp = "fuente" if FUENTE.search(full) else "other"
        fair = r[1] / prem.get((r[2], grp), 1.0)
        ratio = (p / q) / fair
        saving = 1 - (p / q) / r[1]            # what he actually saves, unadjusted
        if ratio > ERR_CHEAP or saving < ERR_MIN_SAVING: continue
        title, var = full.split(M.SEP)[0], (full.split(M.SEP) + [""])[1]
        if title not in hits or ratio < hits[title]["ratio"]:
            hits[title] = dict(ratio=round(ratio, 3), saving=round(saving, 3), variant=var,
                               price=p, q=q, ps=round(p / q, 2), rival=round(r[1], 2),
                               site=r[2], fair=round(fair, 2))
    return hits, prem

def render_errors(date, hits, prem, archive):
    new   = {t: h for t, h in hits.items() if t not in archive}
    still = {t: h for t, h in hits.items() if t in archive}
    gone  = [t for t in archive if t not in hits]
    L = [f"# iheart pricing errors — {date}",
         f"{len(hits)} live · {len(new)} new · {len(gone)} fixed since last run",
         "rival prices are adjusted for each site's measured markup before comparing"]
    def line(t, h, first=None):
        tag = "**likely error**" if h["ratio"] <= ERR_LIKELY else "unusually cheap"
        since = f" · live since {first}" if first else ""
        star = " ★" if INTEREST.search(t) else ""
        return (f"- {tag}{star} — {t} [{h['variant']}] **{money(h['ps'])}/stick**, "
                f"**{h['saving']:.0%} under** the cheapest in stock ({money(h['rival'])} at "
                f"{h['site']}){since}")
    if new:
        L.append(f"\n## New ({len(new)})")
        L += [line(t, h) for t, h in sorted(new.items(), key=lambda x: x[1]["ratio"])]
    if still:
        L.append(f"\n## Still live ({len(still)})")
        L += [line(t, h, archive[t]["first_seen"]) for t, h in
              sorted(still.items(), key=lambda x: x[1]["ratio"])]
    if gone:
        L.append(f"\n## Fixed or gone ({len(gone)})")
        L += [f"- {t} (live {archive[t]['first_seen']} → {archive[t]['last_seen']})" for t in gone]
    return "\n".join(L), new, gone

# ------------------------------------------------------------------ main
def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PROMOS:
        print(__doc__); return 1
    promo = sys.argv[1]
    cached = sys.argv[sys.argv.index("--rivals") + 1] if "--rivals" in sys.argv else None
    cfg  = PROMOS[promo]
    date = datetime.date.today().isoformat()
    if promo == "errors":
        src = cached or fresh_cache()
        if not src:
            raise SystemExit("ABORT: errors needs monitor.py's fresh pull (snapshots/rivals.json.gz)")
        live = json.load(gzip.open(src, "rt")); cur, nm = live["cur"], live["names"]
        rows = rivals(src); idx = indexed(rows)
        hits, prem = find_errors(cur, nm, rows, idx)
        path = os.path.join(ARCHIVE, "errors.json")
        archive = json.load(open(path)) if os.path.exists(path) else {}
        text, new, gone = render_errors(date, hits, prem, archive)
        for t, h in hits.items():
            archive.setdefault(t, {"first_seen": date})
            archive[t].update(last_seen=date, **h)
        for t in gone: archive.pop(t, None)
        os.makedirs(ARCHIVE, exist_ok=True)
        json.dump(archive, open(path, "w"), indent=1, sort_keys=True)
        print(text)
        if new or gone:                      # quiet unless something changed
            with open(os.path.join(HERE, "errors_findings.md"), "a") as f:
                f.write("\n\n---\n\n" + text + "\n")
        return 0
    prods = collection(cfg["handle"])
    print(f"  {cfg['label']}: {len(prods)} products", file=sys.stderr)
    rows = rivals(cached); idx = indexed(rows)
    print(f"  rivals indexed: {len(rows)}", file=sys.stderr)
    hist = archive_load(promo, exclude=date)

    if promo == "burn":
        items = singles_and_alts(prods)
        # The burn is a checkout tier, so the list price never moves and there is no
        # price signal for "a new collection dropped". The only signal is the roster
        # itself. Rather than guess the drop time, report when the roster changes.
        prior = archive_load(promo)                      # includes today, if re-run
        if prior:
            pd, pitems = prior[-1]
            a, b = {norm(k) for k in items}, {norm(k) for k in pitems}
            same = len(a & b) / max(1, len(a | b))
            if same >= 0.80:
                print(f"# {cfg['label']} — {date}\n\nSame collection as {pd} "
                      f"({same:.0%} identical). No new burn to report.")
                return 0
        text, snap = render_burn(date, items, rows, idx, hist, cfg["label"])
    else:
        prev = {}
        if os.path.exists(M.STATE):
            prev = json.load(gzip.open(M.STATE, "rt"))["v"]
        text, snap = render_madness(date, prods, rows, idx, hist, cfg["label"], prev)
    print(text)
    # A quiet run is not a run. Archiving an empty roster inflated the "N previous
    # runs" count that the reasoning leans on, and appending "no markdowns" to the
    # log buried the real reports.
    if snap:
        archive_save(promo, date, snap)
        with open(os.path.join(HERE, f"{promo}_findings.md"), "a") as f:
            f.write("\n\n---\n\n" + text + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
