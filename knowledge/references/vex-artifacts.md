---
kind: technique
tags: [vex, artifacts, react, tsx, verification]
audience: all
half_life: 120
rights: safe
seen: 2026-09-27
---
# Vex artifacts: authoring from files and verifying they run


## Why / Context
Branded artifacts carry a lot of injected source: kit CSS, `@font-face` rules and the logo's paths, about 56 KB. Pasting that into an action call bloats context and invites typos. Some of these behaviours are not stated in the Vex docs, and each cost a probe to confirm.

## Details
- **`execute_actions` can read workspace files.** `const fs = await import('node:fs'); fs.readFileSync('/data/workspaces/<workspace>/<path>', 'utf8')` works, which the docs do not state. Build the TSX with a script, then `vex.artifacts.create({ title, content })` straight from the file.
- **Imports.** The only imports are `react` (plus `react/jsx-runtime` and `react/jsx-dev-runtime`), `recharts`, `lucide-react` and `@vex/actions`. Anything else fails at compile time. `@vex/actions` is the only runtime external.
- **Calling actions.** `import { actions } from "@vex/actions"`, then `await actions.call("plugin.action", input)`. It resolves with the result and throws on failure. Every call carries the **signed-in viewer's** permissions, so design for a denial: show it, don't crash.
- **Update in place.** Use `vex.artifacts.get` then `vex.artifacts.edit` (or `write` for a full rewrite). This keeps the id and URL. A second `create` leaves two copies and a dead link.
- **Verify:**
  1. `buildError` is null on the create or write response.
  2. `canvas.pane.open({ kind: 'artifact', artifactId })` renders the artifact for the viewer.
  3. `vex.artifacts.get` shows `runtimeError: null`. It only fills after a viewer has run the current version.

  If your own code catches an error, render it visibly with the `data-vex-runtime-error` attribute so the text reaches `runtimeError`.
- **Fonts.** URL `@font-face` works, because the artifact runs in the viewer's browser, unlike this box's headless Chrome ([[tool-selection]]). Embedding font bytes in TSX only adds weight.
- **RTL.** Put `dir="rtl" lang="he"` on the root, and wrap recharts in `<div dir="ltr">` so time axes run left to right.
- **Embedding in a note.** A knowledge note can embed an artifact live with `<iframe data-vex-artifact src="/agents/<workspaceId>/artifacts/<artifactId>" title="…"></iframe>`.
