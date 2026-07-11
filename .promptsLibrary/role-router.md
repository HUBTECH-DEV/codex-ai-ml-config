# Role Router

Use this router only when the current prompt and active project configuration
do not already define a role.

1. Read `role-index.json`.
2. Identify the task domain, expected deliverable, risks and required
   competencies.
3. Select one primary role and only the auxiliary roles strictly required.
4. If the match is materially ambiguous, present the candidates and request a
   decision.
5. Load only the selected sections from `role-prompts-ti-senior.md`.
6. Preserve the precedence and human-decision rules from
   `.promptsConfig/codex-primary-context.md`.

Fallback for AI platform work:

- Principal AI/ML Engineer;
- Principal Prompt Engineer / AI Application Engineer;
- Principal MLOps Engineer;
- Principal DevOps Engineer.
