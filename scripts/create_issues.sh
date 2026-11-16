#!/usr/bin/env bash
# Create the open tickets from docs/tickets.md ("Next") as GitHub Issues with a milestone and labels.
# Run once, from the repo root, after `gh auth login`. Shipped tickets (✅) are not recreated.
set -euo pipefail

for label in feature bug chore; do gh label create "$label" --force >/dev/null 2>&1 || true; done
gh api -X POST repos/:owner/:repo/milestones -f title="v4 growth" >/dev/null 2>&1 || true

create() { # label, title, body
  gh issue create --milestone "v4 growth" --label "$1" --title "$2" --body "Done when: $3" >/dev/null && echo "created: $2"
}

create feature "Morning digest as a Railway cron service" "the digest arrives on the webhook at 07:30."
create feature "Import leads from CSV / Airtable" "a CSV with 100 rows imports with duplicates reported, not created."
create feature "WhatsApp Business API: receive messages into the reply inbox" "an incoming WhatsApp message appears in the inbox within a minute."
create feature "Per-user roles (owner / rep)" "a rep cannot change the daily cap or delete data."
create chore   "Alembic migrations" "the first schema change after go-live runs as a migration."
