# Central Codex configuration

This repository is the central source for project-aware Codex instructions,
role routing and GitLab CE integration.

## Components

| Component | Purpose |
|---|---|
| `.promptsConfig/codex-primary-context.md` | Consolidated primary context |
| `.promptsConfig/agentconfig.json` | Active project configuration |
| `.promptsConfig/history/` | Immutable configuration snapshots |
| `.promptsHistory/` | Append-only chat histories |
| `.promptsLibrary/role-prompts-ti-senior.md` | Versioned senior role library |
| `.promptsLibrary/role-index.json` | Deterministic role lookup index |
| `scripts/sync_codex_config.py` | Fast-forward pull or versioned commit/push |
| `scripts/validate_codex_config.py` | Schema, audit-chain and checksum checks |
| `config/codex-global-AGENTS.md` | Minimal global Codex bootstrap |

## Local validation

```sh
make codex-config-index
make codex-config-validate
make codex-config-test
```

## Install the global bootstrap

Run from a regular macOS terminal:

```sh
make codex-global-install
```

The installer backs up an existing `~/.codex/AGENTS.md` before atomically
installing the new bootstrap. Restart Codex or open a new thread after
installation.

## Configure the GitLab remote

The synchronization script requires:

- an initialized Git repository;
- a non-detached `main` branch;
- a configured `origin`;
- existing Git credentials for SSH or HTTPS;
- `git user.name` and `git user.email` when a commit is necessary.

Example using local GitLab SSH:

```sh
git remote add origin \
  ssh://git@localhost:2224/<namespace>/<project>.git
git ls-remote origin
```

Do not replace an existing remote without reviewing it. Do not place tokens in
the remote URL or committed files.

## Synchronize

```sh
make codex-config-sync
```

Optional environment variables:

```sh
CODEX_CONFIG_REPO="/path/to/config-repository"
CODEX_CONFIG_FILE=".promptsConfig/codex-primary-context.md"
CODEX_CONFIG_REMOTE="origin"
CODEX_CONFIG_BRANCH="main"
```

The script:

1. acquires a repository lock;
2. validates the remote and authentication;
3. fetches and compares commit ancestry;
4. pulls only when fast-forward is possible;
5. refuses bidirectional divergence;
6. stages only the primary context;
7. increments `configVersion` and `lastUpdated`;
8. creates a semantic timestamped commit;
9. pushes without force.

Remote and local changes at the same time require manual review.

## Dynamic loading

At thread startup, the global bootstrap validates and, when possible,
synchronizes this repository. Codex then reads the consolidated context and
loads only the selected role from the role library.

If GitLab is unreachable, the bootstrap reports the condition and uses only
the last locally validated context. It must not write remotely or infer
permissions from configuration presence.

