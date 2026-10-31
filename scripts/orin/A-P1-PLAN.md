# A-P1 provider implementation plan

Spec: `docs/design/17-v2-corrected-specification.md`, sections 3–5.

Goal: teammates can call the same small synchronous provider interface with a
deterministic fixture or the existing local OpenAI-compatible server.

Scope: `src/platform/models/`, `scripts/orin/`, focused `tests/platform/` checks.
No shared DTO, route, worker, migration, dependency lock or source-data changes.

- [x] Write behavioral tests for a deterministic result, explicit errors, invalid
  arguments, request shape, timeout, malformed responses and unavailable service.
  Run them before implementation and confirm the missing provider causes failure.
- [x] Implement `ModelProvider.generate(prompt, max_output_tokens, timeout_s)`,
  immutable result/usage values, typed provider errors, a deterministic fixture,
  and the local HTTP adapter. Use standard library only. Never retry, redirect,
  substitute models or return failure text as a successful completion.
- [x] Add a fixture-default smoke command and provider/result JSON examples.
  Publish proposed DraftJob states/results without changing T2's shared contracts.
- [x] Run the focused tests and fixture demo. Observe existing Orin configuration
  and idle state, then run one bounded synthetic completion through this adapter.
  Record model ID, usage, latency and transport configuration, or a hardware blocker.
- [x] Review failure cases and changed files; record evidence and precise T1/T2/T3
  handoffs. Leave commits, pushes, deployment and A-P2 onward for separate work.

Review focus: provider failures must not leak response bodies or prompts; fixture
usage must not masquerade as measured tokens; redirect/proxy behavior must not send
source text elsewhere; timeout must not imply inference cancellation; truncated
output and absent usage must remain visible to consumers. Input token counting is
A-P2 work; persisted queue limits and cancellation admission are A-P3 work.
