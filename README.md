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
| **RESTOCK** | an out-of-stock variant returned at ≤70% of its product's next tier |
| **NEW** | a newly listed variant already at ≤70% of its product's next tier |
| **BREAK** | a variant jumped ≥20% and is now ≥15% above its own cheapest sibling |

Thresholds are constants at the top of `monitor.py`.

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
