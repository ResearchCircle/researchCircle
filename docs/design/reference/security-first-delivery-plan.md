> **Deferred reference, 2026-10-30.** This is the earlier security-first proposal, preserved for later design work. It is not an active alpha requirement or an approved implementation recipe. Reassess its mechanisms when hardening is scheduled; follow the current [platform specification](../17-v2-corrected-specification.md) and [team plan](../18-four-person-delivery-plan.md) now.

# V2 four-person delivery plan

Date: 2026-10-29. Team: **Anurag + Teammate 1 + Teammate 2 + Teammate 3**.

**Goal:** deliver the corrected single-Orin collaboration pilot with clear ownership and independently testable handoffs.

**Spec:** [17 — corrected specification](../17-v2-corrected-specification.md). It is mandatory reading; this document assigns its work and does not relax its safeguards.

**Architecture:** modular monolith in the current repository; Postgres with public retrieval and encrypted confidential blobs; one collaborative room service and one local model coordinator. The three teammates develop with local Postgres, synthetic data and deterministic model fixtures. Only Anurag deploys to Orin or handles production secrets/data.

**Stack:** Python 3.12 application environment, FastAPI/Pydantic, PostgreSQL 16/pgvector/native FTS, SQLAlchemy/Alembic, pycrdt/Yjs, existing Next.js frontend, local model serving. Serving-container Python may differ from app Python; communicate over the versioned internal protocol. Exact package/image versions are locked in ticket A0 after compatibility tests, not guessed in prose.

## 1. Ownership

| Person | Owns implementation | Owns decisions/release evidence | Must not be required for routine work |
|---|---|---|---|
| **Anurag** | Shared security contracts; authentication/session foundation; broker/RLS rules; keys/deletion/recovery journal; model coordinator and serving adapters; Orin deployment | Security architecture, confidentiality, resource budgets, hardware validation, final release and production migration execution | Writing every feature, frontend styling, ordinary source normalization or all integration tests |
| **Teammate 1** | Public ingestion, source provenance, researcher identities, public Postgres retrieval/graph adapters, shortlist ranking/explanations, opportunity import, public writeback projection | Data quality and retrieval evaluation; reproducible 100k fixture/benchmark package | SSH, GPU models, private documents or production database credentials |
| **Teammate 2** | Proposal/pursuit domain APIs, direct membership/invitation workflow using Anurag's auth primitives, CRDT persistence/room service, outbox workers, outcomes, export backend | Workflow correctness, durable edit recovery, replay/idempotency tests; migration ordering integration | Implementing cryptography or inventing authorization rules; accessing Orin |
| **Teammate 3** | Frontend integration, discovery/shortlists, workspace editor, source-approval UI, membership/revoke UX, job/save/error states, export UX, browser E2E | Accessibility, workflow usability, adversarial browser cases and release demonstration | Calling model servers directly, forging tenant context or real secrets |

**Critical boundary:** T2 owns membership tables and feature operations, but invokes Anurag's broker/fence for every access. T1 owns public projection logic, but Anurag owns publication authority and lifecycle enforcement. T3 may hide controls for usability; backend permissions remain authoritative.

Anurag is the final security reviewer, not the sole test author. T1/T2/T3 write attack tests for their own surfaces; another person reviews them. Reserve **20–25% of Anurag's time for review, integration and Orin testing**, separate from feature implementation capacity. If this budget is exceeded, reduce concurrent high-risk tickets rather than bypass review.

## 2. Release scope and exclusions

Ship the complete loop: verified opportunity → public shortlist → direct invite → secure co-edit → local cited draft from approved sources → export/manual submission record → outcome ledger → explicitly approved public projection.

Do not implement persistent confidential search, immediate backup erasure, role inheritance, outcome rank bonuses, federation, automated portal submission or unrequested email delivery. The corrected spec provides useful private grounding without claiming those deferred capabilities. All confidential users acknowledge the 30-day encrypted-backup retention policy.

Global constraints: source text is untrusted; no cloud fallback; no real secrets in fixtures; auth decisions use server-derived context; no success acknowledgement before required durability; no feature imports raw confidential stores; one generator admission path; tests passing with fakes do not count as hardware/security integration acceptance.

## 3. File ownership and shared-file protocol

