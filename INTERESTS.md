# Ali's interests

The volatile half of the monitoring brief. The Routine reads this file on every
run, so changing what gets reported is a commit here — not a rewrite of the
Routine prompt. Keep it current; date every claim.

Last confirmed with Ali: **2026-11-17**.

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
  Shipping since March 2026, restricted to TAA-member retailers. As of
  2026-11-05 the only buyable Black Pink at any tracked retailer is inside Jack
  Schwartz's "November to Remember" sampler ($270, 14 sticks). **Report the first
  time any retailer has Black Pink singles or boxes IN STOCK, whatever the price.**

For an untried Rare Pink vitola he would rather buy **singles or a Weekly Burn
tier than a 5-pack**, so flag single-stick availability when it exists.

## Always

Stock matters as much as price — a cheap listing that is out of stock is useless
to him. Out-of-stock prices appear only as context.

**Do not cite Cigar Aficionado ratings** — Ali considers them paid-for. Use
halfwheel, Cigar Coop or Reddit if a rating is worth mentioning.
