---
kind: technique
tags: [mac, local-muse, blender, dispatch]
audience: all
half_life: 60
rights: safe
seen: 2026-10-13
summary: "Optional: a local copy of Muse on the principal's Mac (Local Muse) for Blender, GPU renders and long jobs - the TASK protocol, the report formats, file exchange, the split of work with the server copy, and health checks learned in the first Blender labs."
---

# Local Muse — an optional helper on the principal's Mac

Local Muse is a copy of Muse that runs in Vex Desktop on the principal's Mac, with Muse's skills,
knowledge and studio files plus a Mac bridge skill. Muse itself runs on the server workspace. The
server box has no GPU and no Blender; the Mac has both. Set this up only if a Mac is available; every
id below is a placeholder for your own deployment.

## The reference machine
| item | value |
|---|---|
| Chip | Apple M5 Pro: 15-core CPU, 16-core GPU (Metal 4) |
| RAM | 48 GB |
| Blender | 5.2.2 LTS, headless as `blender -b` |
| Python | system `python3` has no numpy; scripts that need it run in Blender's bundled Python |

Render speeds on this Mac and the Cycles-first rule are in [[tool-selection]] (the Blender row).
Render settings per job, draft checks and look fixes are in [[blender-field-notes]].

## What it can do that the server cannot
- Full control of the Mac: any app (Blender, QuickTime, browsers), clicks, keys, screenshots, screen recordings.
- Local GPU renders and long jobs, with no server time limit.
- The principal's local files and logged-in apps.
- Web forms in a real browser. A form that rejected an API submission from the server
  (`INVALID_SIGNATURE`) went through once in Local Muse's headless Chrome, with a marker file to block a
  second submit and the thank-you screen saved as proof.
- It has no copy of the server's sensors or schedules. Muse on the server owns those.

## How Muse gives it a task
Post one message in the Mac inbox session (`<mac-inbox-session-id>`) with `vex.sessions.messages.send`.
The bridge on the Mac holds a WebSocket on that session and opens a new local chat `G · <name>` for the
task in about 0.5 s.

| Message | Effect on the Mac |
|---|---|
| `TASK <name> reply:<sessionId>: <goal, context, acceptance check>` | New chat `G · <name>`; it reports back to session `<sessionId>`. |
| `TASK <name> @<macSid>: <text>` | Follow-up into that chat. It keeps its memory. |
| `MSG @<macSid>: <text>` | Free-form message into that chat. |

- One TASK per message. `<name>` is short: letters, digits, `-`, `_`, `.`.
- Use the id of the current session for `reply:`. Without `reply:` the report goes to the inbox.
- The envelope `<message id>` is a message id, not the session id. To find the current session id, call
  `vex.sessions.list`, then `vex.sessions.get` on each web candidate, and pick the one whose
  `firstSeenAt` or `lastSeenAt` matches the time of the current message.
- Each task carries an acceptance check. Give file paths, the brief and the deliverable shape.
- `vex.sessions.messages.send` only stores the text; the Mac service does the dispatch.
- Use one inbox per agent. Do not send the same work through two inboxes: each bridge keeps its own
  task state and locks, so the task runs twice. Do not post into another agent's inbox; a second sender
  there mixes up where the replies go.
- A new `TASK <name>` without `@<macSid>` opens a new chat, even when the name already exists.
- Two tasks can run at the same time, each in its own chat.

## How it reports
A report arrives in the `reply:` session as a new message and starts a turn there. It can show under the
principal's name, so identify it by its first word, not by the caller:
- `PROGRESS <name> @<macSid>`: an interim result with proof; the task still runs.
- `DONE <name> @<macSid>` or `BLOCKED <name> @<macSid> <reason>`, then proof, then one impact line.
- `REPLY <name> @<macSid> <answer>` for a free-form answer.

A report turn on the web platform answers in the web view only. To tell the principal on a phone
channel, send the line with `vex.sessions.messages.send` to that channel's session.

Match a report to its task by `@<macSid>` first: a follow-up keeps the chat's first name. A report can
arrive twice; treat the second one as a duplicate.

## Files between the machines
The Mac cannot receive a file push from the server. To share a file, put it at a URL the Mac can fetch,
or tell the local chat to pull it from the server workspace through RPC (`workspaces.readFile`). The Mac
sends files back the same way: it writes into Muse's workspace through RPC, checks each file with a
read-back sha256, and gives the paths in its report.

## Split of work
The first Blender lab ([[lab-blender]]) used this split, after the principal's Blender-first rule
([[tool-selection]]):
- Local Muse builds, animates and renders the Blender scenes. It makes no paid calls, because the
  project ledger lives on the server.
- Muse on the server directs, reviews each stage, and runs the paid paint pass ([[render-repaint]]), the
  audio, the composite and the final review.
- Local Muse works on a copy of any source project under its own folder, never in the original. A saved
  `.blend` keeps its `render.filepath`: set it before any render, or the frames go into the original
  project folder. The DONE report proves the source is untouched (no changed file since the task
  started, the same `.blend` sha256).

A scene built entirely from Python (one `build.py` plus modules, no add-ons, image textures or HDRI,
quality and camera flags on the command line) is the best reference shape for a Blender project the
agents can rebuild: `blender -b --factory-startup --python build.py -- --quality draft --camera hero`.

## Health
- **Keep the charger on and the lid open during long work.** On battery, overnight renders drained the
  Mac to 1 % and it slept for over 2 hours; a job with a time limit expired during the sleep. A closed
  lid sleeps the Mac even under `caffeinate` (a render stopped for 6.7 min and went on with no lost
  frames when the lid opened). The local chat did not resume its task after a wake; a follow-up TASK did.
- **A DONE or BLOCKED report ends the local chat's run.** For a multi-stage task, ask for PROGRESS lines
  and DONE only after the last deliverable. After a BLOCKED, send a follow-up TASK once the cause is fixed.
- **Bridge delivery is not proof that a run started.** A local chat once stopped, and later tasks got no
  run for about 20 hours (cause not found) while the Mac stayed awake. Ask for an answer within minutes;
  when two pings in a row get none, ask the principal to look at the Mac. A read-only ping in a new chat
  can read the stuck chat's runs and the bridge log.
- **A report can land with no turn acting on it** (the receiving turn failed at the model provider).
  Before chasing a stall, check the deliverable folder and the session history.
- **Watches on the server:** set them every 45–60 min during a chain, created in advance from a normal
  turn. A watch cannot renew itself from inside a scheduled run (`schedules.create` was refused there).
  After the first tick of a new schedule, check that `nextRunAt` moved; one hourly schedule with a
  TZID start and a UTC `UNTIL` fired once and stopped.
- **Keep work files out of `/tmp` on macOS.** macOS clears it at boot, and a `.blend` saved there loses
  its relative texture paths ([[blender-field-notes]], Draft checks).
- **The server clock runs on UTC.** A `find -newermt "<time>"` cutoff written in local time misses
  files; write the cutoff in UTC or add the offset (`"2026-10-12 00:30 +0300"`).

## Set-up notes for a fork
- Install Vex Desktop on the Mac, copy this workspace's skills, knowledge and studio into the local
  workspace, and register the Mac bridge with Muse as its default agent on one inbox session.
- Put the inbox session id in `AGENTS.md` (the optional local-helper paragraph) and nowhere else.
- Never share credentials between the machines through chat; each side gets its own keys through
  secure links.