Paths below are **planned files**, except the existing contracts/API/frontend roots. New Python packages consistently use `packages/<name>/src/<import_root>/`; do not copy the older inconsistent layout.

| Owner | Primary paths |
|---|---|
| Anurag | `packages/contracts/src/tigerexchange_contracts/`, `packages/security/src/tigerexchange_security/`, `packages/crypto/src/tigerexchange_crypto/`, `packages/models/src/tigerexchange_models/`, `services/coordinator/`, `services/key_service/`, `services/serving/`, `deploy/orin/`, `tests/security/`, `tests/hardware/` |
| T1 | `packages/data/src/tigerexchange_data/`, `packages/discovery/src/tigerexchange_discovery/`, `packages/ingestion/src/tigerexchange_ingestion/`, `tests/data/`, `tests/retrieval/`, `tests/fixtures/public/` |
| T2 | `packages/workspace/src/tigerexchange_workspace/`, `packages/workflow/src/tigerexchange_workflow/`, `services/crdt_ws/`, `services/worker/`, `services/api/routes/`, `tests/workspace/`, `tests/workflow/`, migration sequence registry |
| T3 | `frontend/src/`, `frontend/tests/`, generated `frontend/src/lib/api-types.ts`, browser suite in external homelab checkout, `docs/qa/` |
| Shared, one integrator | Anurag: `pyproject.toml`, dependency locks, `packages/contracts/`, API composition `services/api/app.py`, `compose.dev.yml`, `.env.example`, `.github/workflows/`. T2: `migrations/` ordering. T3: `frontend/package.json` and npm lock. |

For a shared file, propose the required change in the ticket and have its integrator merge it first or review the coordinated change. Feature migrations use separate revision files; T2 assigns the parent revision before merge. Anurag reviews every role/RLS/key migration, regardless of author. No branch may rewrite another teammate's migration after merge. Application startup never drops/recreates stores.

Create CODEOWNERS/branch rules in A0 once actual repository usernames are known. Until then, use this table as the explicit review checklist; do not commit invalid placeholder GitHub handles. One ticket per short-lived branch (`v2/a1-auth`, `v2/t1-2-search`, etc.); merge via reviewed PR, no direct shared-branch pushes. No automatic production deployment from feature branches.

## 4. Contract handoff before parallel integration

Anurag owns the canonical types; everyone reviews the first contract PR. API JSON uses snake_case, UUID strings, RFC3339 UTC times and explicit enum values. Bodies reject unknown fields. Expected failures use `{error: {code, message, request_id, retryable}}`; no stack traces/content in messages. Pagination uses an opaque cursor and a server max page size of 50. Mutations carry `Idempotency-Key`; incompatible version changes return 409. Endpoint handlers call operations, not authorize-then-use booleans.

### Shared values and internal interfaces

Define in `packages/contracts/src/tigerexchange_contracts/v2.py` and split by responsibility in the same package once frozen:

