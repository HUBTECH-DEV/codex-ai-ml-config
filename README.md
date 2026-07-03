# Codex AI/ML Config

Versioned framework for controlling Codex roles, structuring AI requests and
dynamically loading audited pre-prompt configuration.

## Install

Linux/macOS:

```sh
./installers/install-codex-framework.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installers\install-codex-framework.ps1
```

## Validate and synchronize

```sh
python scripts/validate_codex_config.py
python scripts/sync_codex_config.py
```

Synchronization uses fetch-first, fast-forward-only pulls, semantic versioned
commits and no force push.
