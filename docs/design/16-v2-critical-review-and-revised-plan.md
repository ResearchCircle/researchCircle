# V2 critical review and revised delivery plan

> **Current priority (2026-10-30):** The user chose working product first and security hardening later. This audit is historical evidence, not the active release checklist. Follow the [working product specification](17-v2-corrected-specification.md) and [team plan](18-four-person-delivery-plan.md); the earlier hardening proposal is preserved under `reference/`. Historical secure-pilot estimates do not apply to the narrower product alpha.

Review date: 2026-10-29. Repository baseline: `d4e3505`.

**Verdict: the direction is credible; the current specification is not safe to implement verbatim.** It contains executable contradictions, incorrect security arguments, and a first release that postpones product validation until after most infrastructure is built. Keep the modular monolith, local inference, public/private separation, bounded ingestion, and explicit authorization boundary. Replace the guarantees and sequence below before treating this as a release contract.

This is an audit and proposed replacement delivery sequence, not evidence that the implementation has been fixed. References are repository paths and section numbers. Findings distinguish observed code, logical counterexamples, and unmeasured assumptions. The review concentrated on the load-bearing contracts and execution paths; it is not an exhaustive line-by-line certification of the entire corpus.

## 1. Release blockers

### B1 — The prescribed RLS policy denies legitimate access

Evidence: `13-data-model-and-schemas.md` §0.3–0.4 prescribes exactly one RESTRICTIVE policy and bans PERMISSIVE policies; `06-security-spine-lld.md` §4 repeats the ban. PostgreSQL requires an applicable permissive policy before restrictive policies can narrow access. Consequently, the copied design denies tenant A's legitimate reads/writes as well as tenant B's attacks. Negative-only security tests can report success on a completely unusable database.