| Type/interface | Contract |
|---|---|
| `Actor` | authenticated `user_id`, `session_id`; server-populated only. Active session rechecked at admission. |
| `DocumentRef` | `document_id`, `owner_tenant_id`, `lifecycle_generation`, `audience_epoch`; returned internally from trusted storage, not authority from request fields. |
| `SourceRef` | `source_id`, immutable `version`, `content_hash`; content fetched only after audience validation. |
| `OperationContext` | actor, document, action, request_id; constructed by broker after authentication. No external DTO can construct effective authority. |
| `WorkspaceView` | proposal_id, version, role, audience_epoch, saved_sequence, lifecycle state, authorized fields. |
| `SearchPage` | items of public `work_id/chunk_id/source_version/title/snippet/citation_url/score/explanation`, next_cursor, degraded flag; no confidential items. |
| `JobView` | job_id, state (`queued/running/succeeded/failed/cancelled`), safe error code, queue_position, created_at; no raw prompt. |
| `OutcomeInput` | pursuit_id, expected_version, outcome (`won/lost/withdrawn`), recorded_at, optional verified award reference; details encrypted. |
| `IWorkspaceFence.operation(actor, proposal_id, action)` | async context manager yielding OperationContext while shared transaction lock and fresh checks remain active. Teammates must enqueue/persist within it; never retain context as later permission. |
| `IWorkspaceFence.revoke(actor, proposal_id, subject_id, idempotency_key)` | returns `RevocationReceipt(operation_id, audience_epoch, acknowledged_at)` only after DB commit and recovery journal durability. |
| `IDocumentCrypto.encrypt(document_ref, kind, sequence, plaintext)` | returns opaque `EncryptedPayload(key_id, nonce, ciphertext, aad_version)`; Anurag's adapter owns key lookup and canonical AAD through the authenticated Unix-socket key-service client; it is not an in-process master-key holder. `decrypt(...)` additionally verifies expected ref/kind/sequence before returning bytes. |
| `IPublicSearch.search(actor, query, filters, cursor, limit)` | returns SearchPage. Optional reranker consumed through IPublicModelOps; no database credentials or private search surface exposed. |
| `ISourceApproval.approve(actor, proposal_id, sources, expected_audience_epoch, idempotency_key)` | owner-only; persists exact immutable source approvals. Admission/activation of a new member requires audience-expansion confirmation. |
| `IModelJobs.submit(actor, proposal_id, sources, instruction, expected_version, idempotency_key)` | returns JobView after validation; captures source/audience generations. Status/cancel/result operations reauthorize. Confidential output delivery uses the workspace fence. |
| `IPublicModelOps.embed_public(texts, model_version)` / `rerank_public(query, candidates)` | Public-only typed input, returns versioned vectors / scores with degraded/error state. Internal service identity and resource coordinator enforce batch/token limits, GPU exclusion and interactive-draft priority. Never accepts confidential text from feature callers. |
| `IPublication.publish(actor, source_ref, exact_projection, approval_id, generation, event_id)` | validates trusted/public provenance or explicit owner approval; atomically applies active matching generation and receipt; never accepts a tier label as sufficient evidence. |

IDs name resources; they never authorize them. Source instruction text is confidential input and must not be stored in plaintext job rows. T2 owns domain DTOs after the first contract merge; changes to shared security fields require Anurag review. T3 generates API types from the same OpenAPI contract, not handwritten competing enums.

### Browser endpoint ownership

All under `/api/v2`; frontend uses a same-origin configurable base, never hardcoded localhost.

| Endpoints | Owner | Required behavior |
|---|---|---|
| `/session`, `/login`, `/logout`, `/csrf` | Anurag | session/CSRF/login limits; no identity from body claims |
| `GET /search`, `GET /researchers/{id}`, `POST /shortlists/preview`, `GET /opportunities` | T1 with T2 route integration | public results, explanations, provenance, safe pagination |
| `POST /pursuits`, `GET/PATCH /pursuits/{id}`, `POST /pursuits/{id}/outcomes` | T2 | explicit transitions and version/idempotency checks |
| `POST /proposals`, `GET /proposals/{id}`, `POST /proposals/{id}/invitations`, `POST /invitations/accept`, `DELETE /proposals/{id}/members/{user_id}` | T2 | owner/guest isolation; revoke invokes Anurag's durable operation |
| `POST /proposals/{id}/sources`, `POST /proposals/{id}/source-approvals`, `POST /proposals/{id}/draft-jobs` | T2 + Anurag adapters | isolated bounded upload; owner approval; queue/revocation integration |
| `GET/DELETE /jobs/{id}`, `GET /jobs/{id}/events`, `POST /proposals/{id}/suggestions/{job_id}/accept` | T2 with Anurag coordinator | SSE results authorized per batch; optimistic document version; cancellation acknowledgement truthful |
| `GET /proposals/{id}/export?format=markdown\|docx`, `DELETE /proposals/{id}` | T2 | fence + ephemeral generation; no deletion of unrelated keys |
| `POST /admin/tenants/{id}/offboarding` | Anurag | administrator-only audited lifecycle operation; explicit confirmation of tenant ID; idempotent receipt after tenant denial and journal durability, cleanup progress separate |
| `WS /ws/v2/proposals/{id}` | T2 server / T3 client | authenticated origin, bounded CRDT envelope and saved-sequence ACK |

Frontend chat/graph legacy calls are retired or redirected through the new supported screens; do not imply `/api/chat` is restored unless an explicit compatibility adapter is implemented and tested. No GraphQL or second API surface.

## 5. Local development without Orin

A0 delivers `compose.dev.yml` (Postgres 16 + pgvector), `scripts/dev/bootstrap.sh`, locked app dependencies and `scripts/dev/seed.py`. Each teammate runs an isolated database and uses synthetic tenants Alpha/Beta, an owner/editor/viewer/guest, public papers, secret-source canaries and tombstoned documents. Test keys are generated locally, never copied from production.

