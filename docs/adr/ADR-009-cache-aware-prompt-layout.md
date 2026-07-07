# ADR-009 — Use cache-aware prompt layout

Status: Proposed  
Date: 2026-07-07

---

## Context

Model providers may reward stable prompt prefixes through caching and lower effective latency/cost.

---

## Decision

The gateway will place stable prompt components before dynamic task context when this does not degrade instruction quality.

---

## Consequences

Static core rules, role deltas and output contracts become easier to cache. Dynamic context remains isolated at the suffix.
