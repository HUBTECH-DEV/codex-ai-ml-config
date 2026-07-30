# Configuração e operação do HubICG

Este documento descreve o núcleo operacional do **HubICG — Hubtech Intent &
Context Governance Framework**. O nome deste arquivo é mantido como alias
legado para não quebrar links existentes.

## Componentes

| Componente | Finalidade |
|---|---|
| `.promptsConfig/codex-primary-context.md` | Contexto primário; filename legado |
| `.promptsConfig/agentconfig.json` | Configuração ativa |
| `.promptsConfig/agentconfig-history.json` | Cadeia append-only de versões |
| `.promptsConfig/history/` | Snapshots imutáveis |
| `.promptsHistory/` | Evidências de chat e mudanças |
| `.promptsLibrary/role-prompts-ti-senior.md` | Biblioteca de 60 roles |
| `.promptsLibrary/role-index.json` | Índice determinístico |
| `schemas/` | Contratos JSON |
| `scripts/validate_codex_config.py` | Validação consolidada |
| `scripts/sync_codex_config.py` | Status e sincronização explicitamente autorizada |
| `config/codex-global-AGENTS.template.md` | Template do bootstrap global |
| `installers/` | Instaladores Linux/macOS e Windows |

## Quality gates locais

Execute toda a suíte:

```sh
make ci
```

Targets disponíveis:

```sh
make validate
make schemas
make index
make test
make compile
make secrets
make install
```

`make sync` é um alias compatível e somente leitura para `make sync-status`.
As mutações têm targets separados: `sync-fetch`, `sync-pull`, `sync-commit` e
`sync-push`.

## Instalação do bootstrap

Linux/macOS:

```sh
./installers/install-codex-framework.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installers\install-codex-framework.ps1
```

Os instaladores:

1. validam a configuração;
2. criam backup timestampado de um `AGENTS.md` existente;
3. renderizam o caminho absoluto do repositório no
   `config/codex-global-AGENTS.template.md`;
4. instalam o bootstrap por substituição atômica.

Os nomes dos instaladores, do template e do contexto são mantidos por
compatibilidade com o alias `codex-ai-ml-config`.

## Configuração do remoto

Destino canônico planejado:

```text
HUBTECH-DEV/hubtech-intent-context-governance-framework
```

Antes de alterar um remoto existente, compare e obtenha autorização:

```sh
git remote -v
git remote get-url origin
git ls-remote origin
```

Exemplo para um repositório ainda sem `origin`:

```sh
git remote add origin \
  git@github.com:HUBTECH-DEV/hubtech-intent-context-governance-framework.git
```

Não coloque tokens na URL. Uma renomeação no GitHub e a mudança do remoto local
são operações distintas e precisam ser verificadas separadamente.

## Modelo de autorização do sincronizador

O comando sem flags é local/read-only: valida a árvore, lê estado do worktree e
compara `HEAD` somente com a remote-tracking ref já existente.

```sh
python3 scripts/sync_codex_config.py
```

As quatro autorizações são independentes:

| Flag | Mutação autorizada | Proteções |
|---|---|---|
| `--fetch` | Atualizar apenas `refs/remotes/<remote>/<branch>` | Sem prune, merge, commit ou push |
| `--pull` | Fetch e merge fast-forward | Branch esperada, worktree totalmente limpo, ref remota validada |
| `--commit` | Commit local do contexto primário | Stage inicialmente vazio, bump de metadados, validação e escopo de um arquivo |
| `--push` | Publicar commits de contexto | Fetch prévio, sem behind/divergência, nenhum arquivo externo no intervalo ahead |

Exemplos:

```sh
python3 scripts/sync_codex_config.py --fetch
python3 scripts/sync_codex_config.py --pull
python3 scripts/sync_codex_config.py --commit
python3 scripts/sync_codex_config.py --push
```

Mesmo quando executadas em sequência, as flags registram autorizações
separadas. O fluxo recomendado é revisar o estado entre `--commit` e `--push`.

O script:

- funciona em repositórios normais e Git worktrees;
- não altera `pull.ff` ou outra configuração Git;
- não faz force push;
- não resolve divergência;
- rejeita HEAD destacado e branch inesperada para mutações;
- valida antes de qualquer ação;
- recusa archives remotos com symlinks/hardlinks antes do fast-forward;
- não publica commits que toquem arquivos fora do contexto autorizado.

## Opções e variáveis

As opções de CLI têm precedência operacional:

```text
--root
--config-file
--remote
--branch
--commit-message
```

Variáveis atuais:

```sh
HUBICG_REPO="/path/to/repository"
HUBICG_CONFIG_FILE=".promptsConfig/codex-primary-context.md"
HUBICG_REMOTE="origin"
HUBICG_BRANCH="main"
```

Por compatibilidade, `CODEX_CONFIG_REPO`, `CODEX_CONFIG_FILE`,
`CODEX_CONFIG_REMOTE` e `CODEX_CONFIG_BRANCH` ainda são aceitas quando a
variável HubICG correspondente não estiver definida.

## Versionamento

Há dois fluxos:

- a configuração ativa usa `currentVersion` e snapshots completos
  `.promptsConfig/history/vNNNN.json`;
- o contexto primário usa `configVersion` no frontmatter e histórico Git.

Uma mudança de configuração deve:

1. incrementar `currentVersion`;
2. criar novo snapshot completo;
3. acrescentar uma entrada em `agentconfig-history.json`;
4. manter snapshots e entradas anteriores byte a byte;
5. registrar a mudança em novo arquivo ou nova mensagem de
   `.promptsHistory/`.

Renomeações atualizam a identidade ativa em nova versão. Referências em
snapshots históricos permanecem como evidência do estado daquela versão.

## Falhas e recuperação

- Validação local falhou: não sincronize; corrija a inconsistência.
- Worktree sujo no pull: revise, commit ou mova alterações conscientemente.
- Branch incorreta/HEAD destacado: selecione a branch esperada fora do script.
- Históricos divergiram: faça análise manual do DAG; não use força.
- Push bloqueado por escopo: publique manualmente somente após nova autorização
  que cubra os arquivos adicionais.
- Remoto indisponível: continue com a última configuração local validada.