Anurag supplies deterministic fixture implementations of model jobs and crypto **protocols**, plus the real local application crypto adapter for security tests. Fake generation returns citations and queued/streaming/error/cancel scenarios from fixtures; it does not purport to judge quality. Default dev mode is explicit; production boot rejects fixture providers, test keys and insecure cookie settings. Database/RLS/outbox/CRDT tests use real local Postgres, not a fake dictionary store.

T1 creates small fixed public embedding fixtures with version/dimension metadata; a 100k synthetic benchmark dataset is reproducibly generated, not checked in as a giant binary. T2 and T3 use contract fakes until Anurag's broker is available; those branches cannot be released or marked integrated until real broker tests pass. All teammates can run real crypto and CPU protocol tests without GPU access.

Browser E2E belongs in `~/code/homelab/tiger_research_buddy/`, following `homelab/AGENTS.md`, with `TIGER_RESEARCH_BUDDY_REPO` pointing to this checkout. T3 adds the suite there and links its commit/results in this repo's `docs/qa/`. In-repo frontend tests cover components and API DTOs; do not create a second browser suite here. A0/T3 document the exact E2E command after reading the external suite conventions. Orin browser smoke tests are run by Anurag from T3's reproducible instructions.

## 6. Work packages and dependency order

Each ticket below follows this checklist; a ticket is not complete just because code exists:

- [ ] Add the named failing tests and confirm the expected failure (not an unrelated import/environment failure).
- [ ] Implement the listed interface/files against the corrected spec; use the shared contract types.
- [ ] Run the indicated tests and applicable lint/type checks in the locked environment.
- [ ] Submit a small PR with behavior, evidence, remaining limitations and migration impact.
- [ ] Obtain the assigned review and merge; publish the handoff fixture/contract for dependents.

Paths in the test column are files to create. `pytest <listed test paths>` must pass with no skipped required cases; hardware tests are a separate mandatory gate owned by Anurag. T3 uses the frontend test runner established in F0; browser tests use the external homelab runner.

