# Decision-ready documents — the method (Dio)

A report is not a decorated dataset. It is a governed argument that helps a named reader make a named
decision. A beautiful report fails if it claims more than its data supports; a correct one fails if the
reader cannot see what deserves attention or what to do next. This file is the method; `lint.py` enforces
the parts a machine can check, and the by-eye review does the rest.

**decision → evidence contract → data QA → metric semantics → matched comparison → decomposition →
evidence ladder → chart by job → action gate → visible trust → artifact QA → usage review**

Scope: every Shift Labs document with numbers follows §2–§7 and §10. A **decision-ready report**
(`<html data-doc="report">`: reviews, weekly or monthly readings, briefs, dashboards, anything whose job
names a decision) follows all of it, and lint enforces the full contract. Examples below use placeholders
and round illustrative numbers; never paste a client's figures, names or partners into this skill.

## 1. Reconstruct the decision before touching a chart
Answer first: who reads it · what decision they own · what action changes when a metric moves · what
would make them say "this needs attention" · what they will ask right after the headline. Write it as
`<!-- job: … -->` under `<title>` (reader, decision, what changes it). The job decides the default view.

The first screen of a report answers six questions (`dl.s-brief`, one `data-q` each):
`changed` what changed · `material` is it material · `drivers` what drove it · `risk` what is at risk ·
`decision` what decision is required · `missing` what evidence is still missing.
The thesis is on the first screen; the evidence sits one level below it, never gone.
A job that reads like promotion ("a great period") is rewritten as a decision ("decide which movements
justify investigation now, and hold changes the evidence does not support yet").

## 2. Every metric is a contract
**Metric = meaning + source + grain + calculation + exclusions + comparison + owner + action.**
- Meaning: the business fact it represents. Source: the system, table, file or certified aggregate.
- Grain: what one row or observation is. Calculation: numerator, denominator, aggregation, time logic.
- Exclusions: tests, internal users, cancelled or refunded items, tax — whatever is removed.
- Comparison: matched prior period, plan, same period last year, peer cohort or SLA.
- Owner: who approves the meaning and the threshold. Action: what changes when it moves.
If two reasonable people can compute it differently, it is not defined yet.
Kit: a `tr[data-metric="id"]` row in `table.s-contract` (all nine cells; "Not set" is a visible gap), and
each KPI `.s-stat[data-metric="id"]` points at its row.
Precision: show the exact value at a sensible precision. If you round, say so ("about 40"), and keep the
exact arithmetic in `data-calc` so lint recomputes it at the shown precision. A growth of 7.46 % is
"+7.5 %", not an unexplained "+7 %".

## 3. Data QA is not metric validation
**Data QA — can the source be used?** Freshness and extraction time · expected periods and entities all
present · duplicate keys · nulls and unknown classes · range and sanity limits · schema stability ·
lower-grain totals reconcile to higher-grain totals · missing sources or collector failures.
**Metric validation — does the number mean what the reader thinks?** Business definition · denominator ·
grain · matched windows · additivity and roll-up · current versus historical dimension values · a proxy
mistaken for an outcome · actionable or only impressive.
Arithmetic can pass while meaning fails: totals that reconcile across every dimension do not make a claim
about hours, costs or margins true when no hourly, cost or margin data is present.
Kit: `data-total="key" data-v="N"` on the governing number; any shape with `"reconcile":"key"` must sum to
it; list every reconciliation in the `qa` trust field.

## 4. Matched comparisons
A number without context says what it is, not whether it is good. Default to the previous matched period
(same length, same alignment: weekday to weekday); add same period last year for seasonality, plan or
budget for steering, an SLA for operations, a peer cohort for relative performance. Never compare a
complete period with an incomplete one without saying so prominently. If the cutoff was not captured,
the `cutoff` trust field says "Not captured" and the period is not treated as closed.
Kit: every report KPI carries `.s-vs` (its benchmark in words and numbers); a `columns` shape shows the
matched prior as a `"role":"prior"` series.

## 5. Decompose the change, not only the total
After "X rose 9 %", the next question is "what moved it". Rank components by **contribution to the
change**, not by current size, and make the parts reconcile exactly to the headline change. Show
contribution shares only when all parts move the same way; with mixed signs, show the deltas.
"Segment A made two thirds of the increase" is arithmetic (confirmed). "Feature X caused segment A's
growth" needs its own evidence (usually unknown). Keep the two statements visibly apart.
Kit: `variance` (zero-centred driver bars, `total` = the headline change) or `tablegraph` (value · share
· prior · Δ · contribution). A report must contain one of them.

## 6. The evidence ladder
| Level | `data-evidence` | Means |
|---|---|---|
| Confirmed | `confirmed` | direct evidence connects the population, the timing and the mechanism |
| Likely | `likely` | strong support; causality not proven |
| Suspected | `suspected` | a pattern worth investigating |
| Correlated, not causal | `correlated` | two movements overlap with no proven mechanism |
| Unknown | `unknown` | the available source cannot answer it |
Every explanatory, causal, attributive, predictive or record claim carries a level (`span.s-claim` chip, or
`data-evidence` on an ancestor). Unsupported claims are not deleted: they move to the claims ledger
(`table.s-ledger`) with what would settle them, and become data requests. Lint fails causal, attribution
and record language outside a `data-evidence` element (a phrase list: new wording can slip past it, so
read your own claims too). Method notes (`.s-counted`, `.s-method`) and quoted bad examples
(`data-example`) are exempt.

## 7. Chart type is part of the analysis
For every visual answer: what job does it do · does the type fit the job · what can it prove · what can it
not prove · is a required chart missing?
| Analytical job | Kit |
|---|---|
| trend over ordered time | `line` — straight segments, visible observations (`points`), context series grey |
| a few period comparisons | `columns` — zero-based, with the matched prior |
| ranked categories | `shares` (horizontal bars) |
| contribution to change | `variance` |
| exact breakdown with movement | `tablegraph` |
| actual versus target | `bullet` |
| two ordered dimensions (day × hour) | `heatmap` |
| operational exceptions | a table or the decision queue, not a chart |
Hard defaults: no pie or donut, no stacked bars or areas, no smoothed lines, no 3D. Categorical bars are
horizontal. Bars start at zero (the kit has no truncated axis; if one is ever needed, label the break).
Colour carries meaning: orange is what fired or the one key series, grey is context, the outlined bar is
the comparison period. **A chart title names the metric** ("Agent turns by day"); the reading goes in the
subtitle, a note or the text beside it. A single period cannot prove a record; units cannot prove
profitability; a share cannot prove a cause.

## 8. Hierarchy for the audience
1 headline — the material movement and its implication · 2 KPI band with explicit benchmarks ·
3 movement — current versus comparison · 4 drivers and drags — reconciled · 5 exposure — concentration,
risk, opportunity, plan gap · 6 decision queue · 7 evidence and provenance.
Operational detail lives below the decision layer (`details.s-more`). Seniority changes the default view
and the depth, never the truth of a metric. Sections carry `data-part` (`movement`, `drivers`, `exposure`,
`decisions`, `evidence`) so lint can check the order.

## 9. Action gates
A decision row (`article.s-decision[data-kind]`) states: the decision requested · its kind
(`approve`, `investigate`, `defer`, `reject`, `act`) · current evidence · missing evidence · owner (a person
or a role) · review point · status · evidence source. A costly or irreversible action whose evidence is
still missing is downgraded to a diagnostic step: the report can authorise learning before it can
authorise intervention. Lint fails `act` or `approve` while `missing` is anything but "None". Invented
precision in an action ("add N people at peak") is a claim like any other: it needs demand,
throughput and cost evidence, or it becomes "evaluate capacity".

## 10. Trust is visible
Trust fields (`div[data-trust]` in the report's `.s-trust` panel): `mode` (published, snapshot, live, sample,
synthetic) · `source` and lineage · `generated` · `period` (latest complete period) · `cutoff` · `qa` (the
checks and reconciliations that passed) · `definitions` (metric-definition version) · `scope` (who may
see it) · `caveats`. A field that was not captured says **Not captured**, never silence. The data mode is
also a persistent badge (`.s-mode` in the page header; the running footer on report decks), so a
screenshot of any screen still says what the data is. The document must not look more authoritative
than its source.

## 11. Verify the artifact, not only the analysis
- Semantic: definitions match meaning · claims ≤ evidence · matched periods · actions follow from evidence.
- Data: totals reconcile across dimensions · variance reconciles to the headline · right denominators ·
  rounding explicit · derived numbers carry `data-calc`.
- Visual: chart types fit their jobs · required charts present · honest axes and baselines · no label
  collisions · semantic, accessible colour (shoot measures contrast in both modes).
- Product: no page-level horizontal scroll at 390 px · wide tables scroll inside `.s-table` or reflow ·
  keyboard focus visible · reduced motion honoured · every control works, or is disabled with its reason,
  or is marked as a prototype · source, freshness, data mode and the decision contract are visible.
A check you could not run (no browser, no source) is reported as not run, never as a pass.

## 12. The final test (all yes, or it is not finished)
1. Can the reader state the headline in 10 seconds?
2. Can they see what moved it without asking for another analysis?
3. Can every material claim be traced to visible evidence?
4. Does the report separate action from investigation?
5. Would it still be honest if its most attractive narrative turned out to be false?
The difference between a promotional report and a decision-ready one is epistemic discipline, not
decoration: what is known, what is inferred, what is missing, what decision is justified, and what must
happen before the next decision becomes safe.

## Markup contract (what lint checks)
```html
<html lang="en" data-theme="light" data-mode="synthetic" data-doc="report" data-cutoff="Not captured">
<!-- job: <reader> decides <decision>; it changes when <metric> moves -->
<header class="s-head"> … <span class="s-mode"></span> …                       persistent data-mode badge
<dl class="s-brief"><div data-q="changed"><dt>…</dt><dd>…</dd></div> … material drivers risk decision missing
<p class="s-stat" data-metric="turns"><b data-total="turns" data-v="20480">20,480</b>
   <span>agent turns this week <small class="s-vs">Matched prior week: 18,400</small></span></p>
<span data-calc="(20480-18400)/18400*100">+11.3%</span>                    recomputed at the shown precision
<figure class="s-shape" data-shape="columns|variance|tablegraph|bullet|heatmap|line|shares">{… "reconcile":"turns"}
<span class="s-claim" data-evidence="confirmed|likely|suspected|correlated|unknown"></span>
<table class="s-ledger"> <tr data-evidence="unknown"><td>claim</td><td>level</td><td>what would settle it</td><td>source</td>
<article class="s-decision" data-kind="investigate"> <div data-field="evidence|missing|owner|review|status|source">
<div class="s-trust"><dl><div data-trust="mode|source|generated|period|cutoff|qa|definitions|scope|caveats">
<table class="s-contract"><tr data-metric="turns"> meaning · source · grain · calculation · exclusions ·
   comparison · owner · action
<td data-example="bad">…</td>                                           quoted bad examples, exempt from claim lint
```
