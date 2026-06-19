# Changelog

## [0.1.0] - 2026-06-19

### Added
- Initial plugin scaffold (`plugin.json`, `README.md`, `CHANGELOG.md`).
- `src/scout_daemon.py` — 24-hour lookback + real-time `gcloud alpha logging tail` stream for Dataform errors.
- `src/skills/fix_dataform.md` — Claude Code skill for analysing and patching failing `.sqlx` files.
- `/scout` slash command registered in the plugin manifest.
