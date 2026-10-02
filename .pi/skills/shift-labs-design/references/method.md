# Honest numbers — the method behind "How we counted"

The Agent Work Index discloses its method on every page that shows a number. Copy that discipline.
This file is the per-number floor for every document. Documents that support a decision also follow the
decision-ready method in `decision-method.md` (metric contracts, matched comparisons, decomposition, the evidence
ladder, action gates, visible trust).

## Every number
1. **Unit and denominator in words.** "53% of sensors fire on new items", "66% of the agent turns that
   sensors start". A bare "66%" fails review.
2. **One orange number per slide** — the one the reader should carry away. Others are ink.
3. **Rounding is visible.** Decks use whole percentages. If shares do not sum to 100, say "may not sum to 100
   because of rounding". In running text say "about" rather than round silently.
4. **Derived numbers recompute.** `data-calc="(1180-1000)/1000*100"` on the element showing 18.0%; lint evaluates it
   and checks it at the shown precision. Only digits and + − × ÷ ( ).
5. **Suppression, not estimation.** When a category is seen at too few units, print n/a (`null` in shares,
   `.s-card__meta.is-na`), and define n/a in How we counted.

## How we counted — what it states
Unit (what one case is) · source (where the rows came from) · weighting (e.g. each organization counts equally) ·
exclusions (tests, empty stubs) · coding reliability (e.g. agreement on a fresh random sample) · anonymisation
(examples paraphrased, names removed, code rewritten). One to three sentences on a slide; a `.s-method` `dl`
on a page. The kit prefixes the bold lead "How we counted." (`data-lead` renames it, e.g. "Source.").

## Data mode (`<html data-mode>`)
| Mode | Meaning | What the kit shows |
|---|---|---|
| `published` | final figures from a named study | calm badge "Published figures" |
| `snapshot` | a frozen export; add `data-cutoff="<date time of extraction>"` | orange badge with the cutoff |
| `live` | fetched at view time | calm badge with an orange dot |
| `sample` | real-looking example data | orange badge + "Sample data" in every deck footer |
| `synthetic` | generated data | orange badge + "Synthetic data" in every deck footer |

Sample and synthetic data must never look like published data: the badge and footer are automatic, do not remove them.

## Claims
A title names the thing; a report h1 may state a finding only when the stat beside it proves it
("Two in three sensor turns end with nothing to do" next to 66%). Causal, attribution and record words (because,
drives, leads to, accounts for, a record) carry an evidence level (`.s-claim` / `data-evidence`, see
`decision-method.md` §6); lint fails them otherwise. Correlation is described as co-occurrence.
