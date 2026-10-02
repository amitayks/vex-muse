# Shapes — full specs

Markup: `<figure class="s-shape" data-shape="NAME" id="…" data-figure="…"><script type="application/json">{…}</script></figure>`.
`id` lets `<pre class="s-code" data-spec-of="id">` print the spec; `data-figure` exports a PNG (shoot `--figures`).
Units are deck points (u). SVG shapes redraw on resize and on theme toggle; colours come from `k-*` classes,
so dark mode needs nothing extra. Every SVG shape takes `"alt"` (the accessible sentence) — write one.

## ticks — runs over time
```json
{"runs": "....1....11...", "pad": 6, "style": "tick",
 "notes": [{"at": 9, "text": "Second failure:\nalert", "mark": "ring", "tone": "signal", "row": 0}], "alt": "…"}
```
- `runs`: one char per run; `.` = nothing, anything else = fired (tick style) or failed (check style).
  Or `{"n": 60, "fired": [8, 20]}`.
- `style: "check"`: ✓ for ok, orange ✗ for failed — probes, health checks, retries.
- `notes`: labels under a run. `mark`: `ring` (orange, fired) or `hollow` (ink, recovered); `tone`: `signal` (default),
  `ink`, `muted`; `\n` breaks lines; `row: 1` drops a label one row (colliding labels also drop automatically).
- Caption it: "Each tick is one run … Orange runs fired."

## axis — points on a line
```json
{"points": [{"label": "Guest wrote", "kind": "start"}, {"label": "5 min", "above": "1 / 5", "size": 0}],
 "scale": "index"}
```
```json
{"scale": "linear", "domain": [-17, 2.4], "spans": [{"from": -14, "to": 0, "label": "Reminder window"}],
 "lines": [{"at": 0, "label": "Due"}], "points": [{"at": -17, "label": "Now", "kind": "now"}, {"at": -7, "label": "7 d", "kind": "dot"}]}
```
- `kind`: `ring` (default, orange, grows with `size` 0–2), `dot`, `start` (ink), `now` (ink), `hollow`, `cross`.
- `scale`: `index` (equal spacing, default) or `linear` with `domain` and each point's `at`.
- `above` + `aboveTone: "signal"`: a label over the point. `ticks: [{at, label}]` for clock hours;
  `dotted: [from, to]` for time that passes without runs. Colliding labels drop a row; crowded tick labels thin out.

## line — a value over time
```json
{"values": [58, 52, 60, 49, 66, 82, 88, 70, 61], "band": [45, 72], "height": 50,
 "bandLabel": "Normal range", "leaveLabel": "Leaves the range: fires", "returnLabel": "Returns: fires once",
 "x": ["Mon", "", "Wed"], "axis": false, "unit": "%", "key": 5}
```
- With `band`: the out-of-range stretch turns orange, the first leave is ringed, the first return is an ink ring.
- As a data chart: `"axis": true` draws three gridlines with values (zero-based unless `"zero": false`); `x` labels
  the runs; `key` rings one point; `"points": true` shows every observation. Titles name the metric; the reading
  goes in the caption.
- Several series (a trend of related series):
```json
{"x": ["20 Jul", "27 Jul", "3 Aug"], "series": [{"name": "Sensors", "tone": "key", "values": [11520, 11840, 13904]},
  {"name": "People", "tone": "ink", "values": [5910, 6080, 6380]}, {"name": "Schedules", "values": [2930, 2960, 3214]}],
 "height": 84, "zero": true, "alt": "…"}
```
  Straight segments, a dot on every observation (`"points": false` to hide), round axis ticks, names at the line
  ends (nudged apart, never overlapping). `tone`: `key` orange (one series: the one the text discusses), `ink`
  (a second series you compare), default grey context. Zero-based unless `"zero": false`. Smoothing does not exist
  (lint fails `"smooth"`).

