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
