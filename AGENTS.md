# Codex configuration bootstrap

Before project work:

1. Run `python scripts/validate_codex_config.py --quiet`.
2. If `origin` is reachable, run `python scripts/sync_codex_config.py`.
3. Read `.promptsConfig/codex-primary-context.md` completely and apply it.
4. Load `.promptsConfig/agentconfig.json`.
5. Load only the selected role from `.promptsLibrary`.

If synchronization is unavailable, report it and use the last locally
validated configuration. Never expose credentials or force push.