## shares — ranked shares
```json
{"rows": [["New items", 53], ["A set time", 18], ["Records only", null]], "key": 0, "unit": "%", "total": 100, "fmt": "int"}
```
- Sort high → low (lint warns otherwise). `key` (default 0) is the orange bar; others are grey.
- `null` prints n/a with a hairline: too few cases to show. `total` makes lint check the sum within rounding.
- ≤ 10 rows. Put the column title and its denominator in `.s-shares-head` above (h3 + `.s-small`).

## flow — how a thing moves through a system
```json
{"steps": [
  {"kind": "list", "label": "Systems it can read", "items": ["Inbox", "Sheet"]},
  {"kind": "code", "label": "Code the agent wrote", "code": "const fresh = past(cursor)"},
  {"kind": "store", "label": "Compare with the last run", "note": "The platform stores the cursor."},
  {"kind": "event", "grow": true, "text": "{ id, prompt }", "tag": "One event per new item",
   "else": {"text": "nothing new → sleep.", "note": "The run ends without calling the agent."}},
  {"kind": "agent", "label": "Agent"},
  {"kind": "chip", "text": "work", "check": true, "tone": "signal"}]}
```
- Kinds: `list`, `code`, `store`, `event` (orange box + optional `else` branch), `agent` (ring), `chip`
  (`tone: "plain"` = ink), `box` (a plain outlined item). Any step takes `label` above and `note` below.
- Arrows are grey until the event, orange after. If the row cannot fit its container it stacks top to bottom.
- Layout: one grid with rows label · body · note (subgrid). Every body and every arrow is centred on the body row,
  so arrows meet boxes at their middles however tall a label or note is. A list of several sources gets a bracket,
  and its arrow leaves from the bracket's middle. Arrows stretch; boxes do not. Each arrow runs box edge to box
  edge with the same gap at both ends, even when a wide label or note widens a step's column. Nodes (store, agent,
  chip) are centred under their captions; lists and code keep left-aligned column labels on one line.

## queue — a list with a cursor
```json
{"seen": 4, "fresh": 2, "cursor": "Cursor", "note": "On the first run the sensor only sets the cursor.",
 "resultLabel": "After the cursor", "result": "2 events → one turn\ncursor moves past them"}
```

## diff — last look vs this look
```json
{"before": {"label": "Last look", "rows": [["status", "Scheduled"], ["gate", "B4"]]},
 "after":  {"label": "This look", "rows": [["status", "Delayed"], ["gate", "B9"]]}}
```
Changed values (by key) turn orange and bold; the card tints; the sign is ≠ (or = when nothing changed).
Grid: labels row, cards row; the sign is centred on the cards, not on card + label.

## match — two systems that should agree
```json
{"left": {"label": "Arrivals today", "rows": ["104", "207", "311"]},
 "right": {"label": "Cleaning plan", "rows": ["104", "207", null]}}
```
Rows pair by position. Equal pairs get a hairline; a missing or different partner gets a dashed orange link, ? and a ring.
Grid: each record is one row shared by both cells and its link, so they share a centre line.

## stairs — stages that take on more
```json
{"steps": [["Shadow", "logs what it would do"], ["Notify first", "alerts; a person acts"], ["Live", "acts, then reports"]],
 "active": 2, "rise": 22}
```
Boxes climb left to right by `rise` u; `active` is tinted. On a phone page they become an indented list.

## fanout — split or copied
```json
{"from": "one sensor", "to": ["5 min", "15 min", "155 min"], "tone": "signal"}
{"from": "one sensor", "to": ["group 1", "group 2", "group 3", "group 4"], "cols": 4}
```
`tone: "signal"` for a split into stages (orange); plain for copies. Narrow containers cap `cols` at 2.

## Data shapes for decision-ready documents (method: `decision-method.md`)
Every data shape takes `"alt"`, `"fmt"` (`int`, `pct1`, `usd`), `"unit"` and `"reconcile": "key"`: lint then checks
that the shape's values sum to the element carrying `data-total="key" data-v="N"` (at the shown precision).

