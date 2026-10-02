# Pre-release checklist for a skill

Run before any release that ships or edits a skill.

1. `name` == directory name; lowercase alphanumeric + single hyphens.
2. `description` ≤1024 chars; states what AND when; carries task keywords.
3. `metadata.version` semver; bumped iff the body or references changed
   behavior; matches any line pin shipped in the same release.
4. Body <500 lines; no rationale/history prose; every reference link resolves
   one level deep.
5. `LEARNINGS.md` present; entries are one-line intents with dates.
6. Acceptance check stated in the body.
7. No real identifiers, hosts, names, or dates of operations; secrets by name.
8. Standalone read-through: a fresh agent with only this skill and its
   declared tools can do the work and verify it.
9. If pack-shipped: listed in `MANIFEST.json` `surfaces.skills` with the same
   name/version/path.
