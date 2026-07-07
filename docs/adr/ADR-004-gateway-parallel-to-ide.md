# ADR-004 — Run the gateway in parallel to the IDE

Status: Proposed  
Date: 2026-07-07

---

## Context

Direct IDE integration may be expensive and brittle during early design.

---

## Decision

The MVP will run as a local CLI and/or daemon parallel to the IDE, with future IDE extension support.

---

## Consequences

The first version can be tested locally with the developer's SSH keys and API keys, without committing secrets or requiring IDE internals.
