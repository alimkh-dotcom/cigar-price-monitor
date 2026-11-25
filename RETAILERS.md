# Retailer quirks

Apply these before calling any finding real. The Routine reads this file on every
run, so correcting a retailer is a commit here, not a rewrite of the Routine
prompt. Date every measurement.

The tracked set: **eight Shopify shops** (iheart, tccigar, mrbundles, jackschwartz,
gtcigars, cigarsdirect, sunofagun, tobaccoreserve) plus luxurycigarclub, Tampa
Sweethearts and Tobacconist of Greenwich.

## Shipping — check this FIRST when evaluating any shop

**Ali is in New York.** A shop that will not ship there is worth nothing to him
whatever its prices, so confirm it before measuring anything else. Published
exclusions, read 2026-11-24:

| shop | will not ship to |
|---|---|
| iheart | Utah, Hawaii (and P.O. boxes) |
| tccigar | Alaska, Hawaii, Maine, South Dakota, Utah, Washington, Wisconsin |
| mrbundles | Hawaii |
| gtcigars | Utah, Hawaii |
| Tampa Sweethearts | Hawaii, Puerto Rico, South Dakota, Utah |
| sunofagun | nothing published; has a "Cigars Shipped to New York City" page |
| jackschwartz, cigarsdirect, tobaccoreserve | nothing published found |

**None of them exclude New York.** The policy pages are often silent, so silence
is not confirmation — but no tracked cigar shop is known to refuse NY.

**parkplaza (Park Plaza Liquor) was added 2026-11-23 and removed 2026-11-24
because it does not ship to New York.** It is a liquor store, which is very likely
why — alcohol shipping is licensed state by state and NY is restrictive. Nothing
on its shipping-policy page says so; Ali found out himself. Its catalogue was
genuinely good (3,016 cigars, 80% in stock, median 1.052x on 620 matches, the only
in-stock Black Pink at a sane price), so **if it ever ships to NY it is worth
re-adding** — that is one line back into `sites.json`, since the `CIGAR_ONLY`
whitelist and `variant_qty()` it needed are still in `monitor.py`, marked dormant.

## The traps that have produced bad findings

- **Inflated base.** A percentage off `compare_at_price` is meaningless if
  `compare_at` is fabricated. Divide the sale price by the pack count and compare
  it against the SAME product's single and 5-pack at that retailer. If the
  discounted box costs more per stick than the single, it is not a deal. Common at
  iheart: OpusX OXO Oro Oscuro Robusto box of 29 "25% off" works out to
  $45.62/stick against a $42.00 single; several Davidoff `Box of 4` SKUs carry
  `compare_at` implying 66-84% off when the price is exactly 4x the single;
  Rare Pink Signature box of 5 at $185.00 is $37.00/stick against its own $32.80
  single. Same on iheart's "Stick or Switch" game: Destino Siglo de Amor box of 13
  at "25% off $650" is $37.50/stick against a $44.00 single, and iheart's own
  Monday Madness sold that cigar at $35.20/stick on 2026-11-09.
- **Samplers carry the same trap, usually worse.** Always price one against its
  components as in-stock singles. cigarsdirect's 2026 God of Fire KKP 4-Cigar
  Sampler is $395.00 against $204.00 for the same four singles at tobaccoreserve.
- **Combo packs are not one cigar.** "OpusX Belicoso XXX + E.P. Carrillo" at
  $20.90/stick and "Casa Cuba Doble Tres + Añejo Reserva" at $12.00/stick are two
  different cigars in a tin; the per-stick is not comparable to a single.
- **Small formats are not the parent cigar.** Papas Fritas, Papas Bravas, Coronets,
  Petit/Petite, Ponies, Cubanitos, Juniors, cigarillos, tins. Rare Pink Short Story
  is the small vitola in that line. **Exception:** Byron Petit Poemas is a line
  name in its own right, not a small format of Poemas.
- **`Default Title` variants** have no reliable stick count, except at parkplaza
  where `variant_qty()` derives it from `product_type` plus the product title.
- Verify anything that looks too good against that retailer's raw /products.json
  (or, for Greenwich, the product page) before reporting it.

## **Matching is weaker than it looks — read this before claiming "sole source"**

The cross-retailer matcher requires near-identical distinctive tokens
(`XR_MATCH` 0.90). Shops name the same cigar differently, so it misses matches and
then reports the item as unique. **This has produced false findings three times.**

- **House prefixes.** iheart sells "Rare Pink **Vintage 1960's** Short Story";
  everyone else sells "**Arturo Fuente** Rare Pink Short Story". Jaccard 0.50, so
  on 2026-11-20 the Weekly Burn reported it as "no listing at all at the other
  retailers" while tccigar had it in stock at $18.25, under the $20.64 tier price.
  Same shape: tobaccoreserve's "Opus X Don Carlos Edicion de **Anniversario**" vs
  everyone else's "Arturo Fuente Don Carlos Edicion de **Aniversario**".