| ID / owner | Concrete deliverable and primary files | Depends on | Acceptance test files and assertions | Reviewer |
|---|---|---|---|---|
| **A0 / Anurag** | Contract baseline `contracts/.../v2.py`, project/dependency locks, compose.dev.yml, fixture providers, CI, synthetic identity schema and Orin smoke report | none | `tests/unit/contracts/test_v2.py`: reject client authority fields; stable enums/error DTOs. `tests/integration/test_dev_boot.py`: fresh clone migration/seed/API boot; production rejects fakes. Orin actual image/model loads. | T2 + T3 |
| **A1 / Anurag** | `security/.../identity.py`, `broker.py`, `fence.py`; RLS template and narrow runtime grants; login/session routes | A0 | `tests/security/test_tenant_access.py`, `test_sessions.py`: owner CRUD succeeds, foreign/empty/reused context denied, forged tenant/body fields rejected, expired session/CSRF/origin tests. | T2 |
| **A2 / Anurag** | `crypto/.../envelope.py`, `keys.py`, `journal.py`, `security/.../revocation.py`; document keys, scoped delete/offboarding and recovery acknowledgements; publication approval/generation authority tables and broker operation; `services/key_service/main.py` + socket client | A1 | `tests/security/test_crypto.py`, `test_revocation.py`, `test_restore.py`: AAD/nonce isolation, provisioning crash/retry/orphan cleanup, delete X preserves Y, dropped notify, crash/response retry, old-backup tombstone replay, journal disk full. | T2 + T1 |
| **A3 / Anurag** | `models/.../jobs.py`, `provider.py`; `services/coordinator/main.py`, serving manifests, egress/resource controller and job HTTP adapter | A0; A1/A2 for confidential delivery | `tests/security/test_model_admission.py`: multiple processes serialize all requests, cache config verified, queue fairness, cancellation cannot release running job, invalid destination blocked before send. `tests/hardware/test_serving_budget.py`: real load/latency/memory. | T1 |
| **A4 / Anurag** | `deploy/orin/`, backup/restore runbook and release evidence; execute migrations and pilot deployment | integrated D/W/F tickets | `tests/hardware/test_pilot_soak.py`, `tests/security/test_recovery_drill.py`: target envelope/retention/RPO/RTO; production auth/keys, upgrade and rollback drill. | T2 + T3 |
| **D0 / T1** | `ingestion/.../normalize.py`, `provenance.py`, public fixtures; minimal source/license/identity tables migration | A0 DTOs; can prepare fixtures immediately | `tests/data/test_public_import.py`: stable IDs, duplicate import, unknown license quarantine, unresolved ORCID remains unresolved, no name merge. | T2 |
| **D1 / T1** | `data/.../public_store.py`, `retrieval.py`; vector/FTS/RRF adapter and indexes | D0, A0 database | `tests/retrieval/test_hybrid.py`: actual SQL executes, reproducible ordering with ties, model/dimension mismatch rejected, lexical degradation explicit, no private source results. | Anurag (boundary), T2 (SQL) |
| **D2 / T1** | `discovery/.../ranking.py`, `explanations.py`, `ingestion/.../opportunities.py`; shortlist + one public import adapter/manual opportunity schema | D1 | `tests/retrieval/test_shortlists.py`, `tests/data/test_opportunities.py`: coverage gaps, no outcome boost, provenance, timezone/unknown eligibility, source fetch SSRF/size limits. | T3 + T2 |
| **D3 / T1** | `data/.../publication.py`, outcome-public projection adapter and offline evaluation report | A2 publication lifecycle, W3 | `tests/data/test_publication.py`: false PUBLIC label denied, active generation equality, high-version replay denied, hidden awards/edges stay hidden; baseline evaluation reproducible. | Anurag |
| **D4 / T1** | `scripts/bench/public_retrieval.py`, benchmark fixture manifest, ingestion ops notes | D1/D2 | `tests/retrieval/test_corpus_limits.py`: 100k cap, bounded batches; deliver script/hash/expected output to Anurag, record actual hardware report when returned. | Anurag |
| **W0 / T2** | `workflow/.../pursuits.py`, `workspace/.../proposals.py`, direct membership/invitations; domain migrations and API routers | A0 for scaffolding; A1 for integration | `tests/workflow/test_states.py`, `tests/workspace/test_membership.py`: versions/idempotency, owner vs editor/viewer, invite expiry/replay/recipient binding, no inherited permissions. | Anurag |
| **W1 / T2** | `workspace/.../persistence.py`, `room.py`, `services/crdt_ws/main.py`; encrypted update log and snapshot compaction | W0, A1, A2 real crypto/fence | `tests/workspace/test_crdt_recovery.py`, `test_revocation_races.py`: two-client convergence, viewer blocked, commit-before-saved, duplicate batch, crash after commit, snapshot-tail preservation, concurrent-update serialization/combined-size overflow, revoked client cannot read/write. | Anurag + T3 |
| **W2 / T2** | `workspace/.../sources.py`, `suggestions.py`, `export.py`; source approval, generation orchestration, Markdown/DOCX export | W0, A2; A3 for actual generation | `tests/workspace/test_audience.py`, `test_export.py`: approved-source guest-editor drafting succeeds; read-only source cannot be redistributed; source withdrawal during stream and expanded audience deny; stale result not inserted, revoked export denied, isolated upload limits, source removal marks dependent content. | Anurag + T3 |
| **W3 / T2** | `workflow/.../outcomes.py`, `outbox.py`; worker claims, receipts and retry/dead-letter; loop metrics | W0 | `tests/workflow/test_outbox.py`, `test_outcomes.py`: reverse commit order, crash after effect, repeated correction, lease takeover, dedup receipt, won/lost/withdrawn distinct. | T1 + Anurag (public effects) |
| **W4 / T2** | `tests/integration/test_collaboration_loop.py`, migration upgrades, service health/readiness and repair scripts | W1–W3, D3, A3 | Full real-DB path: shortlist→invite→edit→draft→export→outcome; restore and publication visibility checks; readiness rejects locked/recovering deployment. | Anurag + T3 |
| **F0 / T3** | `frontend/src/lib/api.ts`, generated types, auth layout/components, frontend test setup | A0 contracts; UI fixtures can begin immediately | `frontend/tests/api.test.ts`: same-origin requests, error envelope, CSRF, no client tenant authority; component tests for expiry/login state. | T2 |
| **F1 / T3** | discovery/shortlist/opportunity/pursuit screens; replace legacy 404 API calls | F0, D2/W0 fixtures then real APIs | `frontend/tests/discovery.test.tsx`: loading/empty/error/degraded states, eligibility unknown, explanations, keyboard operation; real API browser flow. | T1 |
| **F2 / T3** | workspace editor, invite/role/revoke controls, source-approval and audience-expansion consent | F0, W0/W1/W2 fixtures then real APIs | `frontend/tests/workspace.test.tsx`; external E2E: two users converge, viewer cannot edit, unsaved state truthful, revoked guest loses both send/receive, reconnect cannot resurrect. | T2 + Anurag (consent wording) |
| **F3 / T3** | draft job queue/stream/cancel UI, citation/source panel, accept suggestion/export/outcome UX | F2, A3/W2/W3 | `frontend/tests/drafting.test.tsx`; E2E: stale result rejected, queue timeout/cancel, source permission changes, citations authorized, export readable and current. | T2 + T1 |
| **F4 / T3** | external homelab E2E suite, `docs/qa/pilot-checklist.md`, accessibility and pilot walkthrough/report | F1–F3, W4 | browser tests exercise both successful workflow and failure matrix; no private data in screenshots/traces; release demo uses real backend with provider profile identified. | Anurag |

