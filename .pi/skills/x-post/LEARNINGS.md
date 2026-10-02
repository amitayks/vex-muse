# x-post — LEARNINGS

Corrections learned in use, appended same-day as one-line intents.

- 2026-09-26 — Weighted length is an approximation (URLs=23, CJK/kana/hangul=2,
  else 1); when a post hugs the 280 cap, confirm on the compose screen before
  approving, not on the plugin's count alone.
- 2026-09-26 — Media upload uses X v2 simple upload; large video needs chunked
  upload not yet implemented — keep video small or expect an upload error.
- 2026-09-26 The old redirect (content-bot worker /x/oauth/callback) belongs to the retired Telegram Muse: it consumes/validates state against its own DB and bounces to a Telegram-only webapp, dropping the code. xpost now redirects to the stateless page tools/x-callback (muse-x-callback worker), which only displays the callback URL to paste back. Any redirect change must also be added as a Callback URI in the X developer portal, and a connect must restart after it (redirect_uri must match between authorize and token exchange).
