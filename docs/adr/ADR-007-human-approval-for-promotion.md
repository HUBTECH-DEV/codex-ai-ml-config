# ADR-007 — Require human approval for prompt and model promotion

Status: Proposed  
Date: 2026-07-07

---

## Context

Automatic promotion can introduce silent regressions, privacy issues or higher cost.

---

## Decision

Prompt configurations, routing policies and aggressive compression profiles require human approval before promotion during beta.

---

## Consequences

The system may recommend changes, but production behavior remains governed and reversible.
