# ADR-006 — Use object storage for large payloads

Status: Proposed  
Date: 2026-07-07

---

## Context

Prompts, traces, datasets and artifacts can become too large for the operational database.

---

## Decision

Use S3-compatible object storage, such as MinIO locally, for large sanitized payloads and artifacts.

---

## Consequences

PostgreSQL stores metadata and pointers. Object storage holds large payloads with checksums and retention policy.
