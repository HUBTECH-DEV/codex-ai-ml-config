[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) {
        $env:CODEX_HOME
    } else {
        Join-Path $HOME ".codex"
    }),
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryPath).Path
$template = Join-Path $repo "config/codex-global-AGENTS.template.md"
$context = Join-Path $repo ".promptsConfig/codex-primary-context.md"
$agentConfig = Join-Path $repo ".promptsConfig/agentconfig.json"
$history = Join-Path $repo ".promptsConfig/agentconfig-history.json"
$roleLibrary = Join-Path $repo ".promptsLibrary/role-prompts-ti-senior.md"
$roleManifest = Join-Path $repo ".promptsLibrary/MANIFEST.sha256"
$roleIndex = Join-Path $repo ".promptsLibrary/role-index.json"

foreach ($required in @(
    $template,
    $context,
    $agentConfig,
    $history,
    $roleLibrary,
    $roleManifest,
    $roleIndex
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file is missing: $required"
    }
}

$active = Get-Content -LiteralPath $agentConfig -Raw | ConvertFrom-Json
$audit = Get-Content -LiteralPath $history -Raw | ConvertFrom-Json
$roles = Get-Content -LiteralPath $roleIndex -Raw | ConvertFrom-Json

if ($active.schemaVersion -ne "1.0") {
    throw "Unsupported agent configuration schema."
}
if ($active.currentVersion -ne $audit.currentVersion) {
    throw "Active configuration and history versions differ."
}
if ($roles.roles.Count -lt 50) {
    throw "Role index is incomplete."
}

$expectedHash = (
    (Get-Content -LiteralPath $roleManifest -Raw).Trim() -split "\s+"
)[0].ToUpperInvariant()
$actualHash = (
    Get-FileHash -LiteralPath $roleLibrary -Algorithm SHA256
).Hash.ToUpperInvariant()
if ($expectedHash -ne $actualHash) {
    throw "Role library checksum mismatch."
}

New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
$target = Join-Path $CodexHome "AGENTS.md"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")

if (Test-Path -LiteralPath $target) {
    $backup = "$target.backup-$timestamp"
    Copy-Item -LiteralPath $target -Destination $backup -Force
    Write-Host "Backup: $backup"
}

$repoForPrompt = $repo.Replace("\", "/")
$rendered = (
    Get-Content -LiteralPath $template -Raw
).Replace("{{CONFIG_REPO}}", $repoForPrompt)
$temporary = "$target.tmp-$PID"

try {
    [System.IO.File]::WriteAllText(
        $temporary,
        $rendered,
        [System.Text.UTF8Encoding]::new($false)
    )
    Move-Item -LiteralPath $temporary -Destination $target -Force
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Force
    }
}

Write-Host "Installed: $target"
Write-Host "Configuration repository: $repo"
Write-Host "Restart Codex or open a new thread."