## columns — a few periods, zero-based, beside the matched prior
```json
{"x": ["Mon", "Tue", "Wed"], "series": [{"name": "7–13 Sep", "values": [3902, 4288, 4366]},
  {"name": "31 Aug – 6 Sep", "role": "prior", "values": [3560, 3720, 3810]}], "key": 2, "axis": false, "reconcile": "turns"}
```
- Current bars grey (`key` orange), the prior outlined beside them, a legend when a prior exists. Always from zero;
  negative values fail (use `variance`). Value labels sit over the taller bar; if they collide only the key keeps one.
- Without a `"role": "prior"` series lint warns: one period cannot say whether it is good.

## variance — contribution to a change
```json
{"rows": [["Sensors", 12012, 13904], ["People in chat", 6010, 6380], ["Teammates", 700, 820]], "total": 2396,
 "fmt": "int", "reconcile": "turns-change"}
```
- Rows are `[label, from, to]` or `[label, change]`; rank by size of change (lint warns otherwise). `total` is the
  headline change: parts must sum to it (lint fails otherwise). The zero line sits where zero falls: drags extend
  left, drivers right. `key` (default: the largest change) is orange.
- The share of the change prints after each value only when all parts move the same way (`"share": false` hides
  it); with mixed signs the deltas speak alone. A total row closes the chart.

## tablegraph — exact breakdown with movement (the answer to a pie)
```json
{"rows": [["Sensors", 13904, 12012], ["People in chat", 6380, 6010]], "labelHead": "Trigger", "valueLabel": "7–13 Sep",
 "priorLabel": "Prior week", "fmt": "int", "key": 0, "reconcile": "turns"}
```
- Rows `[label, value, prior]` sorted high → low. Columns: value with an inline bar · share of total · prior ·
  change · change % · contribution to the total change (— when parts move in different directions). A total row
  closes it (`"total": false` to drop). Wide on a phone: it scrolls inside its own `.s-table` box.

## bullet — actual against target
```json
{"rows": [{"label": "Failed-turn rate", "value": 2.9, "target": 2.5, "band": [0, 2.5], "max": 4, "unit": "%",
  "fmt": "pct1", "better": "lower"}]}
```
- Track from zero to `max`; `band` = the target range (calm tint); ink tick = `target`; the bar turns orange when it
  misses (`better`: `lower` or `higher`). No target: it is not a bullet (lint fails) — use `shares`.

## heatmap — two ordered dimensions (day × hour)
```json
{"rows": ["Mon", "Tue"], "cols": ["00", "02", "04"], "values": [[47, 31, 39], [51, 34, 43]], "threshold": 540,
 "thresholdLabel": "540 or more", "reconcile": "turns"}
```
- Grey by intensity; cells at or over `threshold` orange (what fired). `null` = no data (outlined). Column labels
  thin out when crowded; a legend (low → high, threshold) sits below. `values` must be rows × cols.

## When no shape fits
Draw inline SVG sized in u (viewBox width = container width / u) using only kit classes:
strokes `k-line` (grey), `k-hair`, `k-ink`, `k-ink2`, `k-sig`; fills `k-fill-bg`, `k-fill-tint`, `k-fill-calm`,
`k-fill-sig`, `k-fill-ink`, `k-fill-ink2`, `k-fill-bar`, `k-fill-rule`; text `k-t`, `k-t-ink`, `k-t-mono`, `k-t-cap` (+ `is-sig`, `is-ink`, `is-faint`).
Grammar: one centre line per connection, grey structure, one orange event, ringed dot = fired, hollow ink ring = recovered, dashed = no data
or a gap, labels in bold caps at 6.2–6.8u, 0.9u strokes, 3.5u corner radius. Draw ✓ ✗ ⏰ as paths, not glyphs.
