# Cigar price monitor

Twice-daily diff of six Shopify cigar catalogs (~25,800 variants). Reports only what
changed and is worth acting on — deliberately not a full anomaly scan.

## Why a diff and not a scan

Snapshot anomaly scans reliably surface *expensive* errors (a box priced above its own
single) and reliably miss *cheap* ones. Underpriced listings get bought out or corrected
within days, so a weekly scan arrives after they are gone.

Measured over 12 days of snapshots from one retailer: a mispriced 5-pack (Liga Privada
H99 Super Ancho — $69 for a cigar selling at $22.85/stick) was **corrected in 4 days**,
while three overpriced box listings sat untouched for **12+ days**, and a new one appeared
mid-window.

Every genuinely cheap find came from a *change* between two pulls, never from a single
snapshot. Hence: diff, twice a day.

## Usage

    ./monitor.py     # scrape, diff against last run, print report, append findings.md

~3 minutes. Exit 0 normally, 2 if a catalog could not be fetched.

## Signals

| signal | trigger |
|---|---|
| **DROP** | price fell ≥20% (≥35% flagged **BIG**) |
| **NEW PRODUCT** | a product that was not in the last pull — reported unconditionally |
| **NEW VARIANT** | a new variant on a product already tracked — reported unconditionally |
| **RESTOCK** | an out-of-stock variant returned at ≤70% of its product's next tier |
| **CROSS** | a new or just-dropped listing ≥25% per stick under the same cigar elsewhere |
| **BREAK** | a variant jumped ≥20% and is now ≥15% above its own cheapest sibling |

Thresholds are constants at the top of `monitor.py`.

New listings are reported whatever they cost. The earlier version only surfaced one that
undercut its own product's next tier, which silently dropped every single-variant product
and every new line priced normally — that is, most genuinely new arrivals. Items that *do*
undercut their own line still carry the `% of its next tier` note, and accessories are
filtered out.

### Cross-retailer matching

Only runs on listings that just changed, and refuses to guess:

- both sides in stock, both with a stated cigar count, compared per stick
- **singles match only singles, multipacks only multipacks.** A box is supposed to cost
  less per stick than a single; that gap is the shape of the market, not a mispricing
- titles must share ≥90% of their distinctive words (Jaccard), with ≥3 such words. The
  variant label is tokenised too — GT and tccigar put the vitola there, and matching on
  the product title alone read *Winston Churchill Petit Panetela* as plain *Churchill*
- numbers are kept in product titles: `858`, `No.5` and `Fifty Five` are what separate
  one cigar from another. Stripping them matched *Perfecxion No.5* to *No.4*
- samplers, collections, gift packs, accessories and small formats (Papas Fritas,
  Coronets, Petit/Petite, cigarillos, Cubanitos, Juniors) are excluded from matching
  entirely; a Coronet tin read against a Belicoso box produced a run of bogus 60%
  "discounts" in manual analysis

Tuning was empirical: a full-catalogue sweep at the first thresholds returned 49 gaps of
which roughly four were real — the rest were vitola confusions and box-vs-single pairs.
The rules above bring the same sweep to 14, with no false positive identifiable by hand.

Findings are still labelled **unverified** — the matcher cannot see vitola differences the
titles don't state, so check the actual cigar before buying. Note also that most gaps mean
the *other* retailer is expensive, not that this one is a steal.

## Files

| file | purpose |
|---|---|
| `sites.json` | domain per site — add a Shopify store here to track it |
| `monitor.py` | the whole pipeline |
| `snapshots/state.json.gz` | last run's prices, names stripped (~212 KB) |
| `findings.md` | append-only log of every report |

Only `state.json.gz` persists between runs; product names come from the live pull.

## Notes

- Per-stick figures appear only where the variant label states a count. `Default Title`
  and similar are tracked but never assigned a quantity — guessing there produced false
  60%+ "discounts" in earlier manual passes.
- `monitor.py` retries each page 6× with backoff and **aborts without touching state** if
  any catalog comes back incomplete; a truncated pull would otherwise read as thousands of
  delistings.
- A 1.5 s pause between pages is required — at least one retailer rate-limits without it.

## Data

Everything here is derived from public `/products.json` endpoints. No credentials, no
account data.

## Promo analysis — `promos.py`

    ./promos.py burn        # Weekly Burn, 10% at 5 sticks / 20% at 10 sticks
    ./promos.py madness     # Monday Madness, on-site markdowns that revert

Neither is scheduled against a guessed drop time — both detect their own promo.
`madness` finds an empty collection except during the sale. `burn` compares the
roster against the last archived one and stays quiet until it changes by more
than 20%. Run them as often as you like; they report once per new promo.

Both produce a **best 5** and a **best 10** with a stated reason per pick, drawn from
three comparisons: the other seven retailers (per stick, in stock), iheart's own other
formats for the same cigar, and every previous run of that promo in `archive/`.

### What the two promos actually are

Measured over 20 twice-daily snapshots, they behave completely differently:

| | Weekly Burn | Monday Madness |
|---|---|---|
| mechanism | checkout tier, list price unchanged | real on-site markdown |
| duration | the week's collection | **~24h, then reverts** |
| price stability | 0 of 99 singles moved in 9 days | 76 of 172 variants moved |
| when it is live | roster changes weekly, no price signal | one observed window, below |

Across 19 consecutive twice-daily snapshots (2026-09-17 to 09-25) exactly one
carried a markdown: **2026-09-22T00:01 UTC, 62 price cuts**, still in place at
12:22 UTC the same day, all 67 restored by 09-23T00:14 UTC. In US Eastern that
is live Monday evening through Tuesday, gone by Tuesday evening — so two
consecutive runs see it. No Friday snapshot showed any price change at all,
which is exactly what a checkout-tier promo looks like from the outside.

That is a single observed Monday. The window above is measured, not assumed,
but one week is one week.

Across three burns, 21 of 22 repeat cigars carried an identical list price. iheart does
not mark up before a burn — the discount is the entire edge. Monday Madness is the
opposite: the price genuinely drops and genuinely goes back up the next day.

### Matching rule

A rival only counts when one title's distinctive words are a **superset** of the other's,
with at least 3 shared. An overlap score, however tuned, kept pairing Rojo with Morado,
Corona Edwardian with Edwardian Robusto and Skinny Monsters Frank with Drac. Requiring a
superset means neither side may contradict the other.

Singles only match singles and multipacks only multipacks; samplers, accessories and small
formats are excluded. Out-of-stock listings never drive a pick — they appear only as
context ("sole in-stock source; nearest listing $50.40 at tccigar, out of stock"), because
a price you cannot act on is not a price.

`archive/<promo>/<date>.json` accumulates every run, which is what powers the
"same list price in N previous runs" and "list was $X on <date>" reasoning. The
2026-09-11 burn was reconstructed from truncated names, so a few of its entries will not
match later runs exactly.
