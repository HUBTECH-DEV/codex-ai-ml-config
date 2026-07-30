# Beta v0.2.0 — configuração AI/ML e blueprint

Data: 2026-07-06

Branch: `beta`

## Objetivo

Estabelecer a base de produto e governança para extrair intenção e usar
feedback de desenvolvimento de software na recomendação de role, persona e
padrões de prompt.

## Alterações

- configuração do projeto promovida de v1 para v2;
- role ativa definida como AI/ML Engineer;
- snapshot imutável e histórico de configuração atualizados;
- objetivo, casos de uso, fluxo de dados e modelo lógico documentados;
- PostgreSQL + pgvector e S3 compatível recomendados para o MVP;
- MLflow planejado para o primeiro experimento;
- Qdrant e Feast condicionados a critérios objetivos de escala;
- métricas, riscos, privacy gates e roadmap P0–P3 definidos;
- branch `beta` adotada como linha de integração.
- CI configurada para validar pushes em `main` e `beta`.

## Validação esperada

```sh
python3 scripts/validate_codex_config.py
python3 scripts/build_role_index.py --check
```

## Riscos conhecidos

- política de coleta/retensão ainda precisa de decisão;
- métricas numéricas dependem do baseline;
- destino GitHub canônico confirmado em `HUBTECH-DEV/codex-ai-ml-config`;
- ainda não há implementação do datastore nem dataset treinável.

## Rollback

A configuração anterior permanece em
`.promptsConfig/history/v0001.json`. Um rollback deve criar uma nova versão; o
histórico existente não pode ser reescrito.
