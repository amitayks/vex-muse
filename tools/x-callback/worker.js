// muse-x-callback: X OAuth2 redirect target for Vex agents (Muse's xpost plugin).
// Stateless: it never exchanges the code. It shows the full callback URL so the user can paste it
// back to the agent, which holds the PKCE verifier and completes the exchange itself.
const esc = s => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export default {
  async fetch(req) {
    const u = new URL(req.url);
    if (u.pathname !== '/x/callback') return new Response('muse-x-callback', { status: 404 });
    const err = u.searchParams.get('error'), ok = u.searchParams.get('code') && u.searchParams.get('state');
    const full = esc(u.toString());
    const body = ok
      ? `<h1>Almost done</h1><p>Copy this whole link and send it to Muse in WhatsApp:</p>
         <textarea id="u" readonly>${full}</textarea><button onclick="navigator.clipboard.writeText(document.getElementById('u').value);this.textContent='Copied ✓'">Copy link</button>
         <p class="s">The code inside works once and expires in about 30 seconds, so paste it right away.</p>`
      : `<h1>X did not connect</h1><p>${esc(err || 'No code in this link.')}</p><p class="s">Ask Muse for a fresh connect link and try again.</p>`;
    return new Response(`<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Connect X · Muse</title>
<style>body{font:17px/1.45 system-ui,sans-serif;max-width:560px;margin:40px auto;padding:0 18px;background:#f4efe6;color:#1d1a17}
h1{font-size:24px}textarea{width:100%;height:120px;font:13px monospace;padding:10px;border:1px solid #bbb;border-radius:8px;box-sizing:border-box}
button{margin-top:10px;font-size:17px;padding:10px 18px;border:0;border-radius:8px;background:#1d1a17;color:#fff}.s{color:#6b645c;font-size:14px}</style>${body}`,
      { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'referrer-policy': 'no-referrer' } });
  }
};
