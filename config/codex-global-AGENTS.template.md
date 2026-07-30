# Global HubICG configuration bootstrap

Use `{{CONFIG_REPO}}` as the central intent and context governance repository.
The directory may retain the legacy alias `codex-ai-ml-config`; treat that as a
filesystem compatibility path, not as the active framework identity.

Before project work:

1. Validate the repository:

   ```text
   python "{{CONFIG_REPO}}/scripts/validate_codex_config.py" --quiet
   ```

2. Read `{{CONFIG_REPO}}/.promptsConfig/codex-primary-context.md` completely
   and apply it as the primary project context, subject to system/developer
   instructions and the user's current prompt.
3. Load the target project's `.promptsConfig/agentconfig.json` when present.
4. For specialized work, consult
   `{{CONFIG_REPO}}/.promptsLibrary/role-index.json` and load only the selected
   role from `role-prompts-ti-senior.md`.

Do not synchronize automatically. The synchronization command is read-only
without an action flag. Fetch, pull, commit and push require the separate
explicit flags `--fetch`, `--pull`, `--commit` and `--push` after user
authorization.
This configuration repository targets the `beta` integration branch; use
`--branch beta` explicitly with an authorized mutation.

If remote access is unavailable, report it and use only the last locally
validated context. Never expose credentials or treat connectivity,
configuration presence or one authorized action as permission for another.
