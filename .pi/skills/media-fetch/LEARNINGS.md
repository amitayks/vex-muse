# media-fetch — LEARNINGS (intent, not case study)

- 2026-10-27 · The YouTube block is the address, not the tool: yt-dlp, ytdl-core, youtubei.js, Steel and the
  data-center proxy all got "Sign in to confirm you're not a bot" from data-center addresses. Change the address.
- 2026-10-27 · One Modal container keeps its address across calls; use single-use containers and several
  regions, in parallel waves. Passing addresses in tests were mostly Google-cloud ranges (34.x).
- 2026-10-27 · Past the bot wall, formats still fail without a PO token ("Requested format is not available"):
  the bgutil script helper in the image fixes it. Use a sort (-S res:H) not a filter, because some client
  modes offer only combined formats.
- 2026-10-27 · Modal on this plan refuses cloud pinning ("Pinning cloud aws not supported"); region pinning works.
- 2026-10-27 · Tests: 4 of 4 runs succeeded in the first wave of 8, 15–60 s, a 13-min 720p lecture = 122 MB.
- 2026-10-27 · Default tries raised 16 → 32: a fresh-session acceptance run passed only on try 16 (15 addresses blocked).
