---
name: x-post
description: Secondary utility for posting a finished piece to X (Twitter). Use ONLY when the principal explicitly asks to post a specific finished item to X — never proactively, never for reading X (that stays on reference-mesh/xfetch.py). Covers the xpost plugin (connect, draft, publish, status), the exact-preview approval gate before any publish, media attachment, and token/connection handling. Keywords: post to X, tweet, publish to Twitter, xpost, X connect, reply, quote tweet, attach media.
license: MIT
metadata:
  author: shift-labs-ai
  version: "1.0.0"
---

# x-post — posting a finished piece to X

Posting is a side tool. Muse is a music-video director; this capability exists
only to put an already-finished piece on X when the principal says to. Never suggest
posting, never post without his explicit OK on the exact draft, never batch or
schedule. Reading X is not this skill — use `reference-mesh/xfetch.py`.

## The one hard gate

`xpost.publish` runs ONLY after the principal approves the exact draft shown to him in
this chat. Flow, every time:

1. The principal asks to post a specific item.
2. Call `xpost.draft {...}` → get `{draftId, preview}`.
3. Show the principal the preview verbatim: the full text, the weighted character
   count, any reply/quote target, and each media file. Nothing paraphrased.
4. Wait for his explicit OK on THAT draft in the chat. Any edit → new
   `xpost.draft`, new preview, new approval. Silence or "maybe" is not an OK.
5. Only then `xpost.publish {draftId}`. Report the tweet id + URL back.

A draft is single-use: once published it cannot be republished. If he wants a
change after seeing the preview, draft again — never hand-edit and publish.

## Actions

- `xpost.status` → `{connected, handle, secondsUntilExpiry, needsRefresh}`.
  Check first; if `connected:false`, run the connect flow below.
- `xpost.connect.start` → `{authorizeUrl}`. Send the principal the authorize URL as
  its own message so he can open it. He authorizes, is redirected, and copies
  the FULL address-bar URL from the callback page.
- `xpost.connect.complete {callbackUrl}` → exchanges the code, stores tokens,
  returns the connected handle. State is single-use + 10-min TTL; if it fails,
  start a fresh `connect.start`.
- `xpost.draft {text, replyTo?, quoteOf?, mediaPaths?[]}` → validates (weighted
  length ≤280, media exists and within size caps) and stores. No network.
  `mediaPaths` are local files (≤4; images/gif/video). `replyTo`/`quoteOf` take
  a tweet id.
- `xpost.publish {draftId}` → uploads media, posts, returns `{tweetId, url}`,
  marks the draft used. Refuses unknown or already-used ids.

## Connection notes

- Public OAuth2 PKCE client — no client secret. The client id + redirect URI
  come from workspace secrets (by name only): `X_OAUTH2_CLIENT_ID`,
  `X_OAUTH2_REDIRECT_URI`.
- Tokens live in the workspace-local `.xpost/` store (git-ignored, chmod 600),
  never logged. X rotates the refresh token on every refresh; the plugin
  persists the new one under a lock — you do nothing for this.
- If `publish`/`status` ever reports a reconnect is required, run
  `connect.start` again and re-approve.

## Acceptance check

Done when: (1) the exact preview shown to the principal matches the published text and
media; (2) he gave an explicit OK on that draft before publish; (3) publish
returned a tweet id + URL, reported back to him; (4) no second publish of the
same draftId. If any is missing, it is not done.

See [LEARNINGS.md](LEARNINGS.md) for corrections learned in use.