Correction: define one explicit permissive application-access policy, with a restrictive tenant boundary; allow only the reviewed permissive policy in migration checks. Derive the tenant from authenticated server context, never request JSON. Normalize an empty tenant setting before casting, e.g. `NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Test fresh and reused pooled connections. Grant access through the partitioned parent only; deny direct child-table access rather than relying on the statement that partitions inherit protection for every access path.

Acceptance: A can perform intended CRUD; B cannot; absent/empty tenant context returns no data; malformed context fails closed; A→B→unset reuse cannot leak; direct partition access fails. Run actual PostgreSQL 16 migrations, not mocked policy checks.

Primary reference: [PostgreSQL CREATE POLICY](https://www.postgresql.org/docs/16/sql-createpolicy.html).

### B2 — Per-tenant tablespace encryption does not prove per-tenant erasure

Evidence: conventions D7, `06` §7–8, `13` §10/22 promise destruction of a tenant key makes all searchable content unrecoverable. Meanwhile the design places WAL on shared NVMe and recommends PITR backups (`06` final risk table). PostgreSQL can write full data pages to WAL. Encrypting a tenant's tablespace does not put those shared WAL records under the tenant key. Restorable wrapped keys, backups, temporary spills, process memory, and mounted dm-crypt mappings also remain part of the threat model.

Counterexample: retain an accessible pre-deletion backup/WAL sequence and its recoverable wrapping keys; destroy the current tablespace key; restore the older state. A failed application query after deletion is not proof that no decryptable copy exists. Whole-disk encryption with a retained shared key does not solve selective tenant erasure.

Correction for the first pilot: persist confidential documents only as application-encrypted blobs; use explicitly selected, authorized documents for drafting. Defer persistent confidential vector/BM25 indexes. Describe access revocation and retention honestly, with no immediate all-backups erasure claim. Before offering cryptographic erasure, design the complete key/backup lifecycle and independently review it. If persistent confidential search remains mandatory, investigate a separate encryption domain covering data, WAL, temp, indexes, and backups; a separate cluster per domain has resource and operations costs that must be measured.

Acceptance: inventory every plaintext/key-bearing surface; restore pre-deletion backups in an isolated recovery test; verify that the documented deletion scope and recovery policy hold. Do not weaken durability by disabling WAL to pass the test.

Primary references: [PostgreSQL WAL settings](https://www.postgresql.org/docs/16/runtime-config-wal.html), [database file layout](https://www.postgresql.org/docs/16/storage-file-layout.html).

### B3 — Object deletion and collaborator revocation have inconsistent blast radii

Evidence: `11` §7.4 correctly separates removing a collaborator from destroying an object, but then prescribes a tenant key for proposal erasure. `06` §11.1 calls tenant `destroy_kek()` for every security/consent reason, without distinguishing grant, proposal, and tenant. The precedence rules make this especially dangerous: the security chapter can override the narrower workspace behavior.

Counterexample: erase one proposal and destroy the key protecting all of the group's other proposals. Or revoke one guest and make every legitimate collaborator lose decryptability.

Correction: three separate operations and schemas: revoke a principal's grant; delete one document using a document-specific key and retention workflow; offboard a tenant. Define exact transitive deletion dependencies. Store immutable document/key identifiers and lifecycle state; never infer deletion scope from a free-form reason alone. Old wrapped-key copies must be addressed before promising cryptographic erasure.

Acceptance: removing guest B preserves owner A's access; deleting proposal X preserves proposal Y; tenant offboarding affects all and only that tenant's artifacts.

### B4 — The anti-resurrection predicate permits resurrection

Evidence: `13` §23 and `09` §11 / `12` §8 compare projection version to current version and revocation epoch.

Concrete counterexample: current version 10, revoked epoch 11, incoming version 12. Both documented comparisons pass. A newer update is not renewed consent. A single ingestion writer does not serialize against a separate revocation transaction.

Correction: use explicit lifecycle state plus a separate authorization generation. Ordinary ingestion cannot clear a tombstone. Only an audited owner-authorized restore transition creates a new generation. Apply projections under a row lock or equivalent atomic conditional update with generation equality, active-state check, and increasing content version. Preserve tombstones across record deletion/recreation and aliases.

Acceptance: stale replay, higher-version replay, concurrent revoke/apply, changed external identifier, and post-restore replay of the old generation. Test grants independently from object tombstones.

### B5 — Zero-window websocket revocation is not implemented by notification

Evidence: `11` §4 and §7 authorize at connection time, periodically recheck, and close on post-commit notification. Between commit and notification, a connected guest can still receive broadcasts or submit updates. The next PEP check denying access does not protect traffic that does not invoke that check. In-process broadcasts also do not cross API/websocket process boundaries.

Correction: define an enforceable ordering contract: after revocation acknowledgement, no new server-authorized document operation or disclosure for that principal may occur. Coordinate room authorization epochs, operation admission, outgoing broadcasts, and revocation through a shared authority. Stop admission and fence/drain affected operations before acknowledging revocation; failures keep the room closed. Notifications accelerate cleanup but are not authority. Specify how in-flight network bytes and previously downloaded copies fall outside revocation's ability to retract data.

Acceptance: pause/drop notifications, revoke during outgoing broadcast and incoming update, disconnect the authority, restart one process, reconnect with stale credentials, and revoke during streamed generation. Verify both read and write directions.

### B6 — Revocation durability pseudocode is wrong

Evidence: `06` §11.1 executes CHECKPOINT inside the transaction, before setting `committed=true`. CHECKPOINT is a privileged maintenance operation, not a transaction commit. The application role in `13` §0.2 is not granted the required privilege. A crash before commit rolls back the transaction; setting a boolean does not create durable evidence.

Correction: atomically remove the grant/update lifecycle state, increment the authorization generation, append the tombstone and durable event, then COMMIT with synchronous_commit enabled. The committed row is the fact; remove the misleading durability boolean. Acknowledge success only after commit and the operation fence required by B5. Use idempotent retry identifiers; distinguish a request that never committed from an acknowledged revocation. Restore must replay revocations before reopening access.

Acceptance: inject crashes before commit, after commit/before response, after response, and before notification. Acknowledged revocations survive; uncertain requests can be safely retried.

Primary reference: [PostgreSQL CHECKPOINT](https://www.postgresql.org/docs/16/sql-checkpoint.html).

### B7 — Private grounding can leak through an intentionally shared draft

Evidence: `11` §6 authorizes a guest to a proposal; `07` §12 and `11` §11 ground drafting on the owner's confidential corpus. Permission to collaborate on proposal X is not permission to read all prior proposals used as context. Owner-only retrieval does not prevent disclosure when its generated output is broadcast to the guest.

Correction: introduce document audience/provenance rules. Generate shared text only from sources approved for that audience. Otherwise keep the result owner-private until an explicit release decision. A confidentiality tier alone cannot express which people are allowed to see a document. Apply the rule to citations, titles, snippets, exports, reranking, logs, and generated text.

Acceptance: owner has a secret prior proposal, guest can edit only X; adversarial prompts and ordinary synthesis must not expose the secret to the guest. Adding a guest must not silently broaden the audience of existing derived text.

### B8 — The classifier/type checks do not establish confidentiality

Evidence: `12` §8.1 says a projection cannot leak confidential content even if mislabeled. `05` §7 checks the tier label, not the provenance of arbitrary field values. A confidential string stamped PUBLIC passes that check. `05` permits PRIVATE projections while the public shared surface elsewhere requires PUBLIC-only content; `13` repeats a different projection schema/default.

Correction: public ingress must come from a trusted public source or an explicit authorized publication transition. Classification can quarantine but cannot independently declassify private uploads. Broker validation derives tier/audience from durable provenance and field allowlists. Keep public and private projection types/sinks distinct; generate documentation from the executable contract. Remove unsafe generic field bags where a concrete public schema is possible.

Acceptance: mislabeling, prompt injection in imported text, mixed-provenance derivation, poisoned metadata, and public summaries of secret sources. Record classifier false negatives on a held-out set; zero observed leaks in a finite set is not a universal guarantee.

## 2. Other material changes

| Finding and evidence | Correction and acceptance |
|---|---|
| `08` §4/7 isolates only confidential calls; public calls bypass that semaphore. A local semaphore also does not coordinate multiple worker processes. Thus its claim that no other request's KV is resident is not established. | One global admission controller for all generator traffic if strict exclusion is required. Start with prefix caching disabled for the entire process. Verify deployed engine behavior, abort/completion semantics, timeouts and process restarts. Do not claim process or physical memory isolation from serialization. |
| `08` assumes a request `extra_body.enable_prefix_caching` toggle and later says public caching is on, while other passages recommend global off. | Pin and probe the installed API; an accepted extra JSON field does not prove behavior. Use documented engine configuration. Current vLLM describes tenant cache salts, but that is not proof the planned build supports any particular per-request toggle. See [vLLM security](https://docs.vllm.ai/en/stable/usage/security/) and [cache configuration](https://docs.vllm.ai/en/latest/api/vllm/config/cache/). |
| `08` calls embed/rerank non-sensitive although confidential source text flows through both. | Apply the same locality, logging, authentication, size limits, and retention controls to all model operations. Check the destination before sending bytes; a result's served_locally flag cannot undo egress. |
| `06` §8.2 directly derives a master key from a passphrase with SP 800-108. | Use a password-hardening KDF such as Argon2id with measured parameters and unique salt; use key expansion separately. Document recovery, rotation, operator access, and backup interaction. [RFC 9106](https://www.rfc-editor.org/info/rfc9106/). |
| `13` §0.2 grants generic UPDATE/DELETE to all tables, including audit/revocation/key records. | Grant by role and table purpose; append-only audit/tombstone writers, restricted key access, migration credentials absent from serving processes. A hash chain is not tamper protection against a writer able to rewrite the whole chain. |
| `07` §5 says confidential SQL differs only by table name, but `13` confidential entries have entry_id/source_proposal_id, not chunk_id/work_id. Partitioned DDL is left as prose despite “copy verbatim” instructions. | Executable migrations and separate tested adapters or a common explicit query projection; compile/run every published SQL example in CI. Pin one BM25 extension/version after the ARM64 spike. |
| `09` §12 advances a global outbox sequence cursor. Sequence allocation need not equal commit order; sequence 10 can commit after 11 is consumed. Run dedupe does not make additive outcome updates idempotent. | Claim pending rows using leases/status and retry failures; retain a unique consumed-event receipt in the same transaction as effects. Make graph/fingerprint changes deterministic or ledger-derived. Test out-of-order commits and crash after each partial effect. |
| `13` §13 denormalizes inherited roles but does not fully specify invalidation of all implied grants. | Prefer direct proposal membership in the pilot. If inherited roles remain, preserve derivation provenance and transactionally invalidate descendants on role/group changes. Test multiple independent grant paths and downgrades. |
| `07` §14 budgets ~7 GB for indexes while its own million-vector estimate reaches 6–8 GB before lexical indexes and other hot data. `08` throughput numbers are planning assertions, not measured results here. | Start with ~100k chunks; benchmark 100k, 300k and 1M separately. Account for table/TOAST data, lexical indexes, index builds, page cache, KV, context lengths, and concurrent processes. Record peak board memory, p50/p95 latency, thermals, OOM/restart behavior. |
| `08` expects ~16 seconds per isolated draft with a 30-second queue timeout and depth 16. | Measure demand and cap completion tokens. At ~16 seconds/service, sustained capacity is only ~3.75 requests/minute before other work. A deep queue is not responsive concurrency. Return explicit queued/busy/cancelled states; protect tenants from monopolization. |
| Separate ingestion/writeback processes cannot share an ordinary asyncio semaphore (`08`/`09`/`12`). Long GPU jobs do not instantly yield because an interactive request arrives. | One cross-process regime owner with leases, bounded batches, fencing and recovery; drain model jobs before regime changes. Test owner death and stale lock holders. Schedule bulk ingest visibly. |
| `11` §12 explicitly accepts up to 30 seconds of lost edits, while `14` P0.9 refers to snapshot plus CRDT log recovery. | Choose one durability contract. Prefer encrypted update batches persisted before a “saved” acknowledgement; compact to snapshots. If accepting 30-second loss, display unsaved state and test simultaneous client/server loss. |
| Public outcome fingerprints and co-PI edges in `12` can reveal non-public awards, team membership, or research topics even if artifacts pass classification. | Require publication authorization for every public derivative, not only WORK artifacts. Keep confidential outcomes private until verified public or explicitly released. |

## 3. Product validity: the loop is a hypothesis

“A win changes a ranking” proves mutation, not learning or improvement (`12` §7/11; `14` P0.10). Funding is delayed, confounded by seniority and institution, and sparse. The proposed positive bump is a heuristic, not a learned model. A coefficient smaller than the sum of other coefficients does not bound influence unless score scales are normalized. Capped bonuses can still entrench incumbents.

Keep the outcome ledger, but default its ranking weight to zero until an evaluation beats a fixed baseline. Record wins, losses, withdrawals, missing outcomes, provenance, award corrections and time. Deduplicate awards. Use a time-separated evaluation to avoid training on future outcomes; report subgroup/career-stage effects and recommendation coverage. Initially prioritize researcher judgments of fit and whether invitations lead to useful collaboration.

The competitive absolutes in `01` §2 (“nobody,” “zero confidentiality,” “only design”) are unsupported by this audit. Treat differentiation as a hypothesis requiring current evidence, not an architectural premise. Confidential grounding is valuable only if groups will provide usable prior proposals and authorize their reuse.

Suggested pilot: two or three consenting groups, one funding domain, one narrow public corpus, several real funding calls. Measure time to an accepted shortlist, invitation acceptance, repeat cross-group editing, citation correctness, export usability, and researcher-reported time saved. A joined account alone is a weak activation metric. Define submission as recorded/exported by the user; do not imply the product submits to funder portals. Add deadline/eligibility verification and an explicit human checkpoint before users rely on an opportunity match.

## 4. Current implementation versus target

| Area | Observed current state | Gap |
|---|---|---|
| P0.0 contracts | Ten Python modules and six passing kernel tests. | Partial and incompatible with the design: PepRequest lacks required_capability/resource_tier/relation; projection scope defaults PUBLIC rather than NONE; protocols differ materially. Not a completed frozen kernel. |
| API | `api.py` and `services/api/main.py` import `services/api/app.py`; only healthz is a product route. | Authentication, tenant context, all product routes, PEP and broker are absent from that application. |
| Frontend | Chat, graph and idea-matching components call localhost:8000 `/api/chat`, `/api/graph`, `/api/idea`. | All three return 404 from the current app. No implemented v2 workspace/editor path found. Configure origin and integrate authenticated APIs. |
| Data/retrieval | `src/database/database.py` uses SQLite; `vector_store.py` uses Chroma; hybrid_retriever has in-memory BM25/RRF; graph/matcher code exists. | Algorithms and fixtures may be reusable; stores, migrations, tenancy, access controls and target retrieval adapters require replacement/integration. |
| Ingestion | Existing RIT crawling, PDF distillation and Dagster assets. | Adapt to a scoped corpus, source licenses/provenance, deterministic IDs, quarantine and authorization-aware publication. “pipeline_v2” is not evidence of design P0.7 completion. |
| Models | Existing Gemini/Ollama paths. | No demonstrated target model router, global resource control, confidential locality boundary or measured Orin SLOs in this review. |
| Confidential collaboration | No target CRDT service, key lifecycle, encrypted store or revocation implementation found. | Most of the product's centerpiece remains to build. |
| Outcome loop | Existing candidate matcher; no target pursuit/outbox/writeback system found. | Build lifecycle, durable events, publication control and evaluation from the start. |
| Operations/security | No target migrations, tests/security, tools or deploy directories found. | Reproducible dependency/image pins, security fixtures, release checks, recovery drills and monitoring remain. |

Assessment: **early foundation, before a verified P0.0 gate**. Roughly 5–10% of the full design's delivery effort appears represented by the current v2 foundation and potentially reusable work. This is an engineering estimate, not a measured completion percentage; existing source-line volume is a misleading denominator. The public research prototype has more reusable substance than the v2 platform does.

## 5. Replacement delivery sequence

These are recommended scope decisions, not an assertion that they have been approved or implemented.

1. **Feasibility and contract repair (1–2 engineer-weeks).** Resolve B1–B8, define tenant/owner/guest semantics, compile representative DDL, freeze executable contracts, verify selected ARM64 packages and model settings, measure one realistic serving workload. Gate: functioning positive and negative tenant access plus a reproducible deployment recipe. Stop if the hardware workload is infeasible.
2. **Public discovery vertical slice (3–4 weeks).** Restore API/frontend integration; authentication and server-derived tenant context; public Postgres corpus, one source/import path, matching and explanations; provenance and citations; backup/restore smoke test. Reuse legacy extraction/ranking behind adapters. Gate: a researcher can find and curate a useful shortlist from real data.
3. **Secure shared workspace (4–6 weeks).** Direct proposal membership, invited guest flow, encrypted document persistence, bounded CRDT service, fenced revocation, local drafting from explicitly approved source documents, visible saved/unsaved status and export. No persistent confidential search indexes or inferred publication. Gate: two real groups co-edit, revoke a guest and recover from failure without unauthorized disclosure.
4. **Pursuit lifecycle and outcome ledger (2–3 weeks).** One opportunity feed or verified manual import; shortlist/invite/submit/outcome transitions; transactional outbox with retry and effect dedupe; consent-gated publication; loop analytics. Outcome ranking stays off by default. Gate: duplicate/reordered events produce the same final state and no private outcome reaches public search.
5. **Pilot hardening (3–5 weeks).** Independent security review, concurrency/DoS and prompt-injection cases, deployment upgrades and rollback, complete backup restore, usability/citation checks and real-user feedback. Gate: published operating limits and evidence against the acceptance matrix below.

Total reduced pilot: **13–20 focused engineer-weeks**, about **4–6 calendar months for one full-time experienced engineer** allowing modest interruptions. Two complementary engineers may reach it in **2.5–4 months**, not half the time, because contracts/security/hardware work lie on the critical path. A public-only demonstrator can be **3–5 weeks** and must not be presented as confidential v2.

Full original P0 after the pilot: budget another **12–20 engineer-weeks** for persistent confidential retrieval/deletion design, broader ingest and identity coverage, outcome evaluation, and operations. Total **25–40 engineer-weeks**, roughly **7–12 months solo**, with substantial uncertainty around crypto-erasure and ARM64 performance. These are planning ranges, not delivery commitments. Budget specialist security/cryptography review; part-time work and institutional approvals extend calendar time. P1/federation is excluded. Re-estimate after the first hardware and user-workflow gates.

## 6. Required acceptance matrix

| Boundary | Must succeed | Must fail or recover safely |
|---|---|---|
| Tenant access | Owner CRUD, intentional guest access to one proposal | BOLA, forged tenant claims, unset/empty context, pooled connection reuse, direct child-table reads |
| Sharing | Valid recipient joins, intended roles work | Expired/replayed invitation, viewer writes, role downgrade, group removal, guest retrieval of owner's unrelated corpus |
| Revocation | Owner continues editing, acknowledged revocation persists | Dropped notification, concurrent writes/broadcasts, stale socket/token, interrupted stream, restore from an older backup |
| Confidential storage | Approved collaborators decrypt current content | Wrong tenant/document AAD, wrong key, old revoked key generation, secret logs/temp files, accidental tenant-wide deletion |
| Persistence | Saved edits recover and converge | Duplicate/out-of-order updates, simultaneous client/server crash, stale client resurrection after deletion, disk full |
| Public publishing | Approved public fields appear with provenance | Mislabeled private content, secret outcome edge/score, injection-driven declassification, higher-version tombstone replay |
| Outbox | Every committed event eventually produces one logical effect | Out-of-order commits, crash after write/before receipt, duplicate retry, lease-holder death, failed run after cursor advancement |
| Models/resources | Local generation and citations within measured limits | Unsupported cache toggles, cross-worker overlap, oversized context/update/upload, cancelled job still consuming GPU, ingest transition during generation |
| Product quality | Better expert-rated shortlist and useful repeated collaboration | Ranking movement mistaken for improvement, unsupported citations, ineligible/expired opportunity, duplicate award credit |

## 7. Verification performed and limits

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/unit/contracts -q`: **6 passed**. Default pytest initially failed before running tests because an installed rerun plugin attempted a sandbox-blocked socket bind; disabling unrelated plugin autoload allowed the synchronous kernel tests to run.
- In-process FastAPI TestClient: `/healthz` **200**; POST `/api/chat` **404**; GET `/api/graph` **404**; POST `/api/idea` **404**.
- Evaluated the documented anti-resurrection predicate with current=10, revoked=11, incoming=12: **accepted**, contradicting the claimed general guarantee.
- Attempted matcher/entity-resolution tests together: **collection failed** on a local SciPy binary import. No pass claim for those tests or the legacy pipeline.
- Confirmed PostgreSQL policy/WAL/checkpoint semantics against primary documentation; did not execute target PostgreSQL 16 migrations, since they are not implemented here.
- Orin SSH access was blocked by the execution environment. No GPU latency, memory, thermal, model compatibility, TPM or disk-erasure benchmark was performed. Those remain release gates.
- Existing untracked audit/test scripts were left unchanged. No application code was changed by this review.
