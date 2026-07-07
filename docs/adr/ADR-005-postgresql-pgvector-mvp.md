# ADR-005 — Use PostgreSQL + pgvector in the MVP

Status: Proposed  
Date: 2026-07-07

---

## Context

The system needs relational lineage, event storage and semantic retrieval, but a dedicated vector database may be premature.

---

## Decision

Use PostgreSQL as the operational store and pgvector for initial vector search.

---

## Consequences

The MVP remains operationally simple while preserving a migration path to a dedicated vector database if SLOs require it.
