# Anurag delivery plan: A-P2 through A-P4

Authority: `docs/design/17-v2-corrected-specification.md` and
`docs/design/18-four-person-delivery-plan.md`. Preserve source data and unrelated
work. No commits, pushes, model changes, production deployment or teammate-owned
feature rewrites. Shared DTOs stay proposed until reviewed by their consumers.

## A-P2 — selected-source drafting

- [x] Write focused failing tests for exact selected/attached source versions,
  proposal isolation, insufficient evidence, citation identity/support snippets,
  provider failure and the 8192-input/512-output limits.
- [x] Implement immutable drafting inputs/results under `src/platform/drafting/`.
  Use the existing provider; serialize source text as data. Validate source hashes,
  citations and quoted support. Never write proposal content or index sources.
- [x] Extend the local provider with the observed server tokenizer API. Fixture
  counting is explicitly synthetic; real limits use the served chat template.
- [x] Add a fixture-default draft demo and run selected-source inference on the
  existing idle Orin service. Record measured usage/latency and limitations.
  T1's source sample is missing; use labeled synthetic evidence, not invented data.

## A-P3 — generation worker behavior

- [x] Test one generation at a time, bounded queue, per-user admission, deadlines,
  cancellation while inference continues, restart interruption and safe failures.
- [x] Implement owned generation behavior against a narrow job-store interface,
  with an explicitly labeled in-memory integration fixture. T2 owns real job
  persistence, atomic claim/admission, routes and worker process composition.
- [x] Keep the slot until the call ends; after an ambiguous transport failure,
  require confirmed model idleness before admitting another generation. Do not
  automatically retry or redeliver interrupted work.
- [x] Publish exact T2 integration calls and runnable lifecycle examples. Real
  persisted-job acceptance remains pending until T2's implementation is available.

## A-P4 — staged runtime and integration

- [x] Build owned API/frontend images with scoped contexts and check disposable
  HTTP startup. Keep health-only/legacy packaging separate from v2 acceptance;
  use T2's full dependency file when it becomes available.
- [x] Supply same-origin reverse proxy/runtime configuration, explicit fixture
  versus local model settings, startup/preflight commands and local validation.
- [x] Test runtime configuration and fail clearly when required app/job services
  are absent. Do not make a health-only app look like the complete product.
- [x] Review measured drafting output, failure cases and all owned changes.
- [ ] Integrate real T1/T2/T3 work when available, validate restart persistence,
  real browser flow and shared demo. These acceptance checks cannot be claimed from
  standalone fixtures. The external homelab project suite is currently absent.

Current dependency evidence: API exposes only `/healthz`; no v2 workflow/database
or worker modules exist. Frontend remains the legacy chat/hub/graph app. No public
source sample or external project browser suite is available. Continue all
independent owned work and retain these as explicit integration gates.
