// xpost — minimal X (Twitter) posting plugin for Muse.
// Side utility only: Muse is a music-video director; posting is secondary and
// only on the principal's explicit request. Basic posting on X API v2 as a PUBLIC
// OAuth2 PKCE client (no client secret). NO Cloudflare/D1/R2, NO multi-tenant,
// NO scheduler. Token + draft state live in a local file store `.xpost/`
// (chmod 600), never in git, never logged.
//
// Actions:
//   connect.start                 -> PKCE authorize URL (state persisted)
//   connect.complete {callbackUrl}-> exchange code, store rotating tokens
//   draft {text, replyTo?, quoteOf?, mediaPaths?[]} -> validate + store (no net)
//   publish {draftId}             -> post the stored draft once, return id+url
//   status                        -> connected handle + token freshness

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const X_AUTHORIZE_URL = "https://x.com/i/oauth2/authorize";
const X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token";
const X_API_V2 = "https://api.twitter.com/2";
const X_MEDIA_UPLOAD = "https://api.x.com/2/media/upload";
const X_SCOPES = "tweet.read tweet.write users.read offline.access media.write";
const STATE_TTL_MS = 10 * 60 * 1000;
const REFRESH_SKEW_MS = 60 * 1000;

// Media caps by category (bytes). X: photo 5MB, gif 15MB, video 512MB.
const MEDIA_CAPS = {
  tweet_image: 5 * 1024 * 1024,
  tweet_gif: 15 * 1024 * 1024,
  tweet_video: 512 * 1024 * 1024,
};

// ---------------------------------------------------------------- file store
function storeDir() {
  // Plugin dir: .../.runline/plugins/xpost/ -> workspace root is 4 levels up.
  return path.resolve(__dirname, "..", "..", "..", ".xpost");
}
function ensureStore() {
  const dir = storeDir();
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  try { fs.chmodSync(dir, 0o700); } catch (_) {}
  return dir;
}
function fp(name) { return path.join(ensureStore(), name); }
function readJson(name, fallback) {
  try {
    const raw = fs.readFileSync(fp(name), "utf8");
    return JSON.parse(raw);
  } catch (_) { return fallback; }
}
function writeJson(name, obj) {
  const f = fp(name);
  fs.writeFileSync(f, JSON.stringify(obj, null, 2), { mode: 0o600 });
  try { fs.chmodSync(f, 0o600); } catch (_) {}
}

// ------------------------------------------------------------------- locking
// Atomic dir-based lock so two concurrent refreshes never clobber the rotating
// refresh token. mkdir is atomic; caller must release in finally.
async function withLock(fn, timeoutMs = 15000) {
  const lockDir = path.join(ensureStore(), ".lock.d");
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    try { fs.mkdirSync(lockDir); break; }
    catch (e) {
      if (e.code !== "EEXIST") throw e;
      // Break a stale lock older than 2x timeout (a crashed holder).
      try {
        const age = Date.now() - fs.statSync(lockDir).mtimeMs;
        if (age > 2 * timeoutMs) { fs.rmdirSync(lockDir); continue; }
      } catch (_) {}
      if (Date.now() > deadline) throw new Error("xpost: token lock timeout");
      await new Promise((r) => setTimeout(r, 100));
    }
  }
  try { return await fn(); }
  finally { try { fs.rmdirSync(lockDir); } catch (_) {} }
}

