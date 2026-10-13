# Vendored upstream — pinned, never edited

| Repo | Upstream | Pinned commit | Commit date | Vendored |
|---|---|---|---|---|
| ClaudeAnimationBase | https://github.com/JohnHeibel/ClaudeAnimationBase | 0ac8bf2b31942376cb6b8c4074715595d512acd2 | 2026-09-24 | 2026-09-26 |
| PDoomVideo | https://github.com/JohnHeibel/PDoomVideo | fa546a38092e75f2b079e6a86d6abc54dd525d17 | 2026-09-25 | 2026-09-26 |
| cua-motion-lab | https://github.com/trycua/cua (path `libs/cua-driver/tools/cursor-gallery/motion-lab/`) | f25fe3691e651cc8ac6adf92931940ed25d9a6bb | 2026-10-05 | 2026-10-06 |

ClaudeAnimationBase is MIT and vendored here. PDoomVideo carries **no license**, so it is
NOT redistributed in this repo: `bash tools/fetch-vendor.sh` clones it at the pin for local study. `vendor/` is the pristine reference; my working engine is `studio/`
(forked from ClaudeAnimationBase at the pin above, with my changes logged in
`studio/FORK.md`). `cua-motion-lab` (MIT) is a sub-folder of a big monorepo: only
that folder + the repo `LICENSE.md` are vendored. It is used as-is (imported,
never edited) by `.pi/skills/code-motion/scripts/cursor_track.mjs`.

## Refresh procedure (monthly schedule, or when my principal asks)
1. `git ls-remote <upstream> HEAD` — same sha → done. For cua-motion-lab the
   monorepo HEAD moves daily: sparse-clone HEAD (`--depth 1 --filter=blob:none
   --sparse`, `sparse-checkout set <path>`) and `diff -ru` the folder; no diff → done.
2. New sha → clone to `/tmp/<repo>-new`, `diff -ru vendor/<repo> /tmp/<repo>-new`
   (exclude node_modules, .git). Read the diff. For cua-motion-lab, re-run
   `node --test test/motion.test.js` and `cursor_track.mjs --selftest` after the swap.
3. Decide per change: adopt into `studio/` (port by hand, log in
   `studio/FORK.md`), note-only, or ignore. Never overwrite `studio/`.
4. Replace `vendor/<repo>` with the new tree (no `.git`), update this table.
5. Report to the principal in one line only if something was adopted.
