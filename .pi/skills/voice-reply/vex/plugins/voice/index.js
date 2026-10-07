// voice — speak an agent's reply as an MP3 (ElevenLabs v4 Turbo), fast.
//
// Action:
//   voice.say {text, voice?, language?, speed?} -> {path, seconds, ms, chars, est_usd}
//
// The call is synchronous (~1-5 s for a 30 s reply), so no job and no wake.
// The caller then sends `path` with send_file in the same turn. Vex has no
// media route for plugins yet (sessions.messages.send is text-only), so the
// plugin cannot post the file into the session by itself.
//
// Key: ELEVENLABS_API_KEY (by name). Files: <workspace>/outbox/voice/, kept 7 days.
// Usage log (for cost): <workspace>/.voice/usage.jsonl.

const fs = require("fs");
const path = require("path");

const API = "https://api.elevenlabs.io/v1";
const MODEL = "eleven_v4_turbo";
const DEFAULT_VOICE = "bIHbv24MWmeRgasZH58o"; // premade "Will"
const USD_PER_CHAR = 0.04 / 1000; // v4 Turbo list price
const MAX_CHARS = 5000;
const KEEP_MS = 7 * 24 * 3600 * 1000;

// The workspace: where send_file may read. Works from .runline/plugins/voice/ and from a skill's vex/plugins/voice/.
const ROOT = process.env.VEX_WORKSPACE_PATH ||
  (__dirname.includes(`${path.sep}.runline${path.sep}`) ? path.resolve(__dirname, "..", "..", "..") : process.cwd());
const OUT = path.join(ROOT, "outbox", "voice");
const LOG = path.join(ROOT, ".voice", "usage.jsonl");

// Light cleanup so markdown never reaches the voice. Writing for the ear is the caller's job.
function forTheEar(s) {
  return s
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\[([^\]]+)\]\((?:[^)]+)\)/g, "$1")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/[*_`#>|~]/g, "")
    .replace(/^\s*[-•]\s+/gm, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{2,}/g, "\n")
    .trim();
}

function prune() {
  try {
    const now = Date.now();
    for (const f of fs.readdirSync(OUT)) {
      const p = path.join(OUT, f);
      if (now - fs.statSync(p).mtimeMs > KEEP_MS) fs.unlinkSync(p);
    }
  } catch (_) {}
}

async function tts(key, voice, body) {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(`${API}/text-to-speech/${voice}?output_format=mp3_44100_128`, {
      method: "POST",
      headers: { "xi-api-key": key, "content-type": "application/json", accept: "audio/mpeg" },
      body: JSON.stringify(body),
    });
    if (res.ok) return Buffer.from(await res.arrayBuffer());
    const msg = (await res.text()).slice(0, 300);
    // 429/5xx are transient; a lone 401 under load was seen once and passed on retry.
    if (attempt < 2 && (res.status === 429 || res.status >= 500 || res.status === 401)) {
      await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
      continue;
    }
    throw new Error(`ElevenLabs ${res.status}: ${msg}`);
  }
}

module.exports = function voice(api) {
  api.setName("voice");
  api.setVersion("0.1.0");
  api.setConnectionSchema({
    apiKey: { type: "string", required: true, env: "ELEVENLABS_API_KEY", description: "ElevenLabs API key" },
  });

  api.registerAction("say", {
    access: "write",
    description:
      "Speak text as an MP3 voice reply (ElevenLabs v4 Turbo, ~1-5 s). Returns {path, seconds}. Then send_file the path in the same turn.",
    inputSchema: {
      text: { type: "string", required: true, description: "What to say, written for the ear (no lists, links or markdown). Max 5000 chars." },
      voice: { type: "string", required: false, description: "ElevenLabs voice ID. Default: Will (premade)." },
      language: { type: "string", required: false, description: "ISO 639-1 code, e.g. 'he' or 'en'. Default: auto-detect." },
      speed: { type: "number", required: false, description: "0.7-1.2. Default 1.1 (natural, a little quick)." },
    },
    async execute(input, ctx) {
      const t0 = Date.now();
      const key = ctx.connection.config.apiKey;
      const text = forTheEar(String(input.text || ""));
      if (!text) throw new Error("Nothing to say: text is empty after cleanup.");
      if (text.length > MAX_CHARS) throw new Error(`Text is ${text.length} chars; the limit is ${MAX_CHARS}. Say less.`);
      const body = {
        text,
        model_id: MODEL,
        voice_settings: { stability: 0.35, similarity_boost: 0.75, speed: input.speed || 1.1 },
        ...(input.language ? { language_code: input.language } : {}),
      };
      const mp3 = await tts(key, input.voice || DEFAULT_VOICE, body);
      fs.mkdirSync(OUT, { recursive: true });
      prune();
      const file = path.join(OUT, `reply-${new Date().toISOString().replace(/[:.]/g, "-")}.mp3`);
      fs.writeFileSync(file, mp3);
      const r = {
        path: file,
        seconds: Math.round((mp3.length * 8) / 128000 * 10) / 10, // CBR 128k
        ms: Date.now() - t0,
        chars: text.length,
        est_usd: Math.round(text.length * USD_PER_CHAR * 10000) / 10000,
      };
      try {
        fs.mkdirSync(path.dirname(LOG), { recursive: true });
        fs.appendFileSync(LOG, JSON.stringify({ ts: new Date().toISOString(), ...r, path: path.basename(file) }) + "\n");
      } catch (_) {}
      return r;
    },
  });
};
