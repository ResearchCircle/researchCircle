# A-P1–A-P4 implementation handoff

Historical provider/drafting record. The user subsequently authorized the crucial
backend/frontend/discovery work here; those implementations now exist. Current
status and assignments are in [CORE-HANDOFF.md](../../docs/onboarding/CORE-HANDOFF.md).
Statements below about missing teammate modules describe the earlier baseline.

## Current status

| Ticket | Implemented evidence | Remaining acceptance |
|---|---|---|
| A-P1 | Shared call shape, deterministic fixture, local completion and focused tests | T2 consumer review of proposed result/job examples |
| A-P2 | Selected-source drafting, exact-version/hash/scope checks, server chat-token counting, source IDs and verbatim support; real synthetic-source Orin draft | T1 source-linked public sample and evidence review |
| A-P3 | Generation controller, exclusive lease, deadlines/cancellation without slot release, late-result suppression, restart interruption; fixture queue and real Orin run | T2 durable transactional job store, route/process wiring and persisted restart validation |
| A-P4 | Same-origin Compose/proxy template, runtime settings, fail-closed startup checks and measured drafting evidence | T1/T2/T3 integration, running Docker, real browser flow, durable restart/backup restore and staged deployment |

The complete assigned workstream is **not yet accepted**. Missing teammate-owned
implementations are explicit dependencies; the fixture store is not a substitute
for real job persistence. No source snapshot, shared DTO, migration, app route,
dependency lock or frontend feature has been modified.
One frontend compatibility line was changed for the A-P4 production build:
`GraphViewer.tsx` now initializes its ref with `null`; no frontend feature was
rewritten. The existing checked-in npm lock is unchanged.

## Files and local commands

- `src/platform/models/provider.py`: local completion, `/tokenize` chat count and
  `/metrics` idle probe. HTTP transport has one bounded request, no proxies,
  redirects, automatic retry, model substitution or cloud fallback.
- `src/platform/drafting/types.py`, `service.py`, `citations.py`: immutable input and
  suggestion values, selected-source assembly and citation validation.
- `src/platform/drafting/jobs.py`, `worker.py`: proposed `JobStore` seam, explicitly
  in-memory fixture and owned generation controller.
- `src/platform/drafting/fixtures.py`, `scripts/orin/draft.py`, `worker_demo.py`:
  synthetic evidence and runnable demos without ML packages or hardware.
- `deployment/`: staged environment, Compose/reverse proxy, configuration checks,
  guarded local startup and disposable HTTP proxy smoke. See its README for
  pending integration and commands.
- `tests/platform/`: provider, drafting, controller, CLI and runtime behavior checks.
- `deployment/api.Dockerfile`, `web.Dockerfile`, scoped context exclusions and
  `build.py`/`image_smoke.py`: owned local image packaging and HTTP startup checks.

```sh
python3.12 -m venv .venv
.venv/bin/python -m scripts.orin.smoke
.venv/bin/python -m scripts.orin.draft
.venv/bin/python -m scripts.orin.worker_demo
.venv/bin/python -m unittest discover -s tests/platform -v
.venv/bin/python -m deployment.preflight --integration
```

Only the final preflight currently exits 1 as expected, reporting missing
integration. Provider/drafting fixtures need no third-party dependencies; the API
image additionally installs its FastAPI/uvicorn bootstrap. All source data
remains under the original immutable snapshot; demos write only temporary lease
files outside it. No model was swapped/restarted by this work.

## T1 and T2 contract request

T1: provide one reviewed, source-linked public example with stable source UUID,
version, usable text, title, origin URL and expected supported claim. The proposed
`SourceSnapshot.content_hash` is SHA-256 of the exact UTF-8 text supplied to the
model; if existing provenance hashes a PDF instead, preserve that hash separately
and agree this normalized-text hash mapping before integration. Snapshots are
already attached to the proposal by T2. Public status never implies attachment.

T2: review internal `DraftRequest`, `SourceRef`, `SourceSnapshot`, `DraftResult`
and `GenerationJob` before mapping them to shared DTOs. `DraftingService.generate`
takes a captured proposal revision, selected refs and attached snapshots. It
returns a suggestion and never saves proposal content or indexes any source.
Acceptance stays a normal revision-checked save under current membership checks.

Implement this proposed durable seam transactionally:

```python
interrupt_running() -> int
claim_next() -> GenerationJob | None
finish(job_id, *, output=None, error=None) -> bool
```

`claim_next` must atomically claim one queued job; `finish` must update **only a
running** job and return false for a terminal/cancelled job. Enqueue must enforce
four queued jobs and one queued/running job per user in a transaction; the fixture
lock proves only local fixture behavior. Persist request revision and exact source
versions/text snapshots at creation. Resolve access through T2's membership service;
this internal controller is not a public authorization boundary.

