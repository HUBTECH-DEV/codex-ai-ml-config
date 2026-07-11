#!/bin/sh
set -eu

repo_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
codex_home="${CODEX_HOME:-${HOME}/.codex}"
template="${repo_dir}/config/codex-global-AGENTS.template.md"
target="${codex_home}/AGENTS.md"
timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 is required." >&2
  exit 1
}

python3 "${repo_dir}/scripts/validate_codex_config.py" \
  --root "${repo_dir}" \
  --quiet

mkdir -p "${codex_home}"
if [ -f "${target}" ]; then
  backup="${target}.backup-${timestamp}"
  cp -p "${target}" "${backup}"
  echo "Backup: ${backup}"
fi

temporary="${target}.tmp.$$"
trap 'rm -f "${temporary}"' EXIT HUP INT TERM

python3 - "${template}" "${temporary}" "${repo_dir}" <<'PY'
from pathlib import Path
import sys

template = Path(sys.argv[1]).read_text(encoding="utf-8")
destination = Path(sys.argv[2])
repository = Path(sys.argv[3]).resolve().as_posix()
destination.write_text(
    template.replace("{{CONFIG_REPO}}", repository),
    encoding="utf-8",
)
PY

chmod 0644 "${temporary}"
mv -f "${temporary}" "${target}"
trap - EXIT HUP INT TERM

echo "Installed: ${target}"
echo "Configuration repository: ${repo_dir}"
echo "Restart Codex or open a new thread."
