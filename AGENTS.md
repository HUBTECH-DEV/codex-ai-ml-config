# HubICG configuration bootstrap

Before project work:

1. Run `python scripts/validate_codex_config.py --quiet`.
2. Read `.promptsConfig/codex-primary-context.md` completely and apply it.
3. Load `.promptsConfig/agentconfig.json`.
4. Consult `.promptsLibrary/role-index.json`.
5. Load only the selected role from `.promptsLibrary`.

Do not synchronize automatically. Running
`python scripts/sync_codex_config.py` without an action flag is read-only.
Fetch, pull, commit and push require the separate explicit flags `--fetch`,
`--pull`, `--commit` and `--push`, respectively, after user authorization.
This integration tree targets `beta`; pass `--branch beta` explicitly when a
mutation is authorized.

If remote access is unavailable, report it and use the last locally validated
configuration. Never expose credentials, rewrite history or force push.
