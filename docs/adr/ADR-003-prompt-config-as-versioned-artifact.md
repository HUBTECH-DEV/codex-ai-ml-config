# ADR-003 — Treat prompt configuration as a versioned artifact

Status: Proposed  
Date: 2026-07-07

---

## Context

Prompt behavior must be reproducible, auditable and comparable across evaluations.

---

## Decision

Prompt configuration will be represented as a composed artifact with component versions and a hash.

---

## Consequences

Every response can be traced to the exact configuration that produced it. Promotion and rollback become manageable.