// --------------------------------------------------------------------- pkce
function base64url(buf) {
  return Buffer.from(buf).toString("base64")
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function generatePkce() {
  const verifier = base64url(crypto.randomBytes(32));
  const challenge = base64url(crypto.createHash("sha256").update(verifier).digest());
  return { verifier, challenge };
}

// ------------------------------------------------------------------- config
function clientConfig(ctx) {
  const cfg = ctx.connection.config || {};
  const clientId = cfg.clientId;
  const redirectUri = cfg.redirectUri;
  if (!clientId) throw new Error("X_OAUTH2_CLIENT_ID is not set in the runtime environment.");
  if (!redirectUri) throw new Error("X_OAUTH2_REDIRECT_URI is not set in the runtime environment.");
  return { clientId, redirectUri };
}

// ------------------------------------------------- weighted length (approx.)
// Twitter weighted length approximation: URLs count as 23; CJK/Kana/Hangul
// code points count as 2; everything else 1. Good enough to guard the 280 cap.
const URL_RE = /https?:\/\/[^\s]+/g;
function isWide(cp) {
  return (
    (cp >= 0x1100 && cp <= 0x115f) ||   // Hangul Jamo
    (cp >= 0x2e80 && cp <= 0x9fff) ||   // CJK
    (cp >= 0xa000 && cp <= 0xa4cf) ||   // Yi
    (cp >= 0xac00 && cp <= 0xd7a3) ||   // Hangul syllables
    (cp >= 0xf900 && cp <= 0xfaff) ||   // CJK compat
    (cp >= 0xff00 && cp <= 0xff60) ||   // Fullwidth
    (cp >= 0x1f000 && cp <= 0x1ffff) || // emoji/symbols supplementary
    (cp >= 0x20000 && cp <= 0x3ffff)    // CJK ext
  );
}
function weightedLength(text) {
  const urls = text.match(URL_RE) || [];
  const stripped = text.replace(URL_RE, "");
  let w = urls.length * 23;
  for (const ch of stripped) w += isWide(ch.codePointAt(0)) ? 2 : 1;
  return w;
}

// --------------------------------------------------------------- token core
function loadTokens() { return readJson("tokens.json", null); }
function saveTokens(tok) { writeJson("tokens.json", tok); }

async function refreshTokens(clientId, tok) {
  const res = await fetch(X_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: tok.refreshToken,
      client_id: clientId,
    }).toString(),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || !body.access_token || !body.refresh_token) {
    const msg = body.error_description || body.error || `X token refresh failed (HTTP ${res.status})`;
    const dead = res.status >= 400 && res.status < 500 &&
      (body.error === "invalid_grant" || body.error === "invalid_request" ||
       /token was invalid/i.test(body.error_description || ""));
    throw new Error(dead ? `X reconnect required: ${msg}` : msg);
  }
  return {
    ...tok,
    accessToken: body.access_token,
    refreshToken: body.refresh_token, // X ROTATES the refresh token — persist it.
    accessTokenExpiresAt: Date.now() + (body.expires_in ?? 7200) * 1000,
  };
}

// Return a fresh access token, refreshing + persisting under lock if needed.
async function validAccessToken(clientId) {
  return withLock(async () => {
    let tok = loadTokens();
    if (!tok) throw new Error("Not connected — run xpost.connect.start first.");
    if (tok.accessTokenExpiresAt - Date.now() < REFRESH_SKEW_MS) {
      tok = await refreshTokens(clientId, tok);
      saveTokens(tok);
    }
    return tok.accessToken;
  });
}

async function xFetch(clientId, url, init = {}) {
  let token = await validAccessToken(clientId);
  const build = (t) => ({ ...init, headers: { ...(init.headers || {}), Authorization: `Bearer ${t}` } });
  let res = await fetch(url, build(token));
  if (res.status === 401) {
    // Force-refresh once, then retry.
    await withLock(async () => {
      const tok = loadTokens();
      if (tok) saveTokens(await refreshTokens(clientId, tok));
    });
    token = await validAccessToken(clientId);
    res = await fetch(url, build(token));
  }
  return res;
}

