# LEARNINGS

<!-- One line per correction: YYYY-MM-DD — the intent, not the incident. -->
2026-09-24 — a line that branches on item kind gets ONE routing skill (kind → skill map, explicit no-op verdicts), not per-kind stations; the router is itself a skill with a version.
2026-09-24 — deterministic checks that need connected plugins (Sheets/Drive reads) stay agent stations until script stations can hold plugin access; note it as a deviation, not a silent choice.
2026-09-24 — a skill that edits its own installed body at runtime (e.g. promoting learnings into SKILL.md) is an instance patch that breaks version pinning; promotion flows upstream as a version bump, the deployment keeps only its LEARNINGS.
2026-09-25 — installed skills never self-mutate: deployment-local corrections go to a deployment LEARNINGS file beside the skill; folding into SKILL.md happens upstream with a version bump, or the installed copy drifts from its pin (design-studio pilot).
