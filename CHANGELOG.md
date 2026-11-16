# Changelog

All notable changes to LeadPilot. Format: [Keep a Changelog](https://keepachangelog.com), versions: [SemVer](https://semver.org).

## [1.2.0] — 2026-11-16

### Added
- `app/errors.py`: every failure is classified by source (payment, account settings, Anthropic, network, deliberate limit, the system) and explained in Hebrew with what to do.
- Header badge shows why Claude is unavailable ("no credit – not a system fault").
- Automatic fallback to rules mode on account problems (no credit, bad key) and transient Anthropic errors; Claude is retried every 5 minutes.
- ruff lint in CI, `pyproject.toml`, CHANGELOG, README screenshots and architecture diagram.

### Fixed
- Login with a wrong password showed "יש להתחבר" instead of "סיסמה שגויה" (lecturer feedback).
- Raw API error JSON no longer reaches the UI.

## [1.1.0] — 2026-11-08

### Added
- Deployed on Railway (web + PostgreSQL, health check, continuous deploy from `main`).

## [1.0.0] — 2026-11-08

### Added
- Leads domain: 12 statuses in 6 stages, phone normalisation, hot / stale / duplicate / needs-reply rules.
- Leads REST API with an activity log for every change.
- Hebrew RTL dashboard: overview, table, Kanban with drag & drop, lead drawer, templates, dark mode, mobile.
- Smart reply: one-shot JSON model call per lead message, with a rules fallback.
- Sales assistant agent with six lead tools; offline rules mode without an API key.
- Tests and evals rewritten for leads.

### Changed
- Built on Bakery Copilot (course project): the bakery sales and invoice domain was replaced end to end.
