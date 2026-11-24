# Ali's interests

The volatile half of the monitoring brief. The Routine reads this file on every
run, so changing what gets reported is a commit here — not a rewrite of the
Routine prompt. Keep it current; date every claim.

Last confirmed with Ali: **2026-11-17**.

## Hard constraint: it must ship to New York

**Ali is in NY. A retailer that will not ship there is worth nothing to him, at
any price.** Check this BEFORE evaluating a shop's catalogue, not after — on
2026-11-23 parkplaza was added, measured and recommended over two sessions before
this came up, and it had to be removed. See RETAILERS.md for the published
exclusions of every tracked shop; none of them exclude NY, which is why this never
surfaced until a liquor store joined the set.

## Brands

**Strong — report anything.** OpusX (especially Heaven & Earth), Arturo Fuente
(Don Carlos, Hemingway, Añejo, Rare Pink, Destino al Siglo), Padrón, Davidoff,
Atabey, Byron, God of Fire, Plasencia (Alma Fuerte, Alma del Cielo).

**Weaker — report only on a real outlier.** Ashton ESG/VSG, Meerapfel, Liga
Privada. On Liga he has said "I have a lot of h99", so treat **H99 as LOW
marginal interest** unless the price is exceptional, even though it shows up in
nearly every Monday Madness.

**Dropped.** Alfonso, removed 2026-11-17 — only two lines (Gran Selección and
Extra Añejo), so no discovery project in it, and he buys it from Neptune, which
is not a tracked retailer. It is out of the `INTEREST` regex in `promos.py`.
Do not re-add without asking.

He wants pricing errors and outliers, not routine markdowns.

## Format

**He buys singles, 5-packs and samplers.** One full box, ever (Plasencia Alma
del Cielo). A box of 10+ is low interest unless the per-stick price is
extraordinary or it is a line he has already committed to. A 5-pack at a modest
discount beats a box at a deep one. **Never headline a box when a single or
5-pack of the same cigar exists.** Confirmed purchases: a Fuente Toast Across
America sampler, a Padrón sampler, an Alma del Cielo box, a lot of Liga H99.

**Price every sampler against its components as in-stock singles before calling
it a deal.** Markups are routinely severe — cigarsdirect's 2026 God of Fire KKP
4-Cigar Sampler is $395.00 against $204.00 for the same four singles at
tobaccoreserve.

## Live projects

### Davidoff, one vitola at a time (started 2026-11-13)
Prioritise **single-stick availability and vitolas he has not been shown
before** over per-stick price. Cheapest in-stock singles as of 2026-11-13:
Winston Churchill Belicoso $10.80 (jackschwartz — 27 vitolas in stock, widest
selection), Late Hour Belicoso $12.40 (iheart), Aniversario Entreacto $14.40
(cigarsdirect), Signature 1000 $15.40 (iheart), Grand Cru No.5 $16.40
(cigarsdirect). sunofagun wins Davidoff on BOXES, not singles; tobaccoreserve's
Davidoff list is thin (7 products). Point him at cigarsdirect / iheart /
jackschwartz for singles.

### God of Fire, one of each line (started 2026-11-17)
Six blends: Serie B, By Don Carlos, By Carlito, Serie Aniversario (the 10th
Anniversary series), KKP Never Back Down, KKP Special Reserve.

**No sampler anywhere covers all six** — checked against the brand's own
assortment page and the open web on 2026-11-17. KKP is the premium tier and is
always boxed apart from the four core lines.

His plan, confirmed 2026-11-17:
- **Regency Cigar "God of Fire Sampler", $92.00** — Carlito Churchill 7x48,
  Don Carlos Toro 6x50, Serie B Double Robusto 5 3/4x52, Aniversario 56
  6 1/2x56. Four of the six lines. Ali verified this himself; it is NOT
  scrapeable (regencycigar.com is behind a Cloudflare managed challenge, which
  covers even /robots.txt — do not attempt it, same as CigarPage and JR).
- **tobaccoreserve**, the two KKP lines at $49.50 each.

**$92 for four lines is the benchmark.** Report any God of Fire sampler that
spans four or more lines AND beats $23/stick, and any KKP single under $49.50.
Two known traps: Greenwich's "Tour of God of Fire 10-Cigar Sampler" at $284.75
covers only three lines despite the name, and Cuenca's KKP Never Back Down &
Special Reserve Sampler is $269 against $99.00 for those two as singles.

If a line lands well and he wants depth later: Greenwich has the Serie B
5-Cigar Assortment at $134.85 and the Serie Aniversario at $146.00, both under
cigarsdirect's $142/$173 and the $170/$180 official MSRPs.

## Standing watches

Both are enforced in code by the `WATCH` list in `monitor.py`, which fires on a
new listing, a restock, or a price cut of ANY size, into the `## ⚑ Standing
watch` section at the top of `findings.md`. That section leads the report.

