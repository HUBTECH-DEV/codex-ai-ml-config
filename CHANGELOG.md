# Changelog

Todas as alterações relevantes deste projeto são registradas aqui e nas
release notes versionadas.

## [0.4.0-beta] - 2026-07-30

### Adicionado

- identidade tecnológica agnóstica **HubICG — Hubtech Intent & Context
  Governance Framework**;
- configuração auditada v4, snapshot imutável `v0004` e registro de chat da
  integração P0;
- 60 roles indexadas, incluindo editoração multiformato e engenharia Git;
- schemas executáveis, validação de segredos, testes automatizados e workflow
  de CI para `main` e `beta`;
- sincronização Git opt-in com autorizações independentes para `fetch`,
  `pull`, `commit` e `push`;
- release notes em `docs/releases/beta-v0.4.0.md`.

### Alterado

- branch padrão da integração beta definida como `beta`;
- documentação ativa e metadados migrados para o repositório canônico
  `HUBTECH-DEV/hubtech-intent-context-governance-framework`;
- Codex e OpenAI tratados como superfícies/adaptadores iniciais, sem acoplar a
  identidade ou o núcleo do framework;
- especificações incubadas na beta catalogadas como propostas, sem indicar
  implementação inexistente.

### Preservado

- snapshots `v0001`, `v0002` e `v0003`, três históricos de chat anteriores e
  as release notes `beta-v0.2.0.md` sem alteração de bytes;
- dez ADRs da incubação com status `Proposed`.

## [0.3.0-beta] - 2026-07-11

### Adicionado

- configuração auditada v3 e snapshot imutável `v0003`;
- auditoria da migração e governança GitHub-first na organização
  `HUBTECH-DEV`.

### Alterado

- roteamento do repositório e política de publicação registrados na
  configuração histórica v3.

## [0.2.0-beta] - 2026-07-06

### Adicionado

- objetivo AI/ML orientado à extração de intenção e otimização de prompts;
- configuração auditada v2 e snapshot imutável `v0002`;
- branch de integração `beta`;
- casos de uso e arquitetura de dados/ML;
- avaliação de PostgreSQL/pgvector, object storage, MLflow, Qdrant e Feast;
- roadmap com critérios mensuráveis de promoção;
- templates equivalentes para Pull Request e Merge Request.
- execução do workflow de validação em pushes para `beta`.

### Alterado

- role ativa para AI/ML Engineer;
- governança para rastrear datasets, features, experimentos, modelos e
  recomendações;
- política de promoção para exigir avaliação offline, regressão e aprovação
  humana.

### Segurança

- persistência condicionada a sanitização de segredos e dados sensíveis;
- proibição de aprendizagem online autônoma na fase beta;
- vínculo obrigatório entre resultado, configuração, modelo e revisão do
  repositório.
