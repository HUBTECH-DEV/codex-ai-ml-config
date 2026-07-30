# Provider Adapter Contract

Status: proposal

---

## 1. Purpose

The provider adapter contract prevents model-provider details from leaking into the gateway core.

The core speaks canonical gateway objects. Provider packages map canonical objects to provider-specific API calls.

---

## 2. Required responsibilities

A provider adapter must:

1. expose provider capabilities;
2. estimate or count tokens when possible;
3. map `CanonicalRequest` to provider-specific request;
4. invoke the provider;
5. map provider response to `CanonicalResponse`;
6. normalize error categories;
7. capture token usage, latency and cost metadata;
8. support streaming when the provider supports it;
9. avoid storing secrets in logs or telemetry.

---

## 3. Conceptual interface

```typescript
interface ModelProvider {
  name: string;
  capabilities(): ModelCapabilities;
  countTokens(req: CanonicalRequest): Promise<TokenEstimate>;
  invoke(req: CanonicalRequest): Promise<CanonicalResponse>;
  stream(req: CanonicalRequest): AsyncIterable<ModelEvent>;
}
```

---

## 4. Capability metadata

```yaml
model_capabilities:
  provider: openai
  model: string
  supports_streaming: boolean
  supports_tools: boolean
  supports_structured_output: boolean
  supports_prompt_caching: boolean
  supports_file_input: boolean
  max_input_tokens: integer
  max_output_tokens: integer
  tokenizer: string
```

---

## 5. Error normalization

Provider-specific errors should be mapped to gateway categories:

- `authentication_error`
- `authorization_error`
- `rate_limit_error`
- `quota_error`
- `invalid_request`
- `context_length_exceeded`
- `provider_unavailable`
- `safety_blocked`
- `timeout`
- `unknown_provider_error`

---

## 6. OpenAI adapter boundary

The OpenAI adapter may know about OpenAI-specific request fields. The core must not.

Allowed package dependency direction:

```text
providers/openai -> packages/core
packages/core    -> no provider-specific package
```
