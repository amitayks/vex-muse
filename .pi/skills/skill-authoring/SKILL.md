---
name: skill-authoring
description: How a Shift skill is written, maintained, and bound — the one methodology. Use before writing or editing any SKILL.md, converting a pack to skills-first, or binding a skill to a factory station. Covers format, budgets, LEARNINGS, and what belongs in a skill vs a script vs a line vs a gate.
license: MIT
metadata:
  author: shift-labs-ai
  version: "1.0.0"
---

# skill-authoring — the constitution

A skill is the ONLY place method lives. Lines enforce, scripts compute, gates
lock — skills teach. If an agent needs to know HOW, exactly one file knows.

## Format (agentskills.io, verbatim)

- Directory `skill-name/` with `SKILL.md`; frontmatter `name` (lowercase,
  hyphens, == dirname) + `description` (what AND when, ≤1024 chars) required.
- `metadata.version`: semver, bumped on every behavior-relevant edit. Lines
  pin it; an unbumped edit is a release failure.
- Optional: `compatibility` (only if real environment needs), `allowed-tools`.

## Budgets (hard)

- Body < 500 lines, < 5k tokens. Depth goes to `references/*.md`, loaded on
  demand, one level deep. Helpers go to `scripts/` (self-contained, clear
  errors). Static resources go to `assets/`.
- Description ≤ 1024 chars carrying keywords an agent would match the task by.
- Fewest words that keep the full knowledge. Added prose without an added
  rule is a defect. Rationale and history live in references, never the body.

## Writing rules

1. **Intent, not case study.** Extract the reusable recipe; the incident that
   taught it goes to `references/` or LEARNINGS, one line, as intent.
2. **Acceptance check included.** A skill states how to verify its own
   output. Work without its check is not done.
3. **Standalone or nothing.** The skill must be fully usable in plain
   conversation with no line, no pack ceremony. Factories add enforcement,
   never enablement.
4. **One skill, one capability.** A skill that teaches two jobs is two
   skills. Split before it bloats.
5. **No identifiers.** Placeholders only; every one documented at its point
   of use. Secrets by NAME only.

## LEARNINGS protocol

- Every skill ships `LEARNINGS.md` (may start empty).
- A correction discovered anywhere — conversation, review, a failed or
  retracted factory item — is appended the SAME DAY as one line of intent.
- A method fix not reflected in the skill is unfinished. Fold LEARNINGS into
  the body at the next version bump when a lesson has stabilized into a rule.

## Where things belong

| Thing | Home |
|---|---|
| Judgment, method, taste | skill body |
| Deterministic transform | `scripts/` (or a code station) |
| Order, retries, gates, evidence | factory line |
| Consequential-action lock | gate/anchor, above agent authority |
| Depth, rationale, history | `references/` |
| Fresh corrections | `LEARNINGS.md` |

## Binding (factory use)

An agent station binds `skill:<name>@<version>` + an acceptance check —
nothing else in the prompt beyond item context. Method in a station prompt is
a lint failure. Deterministic stations bind scripts; adding judgment where it
was deliberately removed is a regression.

## Acceptance check for this skill's own use

A skill you produced passes when: frontmatter validates (name==dir,
description ≤1024 with what+when); body <500 lines with no rationale prose;
`metadata.version` present; LEARNINGS.md exists; the acceptance check for its
work is stated inside it; it reads standalone.

See [references/checklist.md](references/checklist.md) for the full
pre-release checklist and [references/why.md](references/why.md) for the
failure classes behind each rule.
