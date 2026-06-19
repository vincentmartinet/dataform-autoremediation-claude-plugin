# Changelog

## [0.2.0] - 2026-06-19

### Added
- `SessionStart` hook (`src/hooks/hooks.json` + `src/hooks/session-start.sh`) — auto-starts the scout daemon on session open with a PID-file single-instance guard.
- ADR directory (`docs/adr/`) with MADR template and two initial records:
  - ADR-0001: Plugin architecture (Python daemon + Claude Code skill)
  - ADR-0002: SessionStart hook with single-instance guard

### Changed
- `src/scout_daemon.py` — daemon now removes `/tmp/dataform-scout.pid` on graceful shutdown.
- `plugin.json` — registered `hooks` field pointing to `src/hooks/hooks.json`.
- `CLAUDE.md` — added workflow rule to commit after every completed task.

---

## [0.1.0] - 2026-06-19

### Added
- Initial plugin scaffold (`plugin.json`, `README.md`, `CHANGELOG.md`).
- `src/scout_daemon.py` — 24-hour lookback + real-time `gcloud alpha logging tail` stream for Dataform errors.
- `src/skills/fix_dataform.md` — Claude Code skill for analysing and patching failing `.sqlx` files.
- `/scout` slash command registered in the plugin manifest.