## 7. Schedule and integration gates

Availability and teammate experience were not supplied. The following is a **full-time planning scenario**, with about 30 focused delivery hours/person/week and explicit review allowance. It is not a promised date. Re-estimate after week 2 using completed tickets and measured Orin blockers.

| Window | Anurag | Teammate 1 | Teammate 2 | Teammate 3 | Gate |
|---|---|---|---|---|---|
| Week 1 | A0 contracts/dev baseline + initial hardware smoke | D0 fixtures/provenance | W0 domain schema/API proposal + migration map | F0 API client/auth shell from fixtures | **G0:** contracts, local boot, signed-off ownership and representative hardware evidence |
| Week 2 | A1 auth/RLS/broker; publish real adapters | D1 real retrieval SQL | W0 direct membership and pursuit routes | F1 public workflow | **G1:** owner allowed, foreign tenant denied; all three teammates run locally |
| Weeks 3–4 | A2 keys/fence/recovery journal | D2 ranking/opportunities | W1 persistence + websocket integration | F2 editor with real backend | **G2:** public workflow and durable two-user co-edit; no confidential pilot launch yet |
| Weeks 5–6 | A3 serving/coordinator; review audience/fence races | D3 publication + D4 benchmark package | W2 source/drafting/export; W3 outbox | F2 completion + F3 queue/citations/export | **G3:** synthetic confidential loop, scoped revoke/delete, duplicate/out-of-order events pass |
| Weeks 7–9 | A4 deployment/backup/soak; resolve hardware bottlenecks | retrieval quality/data corrections and Orin report analysis | W4 integrated tests/migration/recovery | F4 E2E/accessibility/error-state polish | **G4:** real Orin loop and recovery drill; no unresolved release-blocking security defect |
| Weeks 10–12 | release review and limited consenting pilot | expert shortlist/source evaluation | pilot defects and operations | user walkthroughs and regression E2E | **G5:** repeat collaboration evidence and documented operating limits |
| Weeks 13–16 if needed | reserved for key/recovery/ARM64 or pilot findings | support critical fixes | support critical fixes | support critical fixes | contingency, not new features |

Expect **12–16 calendar weeks** for a credible limited pilot with four suitably experienced full-time people. Do not divide the previous solo estimate by four: Anurag's security/hardware path remains sequential. A public-only demo may land in weeks 3–4; it is not the confidential pilot.

Revised capacity budget: Anurag **9–12 focused engineer-weeks**, T1 **6–9**, T2 **8–11**, T3 **7–10**, totaling **30–42 engineer-weeks**. This expands the earlier rough 13–20-week pilot estimate because the now-explicit scope includes fenced delivery, a separately durable revocation journal, full account lifecycle, encrypted CRDT log recovery, operational restore drills and four-person integration. The earlier estimate should not be used as a commitment. If capacity is part-time, scale by focused hours and preserve the Anurag critical path; do not assume extra frontend capacity can absorb key-management or hardware work.