- **Omitted vitolas.** tobaccoreserve lists "Atabey Hechizos"; everyone else lists
  "Atabey Hechizos **Petit Corona**". Same cigar. Those two-token titles also fall
  below the three-distinctive-token floor, so they are never fuzzy-matched either.
- **Unit class.** A comparison restricted to singles will miss a rival's in-stock
  5-pack entirely. On 2026-11-23 that led to calling parkplaza the first Black Pink
  source in the set when sunofagun, tccigar and cigarsdirect had all carried it for
  weeks.

**So: never present "no match at the other shops" as evidence a shop is the only
source, or as a reason to buy there. Check the brand and line by hand, across all
pack sizes, before saying it.** The 2026-11-17 claim that tobaccoreserve had "53
unique in-stock variants" was about double the truth; re-measured it is ~28 on the
same brand set, ~36 including God of Fire.

## Per-retailer

- **iheart** — the promo engine (Monday Madness, Weekly Burn, Stick or Switch) and
  the inflated-`compare_at` source above. Its "Discontinued" Davidoffs carry a
  vintage premium.
- **cigarsdirect — high outlier on scarce Fuente.** Measured 2026-10-21: ~1.41x
  iheart on Fuente, ~0.98x on everything else; on Davidoff it is priced normally
  and often cheapest. A big "% under cigarsdirect" on a Fuente usually means they
  are overpriced. **God of Fire is a Fuente/Prometheus collaboration so the caveat
  applies there too — except on the four core God of Fire lines, where cigarsdirect
  really is cheapest in the set.** Worked example 2026-11-13: sunofagun's Rare Pink
  Queen of Hearts 5-pack showed "-43% vs cigarsdirect" at $36.99/stick, but Tampa
  sells it at $22.59 — sunofagun was 64% OVER the market, not under.
- **Greenwich** — ~7% under iheart on Fuente/OpusX, level elsewhere (2026-10-23).
  Its OXO Oro Oscuro 5-packs at $29-31/stick against iheart's $36-49 are normal
  pricing, not an error. Honours a 10s crawl delay; do not shorten it.
- **Tampa Sweethearts** — consistently the cheapest Rare Pink: Mini Box of 5 Short
  Story $64.95, Signature $83.95, Work of Art $85.95, Queen of Hearts $112.95
  (2026-11-09). Normal prices, not errors. **Rank Tampa on price like any other
  retailer.** No machine-readable stock field, so do NOT demote it for "unknown
  stock" — that under-ranks the cheapest source on Ali's main watch line. Treat
  **catalogue presence as the stock proxy**: a product that disappears between
  weekly crawls has almost certainly sold out, one that reappears is a restock
  worth reporting. Rare Pink Happy Ending Mini Box appeared 2026-10-28 and was gone
  by 2026-11-09; Signature had gone by 2026-11-19. `snapshots/tampa.json.gz` is a
  dict `{ts, rows}`, not a bare list.
- **sunofagun (added 2026-11-13)** — ~3,765 cigar variants, **85% in stock**,
  highest availability in the set. Baseline 2026-11-13 on 882 matches: median
  **1.062x** the cheapest rival, **1.029x** on Ali's lines; cheapest of anyone on
  32%, 15%+ dearer on 30%. A breadth source, not a discounter. **Deepest source for
  Byron (56 variants / 45 in stock) and cheapest on every Atabey single.** Wins on
  Davidoff BOXES (Grand Cru Toro $26.07/stick, -19%; Millennium Robusto $25.23,
  -18%). Expensive on everyday small Fuente (Exquisitos Maduro +74%). Best Padrón
  (184) coverage, joint-best Davidoff (187). **No Meerapfel.**
- **tobaccoreserve (added 2026-11-17)** — small but concentrated: 198 cigar
  products, 526 variants, 66% in stock. Baseline 2026-11-17 on 101 matches: median
  **1.055x**, cheapest on 38%. A high-end Fuente/OpusX/Atabey/God of Fire
  specialist.
  - **Why it is here: 64 God of Fire variants, all 64 in stock, the best
    availability in the set**, and cheapest on KKP — a flat $49.50 for Gran Toro 56,
    Piramide 58, Toro Extra 54 and Diadema 60; $52.50 Diadema 56, $55.00 Diadema 54.
    On Serie B, Don Carlos, Carlito and Aniversario it is the dearest (median 1.14x)
    and cigarsdirect is cheapest. Route by line.
  - **Not a reason to buy Atabey**: cheapest on **0 of 12** Atabey singles, a flat
    10-14% over sunofagun on every one.
  - Pack pricing is honest — "5-Pack — Save 5%" and "Box of 10 — Save 10%" and the
    arithmetic matches. No fabricated `compare_at`.
  - **Zero Rare Pink, zero Liga Privada, zero Meerapfel**, only 7 Davidoff products.
  - It omits vitolas from titles (see matching, above) and prefixes several Arturo
    Fuente lines with "Opus X", which looks like a mislabel.
  - `PRE-ORDER — ` titles are pre-orders listed as `available: true`. Ali wants them
    reported, but **say plainly that an item is a pre-order**.