### OpusX Heaven & Earth (added 2026-11-17 at Ali's request)
Report ANY of it the moment it is in stock or on pre-order, at any price.
tobaccoreserve is the main source: 45 variants, 15 in stock as of 2026-11-17 —
El Escorpion Maduro and Natural singles $77.50; Rare Black Diadema 54/56, Rare
Black Torpedo, Scorpio Maduro and Tauros The Bull Natural singles $80.00; Rare
Black 6-Cigar Selection $450.00; Opus 5 Set $395.00; Opus 11 Sampler $825.00.
Plus five PRE-ORDER singles at $80.00: Carlito's X Rare Purple Diadema 54/56/60,
Purple Rain Torpedo, Rare Black Double Corona. **Anything beyond that list is
news.** Currently OUT, and worth hearing about the moment they return: BBMF
Natural and Maduro ($90 single / $875 box), Big B, Tauros Maduro, Rare Black
Diadema 60, the Rare Black Diadema 56 five-pack, both Opus 6 Samplers.

### Rare Pink
Report ANY movement, at any price, even outside a promo.

- **Rare Pink Vintage 1960's** — Happy Endings, Signature, Work of Art, Short
  Story, Queen of Hearts, Sophisticated Hooker. He has smoked Work of Art and
  likes it. iheart cut the Happy Endings box of 5 from $175.00 to $122.50
  ($24.50/stick) on 2026-10-19, again 2026-11-02, and again 2026-11-16 alongside
  Work of Art at $160.00 -> $112.00 ($22.40/stick). **He has passed every time,
  so treat a recurrence as information, not urgency.** Always check Tampa first:
  its standing Work of Art Mini Box of 5 at $85.95 ($17.19/stick) beats iheart's
  30%-off price by 23%.
- **Rare Pink Black Pink** — the 2026 follow-up. Connecticut-grown habano-seed
  wrapper over Dominican filler, four double-tapered perfectos (Black Panther
  6 5/8 x 55, Signature 6 x 46, Work of Art 4 7/8 x 60, Happy Ending 5 1/2 x 53).
  Shipping since March 2026, restricted to TAA-member retailers.
  **Corrected 2026-11-24.** An earlier note claimed the only Black Pink in the set
  was inside Jack Schwartz's "November to Remember" sampler, and on 2026-11-23 I
  repeated it and called parkplaza the first source. **Both were wrong** —
  tccigar, cigarsdirect and sunofagun have all carried Black Pink for weeks. The
  note was stale and never re-checked, and the comparison that "confirmed" it
  looked only at singles, so sunofagun's 5-packs were invisible to it.

  Verified live 2026-11-24:
  - **parkplaza — DOES NOT SHIP TO NEW YORK, so it is not a buy at any price.**
    Removed from the tracked set 2026-11-24. Listed Signature $24.99, Work of Art
    $24.99, Happy Ending $29.99, all in stock. Kept here only as a price reference.
  - **cigarsdirect — in stock but it is the Fuente outlier.** Work of Art and
    Signature boxes of 25 at $70.00/stick, Happy Ending $120.00 single, **Black
    Panther box of 20 at $2,200 ($110.00/stick)** — the only Black Panther anywhere
    we can see, and it came back in stock on 2026-11-23. Not a buy at that price.
  - **tccigar — everything OUT.** Work of Art $25.10, Happy Ending $28.75,
    Signature $24.10 as singles. **The prices to watch: a tccigar restock
    undercuts parkplaza on all three.**
  - **sunofagun — everything OUT**, all four vitolas as 5-packs: Signature
    $15.00/stick, Work of Art $15.80, Happy Ending $17.20, Black Panther $21.40.
    **Cheapest per stick of anyone when it is in stock** — and it WAS in stock on
    2026-11-19 (Work of Art), so it moves.

  **Net: there is currently no realistic way for Ali to buy Black Pink.** The only
  shop with it in stock that ships to him is cigarsdirect, at $70-120/stick, which
  is the Fuente outlier and not a buy. tccigar and sunofagun both ship to NY and
  both undercut everyone — **a restock at either is the event to report**, along
  with any Black Panther outside cigarsdirect.

For an untried Rare Pink vitola he would rather buy **singles or a Weekly Burn
tier than a 5-pack**, so flag single-stick availability when it exists.

**Breadth beats depth, and beats per-stick price.** Decided 2026-11-24: offered a
Rare Pink Happy Ending 5-pack at Federal Cigar for $119.75 ($23.95/stick, the
cheapest Happy Ending anywhere and under the $24.50 he had already passed on
three times), he chose Tampa's Rare Pink Sampler IV at $150.00 instead — six
different vitolas including the two he has never smoked. **So for a line he is
still exploring, a sampler covering the range outranks a cheaper 5-pack of one
vitola. Do not lead with a single-vitola multipack when a range sampler exists.**

## Where to buy what