The full historical P0 feature set has **no committed date**. Persistent confidential search/erasure is a separate security/storage project; inherited roles, broader sources and ranking experiments follow measured pilot demand. Estimate those from their reviewed designs, not from the old phase labels.

## 8. Handoffs and Orin queue

Every handoff contains: contract version/commit; synthetic input fixture; expected output including failures; exact setup/test command; migration/dependency impact; current evidence tier (`unit`, `real-db`, `browser`, `orin`); known limitations. A mock screenshot is not an integrated feature.

T1 sends benchmark scripts/corpus manifest to Anurag; Anurag returns image/model hashes, run command, board memory, p50/p95 timings and thermal notes. T2 sends migration + recovery/race test bundles; Anurag runs them in isolated Orin staging before production. T3 sends browser suite revision and walkthrough; Anurag runs the real deployment smoke and returns sanitized results. No one needs Orin credentials for these handoffs.

Keep a single hardware validation queue in `docs/qa/orin-validation-queue.md` (A0 creates it): ticket, commit, command, fixture hash, expected criteria, priority, runtime estimate, result link. Reserve two validation windows/week; one-hour urgent security window when feasible. Batch compatible model tests to avoid unnecessary model swaps. No teammate requests a production model restart directly. Do not run deployment-mutating tests against the live pilot.

Anurag's absence allows local work and reviewed merges that do not change security contracts; it pauses Orin releases, secret rotation, security-sensitive merges and destructive migrations. Document recovery steps so others can diagnose from sanitized logs, without granting them production secret access.

## 9. Review focus and release checklist

The five cross-cutting failures most likely to escape isolated feature tests are mandatory gate tests:

1. Guest is allowed into a proposal but sees a source approved only for the owner — W2/A2/F3 must deny it before model admission and delivery.
2. Revocation races with already-open websocket/export/generated-output delivery — A2/W1/F2 must test outgoing as well as incoming bytes under the fence.
3. Restore revives a deleted document or expired membership — A2/A4 must restore an older backup and replay the independent latest journal before accepting users.
4. Retried/out-of-order events duplicate wins or miss an earlier commit — W3/D3 must verify atomic receipts and explicit pending-row claims.
5. Orin job cancellation/worker death frees admission while old work still runs — A3/A4 must prove no new model work until abort/reconciliation completes.

- [ ] Fresh checkout boots from locked dependencies; exact schema upgrade path tested.
- [ ] Positive functionality and negative access tests pass on real Postgres.
- [ ] No fake provider/test keys/insecure settings in production startup.
- [ ] Real editor retains acknowledged updates across server+client crash; unsaved edits are labeled honestly.
- [ ] Audience, revocation, deletion and publication tests pass with canary secrets.
- [ ] Outbox corrections/retries/dead-letter replay are deterministic.
- [ ] Orin capacity, queue fairness, cancellation, model locality and maintenance transitions pass measured limits.
- [ ] Backup restoration, latest revocation journal, recovery secret and deletion-retention behavior are demonstrated.
- [ ] Frontend E2E passes against the real API; keyboard/focus/errors/citations/export checked.
- [ ] Pilot users see and accept source-sharing and backup-retention terms; no unsupported privacy/learning promises.
- [ ] Anurag and one teammate review the complete evidence bundle; unresolved release blockers keep the pilot closed.

## 10. First five working days

**Anurag:** merge contract/dev foundation; validate one real Orin inference; define DB roles and review synthetic fixtures; publish the real broker interface and first RLS tests; set the two weekly hardware windows. Do not begin by expanding the model fleet.

**Teammate 1:** inventory reusable extraction/ranking code, identify cloud dependencies to exclude, create licensed/synthetic public fixtures, define provenance/identity normalization and executable public-store migrations, then implement D0 against the contracts.

**Teammate 2:** propose domain table/transition map and migration sequence, implement W0 with explicit direct roles and contract stubs, prepare invitation/version/idempotency tests, agree the encrypted CRDT batch envelope with T3 before editor work diverges.

**Teammate 3:** inventory existing frontend calls, create the same-origin typed client and deterministic state fixtures, build discovery/error/auth flows, pair with T2 on websocket saved/unsaved protocol, locate the external homelab suite and document how the other three run it.

End-of-week review: demonstrate a fresh local boot on each laptop and the contract fixtures running through the UI; list remaining interface mismatches. Do not count four disconnected demos as one integrated system.