Compose T2's worker loop with one `GenerationWorker(store, service, lease_path,
idle_check)`. Poll `tick()` outside web requests. All worker processes for the same
model must use the same lease path on the shared local work volume. Acquire the
lease before marking old running jobs interrupted. Do not use the fixture store
for a deployed job service. Before every new admission, the model idle check must
confirm both running and waiting request counts are zero; unavailable/malformed
metrics leave the worker blocked rather than permitting another call.

A failed/cancelled UI job can retain active inference. The controller keeps its
future/lease until completion; `close(wait=False)` returns false while a call
continues. `close(wait=True)` waits for the actual call. A transport timeout is not
proof of remote cancellation; the next admission still requires observed idleness.
`blocked_reason` exposes `model_not_confirmed_idle` for truthful operational status.
No automatic retries or interrupted-job redelivery occur.

T3: consume suggestions with citations containing `source_id`, version, text hash,
title, origin and exact quote. The fixture's origin explicitly says synthetic and
has no public URL. Do not turn it into a fabricated source link. Surface model,
missing usage, insufficient evidence and failure states. Reconcile a changed
proposal revision before acceptance.

## Hardware evidence and limits

The existing service continued to report `homelab-llm` rooted at
`/models/qwen3-coder-30b-a3b-awq`. Its observed `/tokenize` OpenAPI schema accepts
the same `messages` plus `add_generation_prompt=true`; that chat count includes
the generation prefix. No tokenizer/model installation was necessary.

- `evidence-a-p2.json`: real selected-source completion in **4.732360 s**;
  **458 input / 224 output tokens**. The independent tokenizer count was also 458.
- `evidence-a-p3.json`: the first real controller run failed `invalid_citations`
  after **5.737418 s**. The job failed without a fake draft or automatic retry.
- A bounded diagnostic completion then passed the same validator with 458 input /
  224 output tokens. The earlier invalid raw output was intentionally not retained;
  the precise citation failure subtype is unknown, so no parser weakening was made.
- `evidence-a-p3-shared-lease.json`: the corrected shared-lease entrypoint reached
  queued → running → succeeded in **4.745558 s**, with **458 / 224 tokens**.

These are tiny synthetic-source trials, not an accuracy/throughput benchmark or
proof that every future draft will pass. Retain the failed run when evaluating
model reliability. Validation proves selected IDs, exact versions/hash, matching
inline markers and verbatim support quotes. It does **not** establish semantic
entailment of every sentence or guarantee source-prompt injection resistance.
The user must inspect the cited quote; unsupported identities/quotes are rejected.

The service enforces 8192 input tokens using the actual server count and passes
512 output tokens. Fixture counting is explicitly UTF-8 bytes and is not reported
as measured model usage. Sources are JSON-encoded as data, unselected sources are
excluded, truncated/non-JSON/invalid citations fail, and missing evidence returns
an explicit insufficiency result. Provider/worker errors use safe fixed messages.

## Verification and next action

Focused tests were run before implementation and after fixes. Review found and
regression tests fixed an initially per-invocation local demo lease and a tokenizer
deadline that excluded preparation time. The two-controller test verifies shared
lease exclusion before any restart interruption. Runtime tests verify that missing
integration prevents Docker invocation even when `--start` is supplied.

Final focused run: `.venv/bin/python -m unittest discover -s tests/platform -q`
completed with **52 tests passed**. Both fixture draft/controller commands also
completed successfully. Compose parsing passed with
synthetic validation-only image/module/password values; no such images or worker
entrypoint were claimed to exist. Docker Desktop was initially stopped and was
started for a disposable proxy validation. `evidence-proxy.json` records passing
real HTTP fixture checks for routing and origin-preserving redirects through
nginx:1.27-alpine. Review found and fixed external-port loss in upstream Host;
the regression check failed before the fix, then the live proxy test passed.
The separate test network/containers were removed. The external homelab project
browser suite is absent. No app deployment, real persisted restart, database
backup/restore or full browser journey is claimed. Remote branch inspection found
only `main`, `dev` and the unchanged `v2`; no integration branch was available.

Additional independent A-P4 evidence: both local API/frontend images built, and
`evidence-images.json` records passing disposable HTTP startup as UID 10001. The
API remains health-only and the frontend remains the legacy page. The initial
frontend production build exposed the missing React ref initializer described
above; the one-line fix made the real build pass. API image inspection verified
that the source snapshot, `.git` and runtime `.env` were excluded. Anurag owns
these image builds; T2 still supplies the reviewed full application dependencies.

Next owned action: integrate T1's approved source mapping and T2's actual store/worker,
then validate T3's browser flow through the staged proxy and record A-P4 acceptance.
Do not mark the full workstream complete until those real integration gates pass.
