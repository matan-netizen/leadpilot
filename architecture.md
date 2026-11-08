# architecture.md — LeadPilot (leads + smart reply)

The drawing, where each box runs, the limits, and every decision with its reason. Keep it current in the same commit as the change.

## Components

```
 Browser (UI)            Backend (FastAPI, one service)              Anthropic
 static/index.html  --->  /api/leads · /api/leads/{id}/smart-reply ->  Claude API
                    --->  /api/chat  --> agent loop --------------->  (or offline rules)
 app.js, styles.css <---  SSE stream <-- text + tool events          (model, per token)
                             |        \
                             |         tools: leads_overview · search_leads · get_lead · update_lead · create_lead · list_templates
                             v
                          Postgres (Railway plugin)  <---  cron service: python -m app.digest (07:30)
                          users · conversations · messages · runs · leads · lead_events · templates
```

Four layers, one external dependency. Everything on the left and in the middle is ours and runs on Railway; the model is rented per token.

## Flows

- **Chat turn.** UI posts `{conversation_id, message, image?}` → auth cookie checked → three limits checked → user message saved → system prompt (business name, today's date, lead count) + last 20 messages + current message → model stream. Text deltas are forwarded to the UI as they arrive. If the model asks for a tool, the backend runs it, appends the result, and calls the model again (max 6 rounds). At the end: one assistant message, one `runs` row with tokens and cost. A dropped connection saves no partial assistant message; the run is marked `aborted`.
- **Dashboard.** `GET /api/leads` returns every lead with server-computed flags (stage, hot, stale, needs_reply, duplicate); the UI filters, sorts and draws charts client-side. `PATCH /api/leads/{id}` changes only the fields sent and writes a `lead_events` row per change. Kanban drops send the stage's default status.
- **Smart reply.** `POST /api/leads/{id}/smart-reply` sends the lead card + the lead's last message to one tool-less model call (`prompts/smart_reply.md`), which returns JSON: reply, intent, suggested status, summary. Bad output or a model error falls back to the rule engine, so the rep always gets a draft. `POST /api/leads/{id}/sent` marks it answered and applies the status. Every call writes a `runs` row (cost cap).
- **Offline mode.** No `ANTHROPIC_API_KEY` → `MODEL_PROVIDER=offline`: `app/offline.py` speaks the same ModelClient protocol with keyword intents mapped to the same tools, and smart replies come from `smart_reply.rules_reply`. A fresh deploy is usable before a key exists.
- **Digest.** The cron service runs `app/digest.py`: new leads yesterday, hot, waiting for a reply, stale, AI spend; POSTs to `DIGEST_WEBHOOK_URL` if set.

## Storage

Postgres on Railway (`DATABASE_URL` from the plugin); SQLite locally and in tests. Tables and their keys:

| Table | Key | Notes |
|---|---|---|
| users | name (unique) | typed at login; no passwords per user |
| conversations | id | belongs to one user; title = first message |
| messages | id | role, text only; `has_image` flag; image bytes are never stored |
| runs | id | one per model turn: tokens, cost_usd, tool_calls, status, duration |
| leads | id · `phone_norm` (indexed) | phone normalised to 972…; status id or null; three follow-up texts; `last_incoming` + `replied` drive the reply inbox. Seeded from data/leads.json with relative dates |
| lead_events | id · lead_id | activity log: created, status, edit, note, incoming, ai_reply |
| templates | id | WhatsApp templates by lead type; seeded from data/templates.json |
| schema_version | version | 1; created with `create_all` at start |

## Model

`claude-opus-5-5`, effort `medium`, max 2,048 output tokens, adaptive thinking (the model's default). Server-side fallbacks on (`fallbacks: "default"`), so a safety refusal on the primary model is retried on a substitute before we show the user anything. System prompt cached (`cache_control`), tools first and stable so the prefix stays cacheable. Change the model or effort in Variables, not in code; run the evals after.

## Limits

| Layer | Number | Where enforced |
|---|---|---|
| Users → us | 30 messages per user per hour; images ≤ 5 MB | `app/limits.py`, before the model is called |
| Us → model | SDK retries with backoff on 429/529 (2 retries) | Anthropic SDK client |
| Us → wallet | $3.00 per local day across the app | `app/limits.py` from the `runs` table |
| Tool loop | max 6 model rounds per turn; tool results truncated at 12,000 chars | `app/agent.py` |

## Hosting

One Railway project, three things in it: the **web service**, built by Railway's default Railpack builder straight from `requirements.txt` with the Python version in `.python-version` (no Dockerfile), the **Postgres plugin**, and the **digest cron service** from the same repo (start command `python -m app.digest`, schedule `30 4 * * *`; Railway cron is UTC, so that is 07:30 Israel in summer and 06:30 in winter). All three are described in one file, `.railway/railway.ts` (Railway's Infrastructure as Code): start commands, the `/health` check, restart policies and the cron schedule. Railway does not read that file at deploy time; `railway config plan` shows the drift between the file and the project, and `railway config apply` applies it. The file does not manage variables: secrets live only in the Variables tab. The npm package under `.railway/` exists only so the CLI can evaluate the file, and it stays out of the repo root so Railpack keeps seeing a Python project. Deploy on push to `main`. Expected hosting cost: $4 to $6 a month (see README); the model bill is separate.

## Secrets

`ANTHROPIC_API_KEY`, `APP_PASSWORD`, `APP_SECRET`, `DATABASE_URL`, `CRON_SECRET`, `DIGEST_WEBHOOK_URL`. Locally in `.env` (gitignored); on Railway in the service's Variables tab, shared with the cron service through a reference variable. `.env.example` lists the names with no values. The grep test in practice.md must come back empty on every commit.

## Observability

- Railway logs per service (requests, errors, startup seed report).
- `runs` table: every model turn with status (`ok`, `refusal`, `error`, `aborted`), tokens and cost. The digest reads it.
- `GET /api/stats`: spend today vs cap, messages this hour.
- `evals/history.csv`: pass rate per run, per git sha, with tokens and cost.

## Decisions

| Date | Decision | Reason | Would change it if |
|---|---|---|---|
| 2026-10-17 | One service serves UI and API | Ten users; a CDN or a second service is cost and a second deploy for nothing | Traffic from the public web, or a separate frontend team |
| 2026-10-17 | Postgres over Airtable | Chat history grows fast; Airtable's record cap and rate limit would be hit within weeks | Non-developers must edit rows by hand daily |
| 2026-10-17 | Structured tools, no SQL from the model | Least access: the model can read leads and change only status / notes / last update, or create a deduplicated lead; it cannot delete | A genuine need for ad-hoc analysis the parameters cannot express |
| 2026-10-17 | Images not stored | Cheaper, smaller database, fewer privacy questions; the row is the record | A requirement to show the original screenshot later |
| 2026-10-17 | Shared password + typed name, not accounts | One business, ten people, no admin; per-user limits still work | A second client, or a client who wants per-person access control |
| 2026-10-17 | `create_all` + schema_version, no migration tool yet | Schema v1 has no history to migrate; keep the dependency list short | The first schema change after production data exists → add Alembic |
| 2026-10-17 | Digest as a Railway cron service, not an external pinger | Same repo, same variables, runs for seconds, costs cents | Railway removes cron, or the digest needs to run in several regions |
| 2026-10-27 | Railpack build, no Dockerfile | The Dockerfile only pinned Python and ran pip; Railway's default builder does the same from `requirements.txt` and `.python-version`, one file less to keep current | A system package (apt) or a multi-stage build is needed, or Railway drops Railpack |
| 2026-10-27 | Infrastructure as Code (`.railway/railway.ts`) instead of `railway.json` | Railway deprecated config-as-code files (they stop working on 2026-12-01); one IaC file describes both services, so the cron service needs no config path of its own | Railway changes the IaC format again, or a setting the DSL cannot express |
| 2026-11-04 | Chat history is resent as text only; the system prompt says earlier replies were tool-checked and must not be re-checked or retracted unasked | The first live chats showed the model, seeing its old figures without the tool calls behind them, re-running tools on unrelated turns and telling users their searches "never ran" (issue #2). A prompt rule fixes it with no schema change | The eval `no_recheck_after_off_topic` regresses → store a compact tool trace per message and replay it (a schema change, so add Alembic first) |
| 2026-10-28 | Public repository, history restarted as one commit | No secrets live in the code (they are in Variables) and the dataset is mock data; a fresh history keeps the owner's personal email out, and the old private repo is kept as `bakery-copilot-archive` | Real client data or client-specific configuration has to be committed |
| 2026-11-08 | Domain changed from bakery sales to leads + smart reply; UI rewritten in the leads-dashboard design (Hebrew RTL, same tokens) as plain HTML/CSS/JS | Keeps one service and no build step on Railway, while matching the reference look | The UI grows past what one script can hold → move to Vite + React like the reference |
| 2026-11-08 | Statuses/stages defined once in `app/leads_meta.py` and served to the UI via `/api/meta` | One source of truth for labels, tones, next actions and templates | Statuses must be editable by the business without a deploy |
| 2026-11-08 | Offline rule engine when no API key | The app is demonstrable and useful from the first deploy; the key is a switch, not a requirement | Rules start giving answers worse than "no answer" |
| 2026-11-08 | Smart reply is a separate one-shot JSON call, not an agent turn | Faster and cheaper (no tools, short output), easy to validate and to fall back from | Replies need data from other leads or tools |