Measured 2026-11-19 on a full catalogue pull of all eight Shopify shops.

**Atabey -> sunofagun, always.** tobaccoreserve is cheapest on **0 of 12** Atabey
singles, running a flat 10-14% over sunofagun on every one: Hechizos $22.00 vs
$19.99, Divinos and Idolos $29.50 vs $25.99, Brujos $36.00 vs $31.99, Delirios
and Spiritus and Duendes $41.50 vs $36.99, Dioses and Misticos $46.50 vs $41.99,
Benditos $48.50 vs $42.99, Sabios $38.00 vs $33.99, Ritos $45.50 vs iheart's
$40.00. tobaccoreserve has the breadth (46 variants vs 48) but never the price.

**God of Fire -> split.** KKP at tobaccoreserve (flat $49.50 for Gran Toro 56,
Piramide 58, Toro Extra 54, Diadema 60; $52.50 Diadema 56, $55.00 Diadema 54).
The four core lines at cigarsdirect. This is the main reason tobaccoreserve is
in the set: 64 God of Fire variants, all 64 in stock, the best availability
anywhere in the rotation.

**Don Carlos Edicion de Aniversario -> jackschwartz**, $38.50 Robusto / $39.50
Toro / $39.50 Double Robusto, against tobaccoreserve's $43.00-$44.00. Note
tobaccoreserve lists this line as "Opus X Don Carlos Edicion de Anniversario" -
everyone else sells it as an Arturo Fuente line, not an Opus X, so that prefix
looks like their mislabel and is worth confirming before treating it as Opus X.

**Rare Pink singles — split tccigar / Greenwich.** Verified in stock 2026-11-24:

| vitola | cheapest in-stock single | |
|---|---|---|
| Short Story | **$18.25** | tccigar |
| Signature | **$24.35** | tccigar |
| Work of Art | **$25.10** | tccigar |
| Queen of Hearts | **$33.95** | tccigar |
| Happy Ending | **$30.80** | greenwich (iheart $35.00) |
| Sophisticated Hooker | **$50.00** | greenwich (cigarsdirect $90.00) |

**Greenwich carries the entire Rare Pink line as singles, 5-packs and boxes, all
in stock**, and is the only in-stock source for Sophisticated Hooker. This was
invisible until 2026-11-24 because Greenwich never reached the matcher - the gap
that was fixed the same day. Discount any "% under cigarsdirect" on Rare Pink.

**The six as singles come to $182.45. Tampa's Rare Pink Sampler IV is $150.00 for
all six** ($25.00/stick, one order, ships to NY) - still the best way to buy the
line, by $32.45. A 2026-11-23 answer put that gap at $76.65 because Greenwich was
not in the comparison. Greenwich's own Rare Pink 5-Cigar Assortment is $150.00
for FIVE, so Tampa's beats it outright.

**Greenwich also lists Black Pink** (Happy Ending, Signature, Work of Art) but all
out of stock and priced $0.00, which is its known broken-listing pattern. It is a
restock source to watch, not a price.

### Correcting the 2026-11-17 "53 unique variants" claim

That figure was used to justify adding tobaccoreserve and **it was about double
the truth**. Re-measured 2026-11-19 on the same brand set: 51 of its in-stock
variants had no strict match elsewhere, but 25 of those matched once spelling
and title differences were folded, leaving **about 28** genuinely absent from
every other tracked shop. Including God of Fire, which was not in the brand set
on 2026-11-17, the current figure is **about 36**.

Two distinct causes, both worth remembering when judging any shop's "unique"
inventory:
- **tobaccoreserve omits the vitola from its product titles.** It lists "Atabey
  Hechizos"; everyone else lists "Atabey Hechizos Petit Corona". Same cigar.
  Exact token matching cannot see through that, and the two-token titles fall
  below the three-distinctive-token floor the cross-retailer matcher uses, so
  they are never fuzzy-matched either.
- **Spelling and house prefixes.** "Anniversario" vs "Aniversario", "Opus X ..."
  vs "Arturo Fuente ...". Folding doubled letters and accents fixes the first;
  the second needs the house tokens set aside, but only once the rest of the
  title carries three distinctive tokens of its own, or "OpusX Robusto" matches
  "Arturo Fuente Robusto".

So: **never present "no match at the other shops" as evidence a shop is the only
source, or as a reason to buy there.** Check the brand and line by hand first.

**Also found:** Opus X Purple Rain Torpedo is at sunofagun at $80.00, the same
price as tobaccoreserve's pre-order, so Heaven & Earth is not a tobaccoreserve
exclusive the way the 2026-11-17 note implied.

## Always

Stock matters as much as price — a cheap listing that is out of stock is useless
to him. Out-of-stock prices appear only as context.

**Do not cite Cigar Aficionado ratings** — Ali considers them paid-for. Use
halfwheel, Cigar Coop or Reddit if a rating is worth mentioning.
