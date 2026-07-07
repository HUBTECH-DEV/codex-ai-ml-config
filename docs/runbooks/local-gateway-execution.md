# Runbook — Local Gateway Execution

Status: proposal  
Target audience: developers and operators

---

## 1. Purpose

This runbook describes the intended local execution model for the Prompt Optimization Gateway.

The gateway should run locally or near the developer environment so it can use local repository context while relying on the developer's own credentials, SSH keys and provider API keys.

---

## 2. Security stance

- Do not commit API keys.
- Do not commit SSH keys.
- Do not persist raw secrets.
- Run sanitization before storage or model invocation.
- Use `.env` locally and commit only `.env.example`.
- Prefer read-only repository inspection unless a task explicitly requires write operations.

---

## 3. Expected local flow

```text
Developer -> IDE/Codex -> local gateway -> provider adapter -> model
```

For the MVP, the developer should be able to run:

```bash
aigw ask --project codex-ai-ml-config --task "Explain and refactor module X"
```

Or call a local daemon:

```bash
curl -X POST http://localhost:8787/v1/ide/request \
  -H 'content-type: application/json' \
  -d @examples/request.json
```

---

## 4. Dry-run mode

Dry-run mode should:

1. sanitize the request;
2. extract intent;
3. select role and context;
4. produce optimized prompt;
5. estimate tokens;
6. skip provider invocation.

Example:

```bash
aigw ask --dry-run --task "Create ADR for provider abstraction"
```

---

## 5. Required local configuration

Example `.env` file:

```bash
OPENAI_API_KEY="replace-locally-only"
AIGW_DB_DSN="postgres://aigw:aigw@localhost:5432/aigw?sslmode=disable"
AIGW_OBJECT_STORE_ENDPOINT="http://localhost:9000"
AIGW_OBJECT_STORE_BUCKET="aigw-artifacts"
AIGW_DEFAULT_PROVIDER="openai"
AIGW_DEFAULT_MODEL="replace-with-approved-model"
```

The real `.env` file must not be committed.

---

## 6. Minimum validation before provider invocation

The gateway should block provider invocation when:

- sanitization fails;
- required policy is missing;
- selected provider is not approved;
- token estimate exceeds budget;
- mandatory human approval is required but absent;
- repository context contains unredacted secrets.

---

## 7. Minimum telemetry

Every invocation should record:

- request ID;
- project ID;
- provider;
- model;
- prompt config hash;
- compression profile;
- input token estimate;
- actual input tokens when available;
- output tokens;
- cached tokens when available;
- latency;
- cost estimate;
- safety/policy decision;
- evaluation status.