// -------------------------------------------------------------------- media
function mediaCategory(p) {
  const ext = path.extname(p).toLowerCase();
  if (ext === ".gif") return "tweet_gif";
  if ([".mp4", ".mov", ".m4v"].includes(ext)) return "tweet_video";
  if ([".jpg", ".jpeg", ".png", ".webp"].includes(ext)) return "tweet_image";
  throw new Error(`Unsupported media type: ${ext || "(none)"} for ${p}`);
}
function validateMedia(mediaPaths) {
  const out = [];
  for (const raw of mediaPaths) {
    const p = path.isAbsolute(raw) ? raw : path.resolve(storeDir(), "..", raw);
    if (!fs.existsSync(p)) throw new Error(`Media file not found: ${raw}`);
    const cat = mediaCategory(p);
    const size = fs.statSync(p).size;
    if (size > MEDIA_CAPS[cat]) {
      throw new Error(`Media ${raw} is ${(size / 1048576).toFixed(1)}MB, over the ${(MEDIA_CAPS[cat] / 1048576)}MB limit for ${cat}.`);
    }
    out.push({ path: p, category: cat, size });
  }
  return out;
}
async function uploadMedia(clientId, m) {
  const buf = fs.readFileSync(m.path);
  const form = new FormData();
  form.append("media", new Blob([buf]), path.basename(m.path));
  form.append("media_category", m.category);
  const res = await xFetch(clientId, X_MEDIA_UPLOAD, { method: "POST", body: form });
  if (!res.ok) throw new Error(`X media upload error ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  const id = data?.data?.id || data?.media_id_string;
  if (!id) throw new Error("X media upload returned no media id");
  return id;
}

// =========================================================== plugin surface
module.exports = function xpost(api) {
  api.setName("xpost");
  api.setVersion("0.1.0");

  api.setConnectionSchema({
    clientId: { type: "string", required: true, env: "X_OAUTH2_CLIENT_ID",
      description: "X OAuth2 public client id (your-account)." },
    redirectUri: { type: "string", required: true, env: "X_OAUTH2_REDIRECT_URI",
      description: "Registered X OAuth2 redirect URI (callback the user returns from)." },
  });

  api.registerAction("connect.start", {
    access: "read",
    description: "Begin X OAuth2 PKCE connect. Returns the x.com authorize URL to open; persists single-use state.",
    inputSchema: {},
    async execute(_input, ctx) {
      const { clientId, redirectUri } = clientConfig(ctx);
      const state = crypto.randomUUID();
      const { verifier, challenge } = generatePkce();
      const states = readJson("pkce.json", {});
      // prune expired states
      const now = Date.now();
      for (const s of Object.keys(states)) if (now - states[s].createdAt > STATE_TTL_MS) delete states[s];
      states[state] = { codeVerifier: verifier, createdAt: now };
      writeJson("pkce.json", states);
      const params = new URLSearchParams({
        response_type: "code",
        client_id: clientId,
        redirect_uri: redirectUri,
        scope: X_SCOPES,
        state,
        code_challenge: challenge,
        code_challenge_method: "S256",
      });
      return { authorizeUrl: `${X_AUTHORIZE_URL}?${params.toString()}`, redirectUri };
    },
  });

  api.registerAction("connect.complete", {
    access: "write",
    description: "Finish X connect from the pasted callback URL: validate state, exchange the code, store rotating tokens. Returns the connected handle.",
    inputSchema: {
      callbackUrl: { type: "string", required: true, description: "The full callback URL (or query string) after authorizing." },
    },
    async execute(input, ctx) {
      const { clientId, redirectUri } = clientConfig(ctx);
      const pasted = String(input.callbackUrl || "").trim();
      let qs;
      try { qs = new URL(pasted).searchParams; }
      catch (_) { qs = new URLSearchParams(pasted.replace(/^\?/, "")); }
      const code = qs.get("code");
      const state = qs.get("state");
      if (!code || !state) throw new Error("Pasted URL carries no code/state — copy the FULL address-bar URL after authorizing.");
      const states = readJson("pkce.json", {});
      const entry = states[state];
      if (!entry) throw new Error("Unknown, expired, or already-used state — start a fresh connect.");
      delete states[state]; // single use
      writeJson("pkce.json", states);
      if (Date.now() - entry.createdAt > STATE_TTL_MS) throw new Error("State expired — start a fresh connect.");
      const res = await fetch(X_TOKEN_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "authorization_code",
          code,
          redirect_uri: redirectUri,
          client_id: clientId,
          code_verifier: entry.codeVerifier,
        }).toString(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body.access_token || !body.refresh_token) {
        throw new Error(body.error_description || body.error || `X token exchange failed (HTTP ${res.status})`);
      }
      const tok = {
        accessToken: body.access_token,
        refreshToken: body.refresh_token,
        accessTokenExpiresAt: Date.now() + (body.expires_in ?? 7200) * 1000,
        connectedAt: Date.now(),
      };
      saveTokens(tok);
      // Resolve the handle for a friendly status; non-fatal if it fails.
      try {
        const me = await xFetch(clientId, `${X_API_V2}/users/me?user.fields=id,username,name`, { method: "GET" });
        if (me.ok) {
          const d = (await me.json()).data;
          if (d) { tok.handle = d.username; tok.userId = d.id; tok.name = d.name; saveTokens(tok); }
        }
      } catch (_) {}
      return { connected: true, handle: tok.handle || null, userId: tok.userId || null };
    },
  });

  api.registerAction("draft", {
    access: "write",
    description: "Validate and store an X post draft (no network). Checks weighted length <=280 and media existence/size. Returns {draftId, preview}.",
    inputSchema: {
      text: { type: "string", required: true, description: "Post text." },
      replyTo: { type: "string", required: false, description: "Tweet id to reply to." },
      quoteOf: { type: "string", required: false, description: "Tweet id to quote." },
      mediaPaths: { type: "array", required: false, description: "Local file paths to attach (images/gif/video)." },
    },
    async execute(input) {
      const text = String(input.text || "");
      if (!text.trim()) throw new Error("Draft text is empty.");
      const weighted = weightedLength(text);
      if (weighted > 280) throw new Error(`Draft is ${weighted} weighted characters, over the 280 limit.`);
      const mediaPaths = Array.isArray(input.mediaPaths) ? input.mediaPaths : [];
      if (mediaPaths.length > 4) throw new Error("X allows at most 4 media items per post.");
      const media = validateMedia(mediaPaths);
      const draftId = "dft-" + crypto.randomBytes(4).toString("hex");
      const drafts = readJson("drafts.json", {});
      drafts[draftId] = {
        text, replyTo: input.replyTo || null, quoteOf: input.quoteOf || null,
        mediaPaths: media.map((m) => m.path), createdAt: Date.now(), used: false, tweetId: null,
      };
      writeJson("drafts.json", drafts);
      const preview = {
        text, weighted, replyTo: input.replyTo || null, quoteOf: input.quoteOf || null,
        media: media.map((m) => ({ path: m.path, category: m.category, sizeKB: Math.round(m.size / 1024) })),
      };
      return { draftId, preview };
    },
  });

  api.registerAction("publish", {
    access: "write",
    description: "Post exactly the stored draft to X (single use). Uploads any media, returns the tweet id + URL, and marks the draft used. Refuses unknown or already-used ids.",
    inputSchema: {
      draftId: { type: "string", required: true, description: "The draftId returned by xpost.draft." },
    },
    async execute(input, ctx) {
      const { clientId } = clientConfig(ctx);
      const draftId = String(input.draftId || "");
      const drafts = readJson("drafts.json", {});
      const d = drafts[draftId];
      if (!d) throw new Error(`Unknown draftId: ${draftId}`);
      if (d.used) throw new Error(`Draft ${draftId} was already published (tweet ${d.tweetId}).`);
      if (!loadTokens()) throw new Error("Not connected — run xpost.connect.start first.");

      // Upload media (validate again — file may have changed since draft).
      let mediaIds;
      if (d.mediaPaths && d.mediaPaths.length) {
        const media = validateMedia(d.mediaPaths);
        mediaIds = [];
        for (const m of media) mediaIds.push(await uploadMedia(clientId, m));
      }

      const bodyObj = { text: d.text };
      if (d.replyTo) bodyObj.reply = { in_reply_to_tweet_id: d.replyTo };
      if (d.quoteOf) bodyObj.quote_tweet_id = d.quoteOf;
      if (mediaIds && mediaIds.length) bodyObj.media = { media_ids: mediaIds };

      const res = await xFetch(clientId, `${X_API_V2}/tweets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bodyObj),
      });
      if (!res.ok) throw new Error(`X post error ${res.status}: ${(await res.text()).slice(0, 300)}`);
      const tweetId = (await res.json())?.data?.id;
      if (!tweetId) throw new Error("X post returned no tweet id.");

      d.used = true; d.tweetId = tweetId; d.publishedAt = Date.now();
      drafts[draftId] = d;
      writeJson("drafts.json", drafts);
      const tok = loadTokens();
      const handle = tok?.handle;
      const url = handle ? `https://x.com/${handle}/status/${tweetId}` : `https://x.com/i/status/${tweetId}`;
      return { tweetId, url };
    },
  });

  api.registerAction("status", {
    access: "read",
    description: "Report X connection: connected account handle and access-token freshness (secondsUntilExpiry, needsRefresh). No network call.",
    inputSchema: {},
    async execute() {
      const tok = loadTokens();
      if (!tok) return { connected: false };
      const secondsUntilExpiry = Math.round((tok.accessTokenExpiresAt - Date.now()) / 1000);
      return {
        connected: true,
        handle: tok.handle || null,
        userId: tok.userId || null,
        accessTokenExpiresAt: new Date(tok.accessTokenExpiresAt).toISOString(),
        secondsUntilExpiry,
        needsRefresh: secondsUntilExpiry < 60,
        hasRefreshToken: !!tok.refreshToken,
      };
    },
  });
};
