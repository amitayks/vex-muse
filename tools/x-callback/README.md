# muse-x-callback
Stateless X OAuth2 redirect page (a tiny Cloudflare worker you deploy on your own account), e.g.
`https://muse-x-callback.<your-subdomain>.workers.dev/x/callback`. It shows the full callback URL to paste back to Muse;
the xpost plugin (which holds the PKCE verifier) completes the exchange. Register that URL as a Callback URI in your X app,
then set workspace variables `X_OAUTH2_CLIENT_ID` and `X_OAUTH2_REDIRECT_URI`.
Deploy: `PUT /accounts/<account>/workers/scripts/muse-x-callback` (module upload of `worker.js`), or `wrangler deploy`.
