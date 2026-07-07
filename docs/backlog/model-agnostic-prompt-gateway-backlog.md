# Backlog — Model-Agnostic Prompt Optimization Gateway

Status: initial proposal  
Target branch: `beta`

---

## Epic 1 — Architecture foundation

### Goal

Create the basic contracts and repository structure for the gateway.

### Issues

1. Define `CanonicalRequest` schema.
2. Define `CanonicalResponse` schema.
3. Define `PromptConfig` schema.
4. Define `IntentExtraction` schema.
5. Define `ProviderAdapter` contract.
6. Define compression profile contract.
7. Define policy decision contract.
8. Define telemetry event contract.
9. Create architecture documentation index.
10. Create initial ADRs.

### Acceptance criteria

- Schemas are versioned.
- Contracts do not reference OpenAI-specific fields except in adapters.
- Documentation explains the domain to developers and sponsors.

---

## Epic 2 — Local gateway MVP

### Goal

Create a local execution path for receiving a prompt, optimizing it and calling a provider.

### Issues

1. Create `aigw` CLI skeleton.
2. Create local daemon skeleton.
3. Implement request ingestion endpoint.
4. Implement dry-run mode.
5. Implement request correlation ID.
6. Implement structured logs.
7. Implement config loading from local files.
8. Implement failure handling and error categories.

### Acceptance criteria

- A local request can be submitted to the gateway.
- The gateway can run without provider invocation in dry-run mode.
- Every request receives a stable request ID.

---

## Epic 3 — Sanitization and policy

### Goal

Guarantee that secrets and sensitive data are handled before persistence or model calls.

### Issues

1. Create secret detection rules.
2. Create allowlist mechanism.
3. Create policy tags for payloads.
4. Block unsafe persistence by default.
5. Record policy decisions in telemetry.
6. Create tests for secret redaction.
7. Create runbook for retention and deletion.

### Acceptance criteria

- Sanitizer runs before storage.
- Sanitizer runs before provider invocation.
- Known secret patterns are redacted in tests.
- Policy decisions are auditable.

---

## Epic 4 — Intent extraction and role routing

### Goal

Transform raw prompts into structured task intent and route to appropriate role and prompt contract.

### Issues

1. Implement deterministic baseline extractor.
2. Implement model-assisted extractor behind adapter.
3. Validate extraction against schema.
4. Implement role router using role index.
5. Load only selected role definitions.
6. Add confidence threshold and abstention.
7. Add tests for ambiguous role selection.

### Acceptance criteria

- Intent extraction includes task type, deliverable, constraints and acceptance criteria.
- Role routing can abstain when confidence is low.
- Full role library is never loaded by default.

---

## Epic 5 — Prompt optimization and compression

### Goal

Reduce input tokens while preserving semantic requirements.

### Issues

1. Implement token budget allocation.
2. Implement duplicate rule removal.
3. Implement role delta loading.
4. Implement context slicing.
5. Implement semantic compression to YAML/JSON.
6. Implement compression profiles: conservative, balanced and aggressive.
7. Implement prompt linting.
8. Implement before/after token report.
9. Implement compression safety checks.

### Acceptance criteria

- Compression report includes original tokens, optimized tokens and reduction ratio.
- Constraints and acceptance criteria are preserved.
- Aggressive compression is not default.

---

## Epic 6 — OpenAI provider adapter

### Goal

Implement OpenAI as the first provider adapter without coupling the core to OpenAI.

### Issues

1. Map `CanonicalRequest` to OpenAI request.
2. Map OpenAI response to `CanonicalResponse`.
3. Capture token usage.
4. Capture cached token usage when available.
5. Capture latency and error categories.
6. Implement streaming support.
7. Implement structured output support.
8. Implement provider capability metadata.

### Acceptance criteria

- Core packages do not depend on OpenAI SDK types.
- Provider mapping is isolated.
- Token/cost metadata is captured.

---

## Epic 7 — Storage and telemetry

### Goal

Persist enough metadata to evaluate prompts, routing and model behavior.

### Issues

1. Create PostgreSQL schema for projects, sessions and events.
2. Create prompt config lineage tables.
3. Create intent extraction table.
4. Create evaluation table.
5. Add pgvector extension support.
6. Add object storage pointer support.
7. Add append-only audit log.
8. Create migration scripts.

### Acceptance criteria

- Every model invocation links to a prompt config hash.
- Raw sensitive payloads are not stored directly by default.
- Audit events are append-only.

---

## Epic 8 — Evaluation and quality gates

### Goal

Determine when prompt optimization improves efficiency without degrading results.

### Issues

1. Create initial gold set format.
2. Define deterministic evaluators.
3. Define human review format.
4. Implement constraint recall evaluation.
5. Implement acceptance criteria coverage evaluation.
6. Implement role adherence evaluation.
7. Implement regression gate.
8. Implement promotion report.

### Acceptance criteria

- No configuration can be promoted without evaluation evidence.
- Evaluation links to prompt config, model and task.
- Critical regressions block promotion.

---

## Epic 9 — Developer experience

### Goal

Make the gateway understandable and useful for developers.

### Issues

1. Create local setup runbook.
2. Create `.env.example` without secrets.
3. Add dry-run examples.
4. Add example request fixtures.
5. Add architecture diagrams.
6. Add troubleshooting guide.
7. Add contribution guidelines for provider adapters.

### Acceptance criteria

- A developer can run the gateway locally using their own API keys and SSH keys.
- The setup path does not require committing secrets.
- Documentation separates developer and sponsor narratives.

---

## Epic 10 — Future provider expansion

### Goal

Prove real model agnosticism.

### Issues

1. Implement a second cloud provider adapter.
2. Implement a local model adapter prototype.
3. Create model capability matrix.
4. Implement provider fallback policy.
5. Implement provider cost policy.
6. Implement provider privacy policy.
7. Add provider compatibility tests.

### Acceptance criteria

- At least two providers can be invoked through the same canonical contract.
- Provider routing does not require changing the core request schema.
