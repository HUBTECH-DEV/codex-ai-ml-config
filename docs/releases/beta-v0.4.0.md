# HubICG beta v0.4.0

Date: 2026-07-30  
Status: release candidate prepared locally; commit and publication pending  
Target branch: `beta`

## Purpose

This candidate integrates the approved P0 foundation from main commit
`28aed817b38687e643359369fe759f41dd129cee` with the existing beta lineage at
`1ede7efdc2134022bb64274c5f90a9a1da0ec7e9`.

The project now uses the technology-agnostic identity **HubICG — Hubtech
Intent & Context Governance Framework** and the canonical repository name
`HUBTECH-DEV/hubtech-intent-context-governance-framework`. The prior
`codex-ai-ml-config` name is retained only as a migration alias and in
immutable history.

## Delivered foundation

- audited agent configuration v4 and primary context v3;
- append-only configuration lineage with immutable snapshot `v0004`;
- 60 indexed roles, including multiformat publishing and Git engineering;
- JSON Schemas and validators for active configuration, context and chat
  history;
- deterministic role-index generation and historical-integrity tests;
- static secret scanning;
- opt-in Git synchronization with separate authorization for `fetch`, `pull`,
  `commit` and `push`;
- validation workflow for both `main` and `beta`;
- branch-aware beta defaults in the Makefile, configuration guide and sync
  helper.

## Beta specifications retained

The architecture proposal, AI/ML blueprint, backlog, runbook, provider
contract, three incubated schemas and ten ADRs remain available on `beta`.
Their status is intentionally truthful:

- ADRs remain `Proposed`;
- the gateway CLI/daemon, provider calls, storage, telemetry and learning
  pipelines are not implemented;
- OpenAI and Codex are candidate first adapters, not dependencies of the
  framework identity or model-agnostic core.

## Immutable lineage verification

The integration preserves these pre-existing beta artifacts byte-for-byte:

| Artifact | SHA-256 |
|---|---|
| `.promptsConfig/history/v0001.json` | `c1f3c714be6ff5f1cd65ce63935799445a4ea69da68647a34bc2623be88f0b4d` |
| `.promptsConfig/history/v0002.json` | `817e0280c3f6169dfe1b88ac62dcec5c9c0c62be58ad276bab60f05176591d79` |
| `.promptsConfig/history/v0003.json` | `db9e7df57e9eb769324bf8c49abd3dcbfc1cc3acfb8f5b171da8c64e43f2cd92` |
| `.promptsHistory/framework-bootstrap.json` | `f42fa61363a33b92b5b6d464be98ad05ec02fe5f0b1d860eb93016cd54c8cb2c` |
| `.promptsHistory/ai-ml-beta-project-setup.json` | `695889f46d2297e90807baf80a4f5d670ed87ffb1a2c95284f86967c77bd12ae` |
| `.promptsHistory/github-migration-audit.json` | `7b9d20ced46e9e97993b2fc9d8515b2b974b4748d018ad468b9d51ec20660938` |
| `docs/releases/beta-v0.2.0.md` | `d4150680ae93d61772c556d9eb73069863cd9d0972f62b57b6e3d8ba852c4183` |

## Validation

Before promotion, run:

```bash
make ci
git diff --check
```

This preparation performs no commit, push, remote rename or remote staging.
