# ADR-002 — Use OpenAI as the first provider adapter

Status: Proposed  
Date: 2026-07-07

---

## Context

The initial use case targets Codex-oriented workflows and OpenAI models.

---

## Decision

OpenAI will be implemented as the first ProviderAdapter, with all OpenAI-specific mapping isolated under the provider package.

---

## Consequences

The project gets a useful first integration while preserving the provider abstraction.
