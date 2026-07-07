# ADR-008 — Require evaluation before aggressive compression becomes default

Status: Proposed  
Date: 2026-07-07

---

## Context

Aggressive prompt compression can remove critical context even when token reduction looks attractive.

---

## Decision

Aggressive compression may be tested, but cannot become default without regression evaluation and human approval.

---

## Consequences

Token savings are measured against quality gates instead of being optimized blindly.
