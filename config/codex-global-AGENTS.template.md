# Global Codex configuration bootstrap

Use `{{CONFIG_REPO}}` as the central AI/ML prompt configuration repository.
When this repository has a historical directory name, treat it as a filesystem
path only; active Codex project publication uses GitHub/HUBTECH-DEV.

Before project work:

1. Validate the repository:

   ```text
   python "{{CONFIG_REPO}}/scripts/validate_codex_config.py" --quiet
   ```

2. If `origin` is configured and reachable, synchronize:

   ```text
   python "{{CONFIG_REPO}}/scripts/sync_codex_config.py"
   ```

3. Read `{{CONFIG_REPO}}/.promptsConfig/codex-primary-context.md` completely
   and apply it as the primary project context, subject to system/developer
   instructions and the user's current prompt.
4. Load the target project's `.promptsConfig/agentconfig.json` when present.
5. For specialized work, consult
   `{{CONFIG_REPO}}/.promptsLibrary/role-index.json` and load only the selected
   role from `role-prompts-ti-senior.md`.

If synchronization is unavailable, report it and use only the last locally
validated context. Never expose credentials or treat failed connectivity as
permission to write, replace remotes, merge divergent histories, or force
push.
