# tickets.md — LeadPilot work plan

Each ticket has a "Done when" line that a test or a manual check can prove. `scripts/create_issues.sh` turns this list into GitHub Issues with milestones and labels. ✅ = shipped.

## v1 — Leads dashboard

| # | Ticket | Done when | |
|---|---|---|---|
| 1 | Leads domain: 12 statuses, 6 stages, phone normalisation | `normalize_phone` passes all formats in `test_tools.py`; stages map 1:1 to statuses | ✅ |
| 2 | Database: leads, lead_events, templates + demo seed | first start logs `leads_seeded: 32, templates_seeded: 7`; a redeploy logs zeros | ✅ |
| 3 | Leads REST API (list, get, create, patch) | only sent fields change; every change writes a `lead_events` row; duplicate phone → 409 | ✅ |
| 4 | Overview: KPI tiles, funnel, status split, "today", data quality | clicking a tile or a bar opens the table with that filter | ✅ |
| 5 | Leads table: search, filters, sort, CSV | search finds a phone in any format; CSV opens in Excel with Hebrew | ✅ |
| 6 | Kanban with drag & drop | dropping a card sets the stage's default status and persists | ✅ |
| 7 | Lead drawer: next action, template, edit form, activity log | Save is enabled only after a change; the log shows who changed what | ✅ |
| 8 | Hebrew RTL design, dark mode, mobile | no horizontal scroll at 390 px; theme choice survives reload | ✅ |

## v2 — AI

| # | Ticket | Done when | |
|---|---|---|---|
| 9 | Agent tools: overview, search, get, update, create, templates | tool loop test updates a lead through `update_lead` and logs one run | ✅ |
| 10 | System prompt for the sales assistant | the prompt names the business and today's date; no `{{` left | ✅ |
| 11 | Smart reply: one-shot JSON call + rules fallback | bad model output still returns a draft; no invented prices (eval) | ✅ |
| 12 | Reply inbox with send-to-WhatsApp and status apply | "send" marks the lead answered and removes it from the inbox | ✅ |
| 13 | Offline rules mode when no API key | the app answers "מה לטפל היום?" with tools and no key | ✅ |
| 14 | Evals for the agent (`evals/cases.yaml`) | `python -m evals.run --baseline 0.8` passes | ✅ |

## v3 — Production

| # | Ticket | Done when | |
|---|---|---|---|
| 15 | Deploy on Railway: web + Postgres + health check | `/health` 200 on the public URL; data survives a redeploy | ✅ |
| 16 | Limits: per-user hourly, daily $ cap, upload size | 31st message → 429; cap reached → 402 | ✅ |
| 17 | Wrong-password message on login (lecturer feedback) | wrong password shows "סיסמה שגויה." and not "יש להתחבר" | ✅ |
| 18 | Explain every error with its source (payment / settings / Anthropic / bug) | each error class in `test_degraded.py` names its source; no raw JSON reaches the UI | ✅ |
| 19 | CI: lint + tests on every push, evals on PRs | the badge in README is green | ✅ |

## Next

| # | Ticket | Done when |
|---|---|---|
| 20 | Morning digest as a Railway cron service | the digest arrives on the webhook at 07:30 |
| 21 | Import leads from CSV / Airtable | a CSV with 100 rows imports with duplicates reported, not created |
| 22 | WhatsApp Business API: receive messages into the reply inbox | an incoming WhatsApp message appears in "ממתינים למענה" within a minute |
| 23 | Per-user roles (owner / rep) | a rep cannot change the daily cap or delete data |
| 24 | Alembic migrations | the first schema change after go-live runs as a migration |
