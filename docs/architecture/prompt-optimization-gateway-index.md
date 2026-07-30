# HubICG Prompt Optimization Gateway — Documentation Index

Status: proposal incubated on `beta`

This folder catalogs the proposed model-agnostic HubICG gateway. OpenAI and
Codex are candidate first adapters, not requirements of the core or the
project identity. The repository currently supplies configuration governance,
schemas, roles and validation; it does not yet supply an executable gateway.

## Primary documents

| Document | Audience | Purpose |
|---|---|---|
| `model-agnostic-prompt-optimization-gateway.md` | Developers, maintainers, sponsors | Main architecture proposal |
| `../backlog/model-agnostic-prompt-gateway-backlog.md` | Developers, project owners | Implementation backlog and epics |
| `../runbooks/local-gateway-execution.md` | Developers/operators | Local execution flow |
| `../schemas/canonical-request.schema.json` | Developers | Canonical request schema |
| `../schemas/prompt-config.schema.json` | Developers | Prompt configuration schema |
| `../schemas/intent-extraction.schema.json` | Developers | Intent extraction schema |
| `../schemas/provider-adapter.contract.md` | Developers | Provider adapter contract |

## ADRs

| ADR | Decision |
|---|---|
| `../adr/ADR-001-model-agnostic-framework.md` | Keep the core model-agnostic |
| `../adr/ADR-002-openai-first-provider.md` | Use OpenAI as the first provider adapter |
| `../adr/ADR-003-prompt-config-as-versioned-artifact.md` | Treat prompt configuration as a versioned artifact |
| `../adr/ADR-004-gateway-parallel-to-ide.md` | Run the gateway in parallel to the IDE |
| `../adr/ADR-005-postgresql-pgvector-mvp.md` | Use PostgreSQL + pgvector in the MVP |
| `../adr/ADR-006-object-storage-for-large-payloads.md` | Use S3-compatible object storage for large artifacts |
| `../adr/ADR-007-human-approval-for-promotion.md` | Require human approval for promotion |
| `../adr/ADR-008-evaluated-aggressive-compression.md` | Require evaluation before aggressive compression becomes default |
| `../adr/ADR-009-cache-aware-prompt-layout.md` | Use cache-aware prompt layout |
| `../adr/ADR-010-git-as-config-registry.md` | Use Git as the canonical configuration registry |

## Communication framing

For developers, this project is a gateway, router and evaluation layer for AI-assisted software development.

For sponsors and incentivizers, this project reduces waste, improves traceability, lowers AI usage cost and creates governance around AI-generated development work.
