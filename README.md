# Codex AI/ML Config

> Status: **beta** — the `beta` branch is the integration baseline.

Framework versionado para extrair a intenção do solicitante, selecionar
configurações de role/persona, gerar prompts auditáveis e aprender com feedback
e resultados do desenvolvimento de software.

O objetivo é aproximar o resultado produzido da necessidade real do
solicitante sem permitir que um modelo altere autonomamente a configuração
ativa. Recomendações aprendidas precisam de avaliação, rastreabilidade,
aprovação humana e rollback.

## Direção atual

- configuração ativa: `.promptsConfig/agentconfig.json` (versão 2);
- role do projeto: AI/ML Engineer;
- branch de integração: `beta`;
- código/configuração canônica: Git;
- documentação técnica e decisão de armazenamento:
  [`docs/ai-ml-project-blueprint.md`](docs/ai-ml-project-blueprint.md);
- release notes da configuração inicial:
  [`docs/releases/beta-v0.2.0.md`](docs/releases/beta-v0.2.0.md).

## Arquitetura recomendada

O MVP usa:

1. Git para configurações aprovadas, schemas e código;
2. PostgreSQL + pgvector para eventos, feedback, avaliações, linhagem e
   embeddings;
3. armazenamento S3 compatível para datasets e artefatos grandes;
4. MLflow quando houver o primeiro experimento treinável.

Qdrant, Feast, Redis e um warehouse analítico somente entram quando métricas de
escala ou latência justificarem a complexidade adicional.

## Instalação

Linux/macOS:

```sh
./installers/install-codex-framework.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installers\install-codex-framework.ps1
```

## Validar e sincronizar

```sh
python scripts/validate_codex_config.py
python scripts/sync_codex_config.py
```

A sincronização faz fetch primeiro, aceita somente fast-forward e nunca usa
force push.

## GitHub

O remoto GitHub canônico é:

```text
git@github.com:HUBTECH-DEV/codex-ai-ml-config.git
```

A branch `beta` deve ser publicada no GitHub canônico acima. Não substitua
remotos existentes sem revisar os históricos e não use force push.

Neste workspace gerenciado, a política de filesystem não permite criar
`.git`. O clone local usa `.gitdata` como diretório Git separado:

```sh
git --git-dir=.gitdata --work-tree=. status
git --git-dir=.gitdata --work-tree=. log --oneline
```

Um clone normal fora dessa restrição continua usando comandos Git usuais.

## Qualidade

```sh
make validate
make index
PYTHONPYCACHEPREFIX="$(mktemp -d)" python3 -m py_compile scripts/*.py
CODEX_HOME="$(mktemp -d)" ./installers/install-codex-framework.sh
```