- **parkplaza (added 2026-11-23)** — a liquor store with a serious cigar
  department: 5,790 products, **3,016 cigars, 80% in stock**, fourth-largest cigar
  catalogue in the set. 25% of it (747 products) is in Ali's lines. Baseline
  2026-11-23 on **620** head-to-head in-stock singles, the largest sample measured
  for any shop: median **1.052x**, cheapest of anyone on **36%**, 15%+ dearer on
  16% — better than sunofagun.
  - **Cheapest Rare Pink singles anywhere**, and the only shop with **Black Pink in
    stock** at a sane price (see INTERESTS.md).
  - **No Atabey, Byron, God of Fire or Meerapfel.** 33 Davidoff singles in stock
    from $13.50 — good breadth, not cheapest.
  - Two integration quirks, both handled in `monitor.py` and both worth knowing:
    its ~2,774 wine/bourbon/beer/scotch listings are excluded by the `CIGAR_ONLY`
    whitelist rather than the `NONCIGAR_TYPE` blacklist, which they do not match;
    and every product has one `Default Title` variant with the pack count in the
    PRODUCT title, so `variant_qty()` derives the count and moves it into the
    variant label.
- **federalcigar.com — evaluated 2026-11-24, NOT added.** WooCommerce (Store API
  open, robots.txt fine), 173 products / 723 variations, 100% in stock, 32% of it
  in Ali's lines, ships to NY (only Hawaii and Utah excluded), free shipping over
  $175, NH tax-free. Rejected on price: **median 1.106x the cheapest tracked rival
  and cheapest of anyone on only 22%** — the worst baseline measured, against
  sunofagun 1.062x/32% and tobaccoreserve 1.055x/38%. Its apparent Rare Pink
  "wins" are all against cigarsdirect, the Fuente outlier; read against Tampa it
  loses on four of six vitolas. Atabey is dearer than sunofagun on every size with
  no pack discount at all. No Black Pink, 2 OpusX products. Being WooCommerce it
  would need a bespoke scraper plus a variation call per product — not worth it.
  **Worth a MANUAL check for two things only:** Rare Pink Happy Ending 5-pack
  ($119.75, $23.95/stick, cheapest anywhere) and Sophisticated Hooker box of 20
  ($691.50, $34.58/stick, best per-stick anywhere). Ali passed on both on
  2026-11-24, preferring Tampa's Sampler IV.
- **User agent and pacing — do not revert.** Every script sends `monitor.UA`
  (`cigar-price-monitor/1.0`). They used to send `Mozilla/5.0`, and on 2026-11-25
  both promo scripts failed twice against an iheart bot interstitial ("Verifying
  your connection..."). Claiming to be a browser while firing rapid identical
  requests is exactly what a bot filter targets, and it was dishonest besides.
  `promos.collection()` also paged a collection five times back-to-back with no
  delay while `monitor.py` has always slept 1.5s between pages with the comment
  "iheart 429s without this"; it now paces the same way, and `lux_products()`
  sleeps 1s. **Never put anything identifying Ali in the user agent.**
  `monitor.CHALLENGE` detects a challenge page so it is reported as a block
  rather than an opaque parse error. **If it fires, the shop is refusing
  automated access: stop and report it. Do not try to answer or defeat it.**
- **Bot-protected, do not retry and never work around a challenge:** CigarPage and
  Regency Cigar (Cloudflare managed challenge, covering even /robots.txt), JR
  Cigars (Imperva).
- **Not in the set:** Famous, Cigars International, Atlantic, JR, Neptune, Nice Ash,
  Holts. Ali buys from Neptune himself. **Never claim a cigar is scarce or
  unavailable on the strength of this set alone** — say "cheapest among the
  retailers we track" and check the open web before calling anything hard to find.

## Non-cigar filtering

Two layers. `NONCIGAR_TYPE` matches Shopify `product_type` only — never the title,
because cigar lines are routinely named after spirits (Diesel Whiskey Row, Perdomo
Bourbon Barrel-Aged, M Bourbon by Macanudo, Tatiana Rum, Punch Bottle Rocket,
Kentucky Cheroots Bourbon RamRod). `NONCIGAR` matches titles for accessories, and
includes "watch winder", "box only" and `\bno cigars\b` to catch the Prometheus and
OpusX display pieces that carry a cigar brand. **The word boundary on
`\bno cigars\b` must not be removed** — without it the pattern matches inside
"25 Premium Habano Cigars (Naked Bundle)" and drops five real cigars.

tccigar tags almost nothing, so its accessories rely entirely on the name regex.
If a whisky, an ashtray or an empty humidor reaches a report, say so — a filter has
a gap — and do not present it as a cigar deal.
