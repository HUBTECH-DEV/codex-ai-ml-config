# ADR-001 — Keep the gateway core model-agnostic

Status: Proposed  
Date: 2026-07-07

---

## Context

The project starts with OpenAI and Codex-oriented workflows, but provider dependency in the core would make future routing, cost optimization and portability difficult.

---

## Decision

The gateway core will use canonical request and response contracts. Provider-specific behavior will be implemented behind adapters.

---

## Consequences

The MVP requires slightly more abstraction work, but avoids hard coupling to OpenAI and supports future providers without redesigning the core domain.
