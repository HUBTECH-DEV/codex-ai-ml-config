# Changelog

Todas as alterações relevantes deste projeto são registradas aqui e nas
release notes versionadas.

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
