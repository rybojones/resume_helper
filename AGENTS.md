# Agent Guidelines

## Security

- Follow secure coding practices by default (validate inputs, avoid hardcoded secrets, use least-privilege principles, and adhere to OWASP top 10 guidelines).
- Never introduce vulnerabilities such as SQL injection, XSS, command injection, or insecure deserialization.
- Do not log, store, or expose sensitive data (credentials, PII, tokens).

## Pair Development Workflow

Work as a pair developer alongside the human dev. This means:

1. **Plan first.** Before writing any code, read and understand the relevant files, then design a step-by-step plan based on the human dev's instructions. Use this plan as a to-do list to stay on track and monitor progress as development takes place.
2. **Share the plan.** Present the plan clearly to the human dev and wait for validation before proceeding. Update the plan if the human dev requests changes.
3. **One step at a time.** Complete only one step per turn, then pause and confirm with the human dev before moving to the next step. Do not run ahead or batch multiple steps together.
4. **Surface blockers early.** If a step surfaces unexpected complexity or a decision point, stop and discuss with the human dev before continuing.
5. **Keep changes minimal and focused.** Only make changes directly required by the current step. Avoid refactoring, cleanup, or "improvements" outside the scope of what was agreed upon.
