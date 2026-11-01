# V2 working product specification

Updated: 2026-10-30. **Active priority: working product first. Security hardening is a later project.**

## 1. Scope and authority

This specification and the [four-person delivery plan](18-four-person-delivery-plan.md) replace the previous security-first pilot requirements. Build a usable research collaboration platform in this repository. Do not start a new project root or require a security framework before shipping the core workflow.

The [earlier hardening design](reference/security-hardening-specification.md) is preserved for future consideration. Its key service, encryption lifecycle, revocation journals, policy engines, cross-process authorization fences, recovery protocols and security release gates are **not dependencies of this release**. The original [audit](16-v2-critical-review-and-revised-plan.md) remains useful evidence about claims we must avoid, but does not define the current milestone.

**Release workflow:** find relevant researchers and papers → create a shortlist/team → attach an opportunity or idea → create a proposal → edit and save → generate a cited draft using local inference → review/accept the suggestion → export → record submission/outcome.

The first demo uses public/synthetic papers, sample proposals and seeded test users. The first usable alpha supports named accounts and ordinary proposal membership. This release does not claim confidential-workspace certification, cryptographic erasure or immediate revocation guarantees. Do not market the early product as providing those properties.

Scope addition, 2026-11-01: the original Collaboration Hub, graph visualization and
research chat must be tracked as remaining v2 restoration work. Their retained
code is disconnected from the active workspace. See [restoration tickets](23-v2-remaining-feature-restoration.md)
for owners, integration and acceptance. Existing P1 acceptance remains distinct
from completing those additional v2 features.

## 2. Product stages

| Stage | User-visible result | Acceptance |
|---|---|---|
| P0 — connected demo | Search real public/sample corpus; see researcher matches; create and save a proposal; generate a local draft | Browser talks to real API, saves survive restart, one real Orin generation returns cited text; fixtures alone do not count |
| P1 — usable alpha | Accounts, team invitations/membership, editable proposals, opportunity tracking, sources, draft suggestions, Markdown export and outcomes | Two named users complete the workflow; suggestions never silently overwrite edits; search/citations/export/outcomes work end to end |
| P2 — collaboration polish | Concurrent editing if needed, richer export, graph exploration, retrieval and drafting improvements | Chosen features are demonstrated with real users; ordinary save/conflict handling remains reliable |
| Later — security hardening | Stronger isolation, encryption, hardened sharing/revocation, recovery and independent review | Separate scope/estimate/design, after the platform is useful |

P1 does not depend on P2. Real-time CRDT editing, DOCX layout, graph visualizations and large automated data feeds must not delay a functioning P1 workflow. Complete the basic loop before adding these enhancements.

## 3. Architecture and reuse

Use the existing Next.js frontend, FastAPI app and Python research modules. One application owns ordinary feature logic; one background worker handles slow model jobs. Avoid extra infrastructure until a working feature needs it.

- **Business records:** PostgreSQL 16 with SQLAlchemy/Alembic for accounts, teams, proposals, revisions, opportunities, pursuits, sources, jobs and outcomes. Migration setup belongs to the backend workstream, not a new infrastructure project.
- **Public retrieval:** reuse existing Chroma/BM25/RRF and matcher algorithms behind a small adapter. Chroma remains a public-data index only. Do not make a pgvector/BM25-extension migration a release prerequisite. Record index/embedding version and stable source IDs so a later store migration is possible.
- **Sources:** initially public text/PDF and synthetic/user-approved non-sensitive sample documents. Store proposal sources separately from the public corpus. A source attached to a proposal must not automatically enter public search.
- **Inference:** one local model on Orin through a server-side provider adapter. Anurag selects a working already-supported model/configuration and records it; no new model fleet or serving stack rewrite is required. Teammates use deterministic model fixtures locally.
- **Slow jobs:** a simple persisted jobs table and one worker; one generation at a time initially. No distributed coordinator, resource-regime service or generic event bus required. Detect interrupted jobs on restart and let the user retry.
- **Deployment:** same-origin browser/API routing, internal database/model services, straightforward environment configuration and a documented start command. Anurag deploys the shared demo.

Reuse is conditional on a small behavior check, not a full legacy rewrite: extraction must return usable text, retrieval stable source IDs/snippets, matcher a sensible shortlist and the provider a local completion. Remove accidental cloud fallback from the v2 drafting path. Legacy code remains behind adapters and must not invent source IDs/citations when a dependency fails.

## 4. Feature requirements

### Discovery and shortlist

Search researchers and papers by query/topic. Results show name/title, department where known, relevant evidence and a short reason for a match. Retain provenance and source links. Provide loading, empty, partial/degraded and error states. Allow adding/removing candidates from a saved shortlist attached to a team or pursuit. The PI chooses the team; ranking does not automatically add collaborators.

Start with one small reproducible public import and a useful sample corpus. Manual opportunity entry/import is sufficient. Automated OpenAlex/funding feeds and a million-chunk benchmark are later additions. Deduplicate by reliable external ID/content hash; unresolved identities stay unresolved.

### Teams and proposals

A named user can create a team and proposal, add existing users through an in-app invitation/acceptance flow, see their proposals and reopen them. Roles are owner/editor/viewer. Owner manages membership and deletes; editor edits and drafts; viewer reads. Basic account/session handling and object membership checks are ordinary backend behavior. No custom entitlement engine, RLS framework, cryptographic roles or federation abstractions are required now.

P0 may use seeded development users through an explicit development profile. A deployed P1 uses named login sessions and standard password hashing/session libraries; never ship an unrestricted development identity switcher. Membership checks live in a single application service used by routes, avoiding scattered hand-written permission logic. Passwords/secrets are not stored in plaintext or committed. Browser requests use same-origin configuration. These small foundations accompany features; advanced security work is deferred.

### Editing and saving

Ship a normal proposal editor first. Store a revision number and content; PATCH must supply expected revision. Save succeeds only after database commit. A stale update returns 409 and the UI offers reload/copy/reapply, never silently replaces somebody else's work. Autosave can debounce edits by 1–2 seconds, with visible saving/saved/error state. Preserve proposal title, sections, selected sources and team references.

Concurrent CRDT editing is P2, after editing is usable. Do not present optimistic revision conflict handling as real-time co-authoring. Source/editor/retrieval data formats should permit the editor implementation to change without replacing the proposal domain model.

### Drafting and citations

User selects sources already attached to the proposal and gives a drafting instruction/section. Backend creates a persisted draft job capturing proposal revision and exact source versions, returns a job ID and runs local inference outside the web request. UI shows queued/running/failed/succeeded, and polls initially; streaming is optional polish.

Return text with citations to actual retrieved/selected source IDs. Show snippets/links so the user can check support. Missing evidence is stated as insufficient evidence. Generated text is a suggestion: the user accepts it through the normal version-checked save path. If the proposal changed, ask the user to reconcile; never overwrite newer text automatically. Job details/results are visible only to current proposal members. Source content is input data, not an instruction to run tools or publish data.

Initial limits: 8192 model input tokens, 512 output tokens, 4 queued jobs, one queued/running job per user, 120-second worker deadline. Full queue returns a useful busy response. Timeout/cancel marks the UI truthfully; a second model request is not started while the first still runs. Restarted worker marks abandoned running jobs interrupted rather than claiming success or blindly duplicating work. Anurag can tune these limits after one realistic Orin run.

### Opportunities, export and outcomes

Opportunity records need title, source URL, deadline/timezone if known and notes. Unknown eligibility stays unknown. Pursuit states: draft → shortlisted → collaborating → submitted → won/lost/withdrawn. Unknown outcomes remain submitted. User records submission manually; the app does not submit to a funding portal.

Export current proposal to Markdown in P1; retain sections and valid source references. DOCX comes in P2 if users need it. Record outcomes transactionally and return the stored record on a retried idempotent request. Display history/status; no automated public graph writeback or outcome-weighted ranking required. A win changing a score is not proof that recommendations improve.

## 5. Small contracts that keep parallel work moving

Use `/api/v2` and JSON error shape `{error: {code, message, retryable}}`. UUID IDs, UTC timestamps, snake_case fields and explicit enum values. Teammates may implement against synthetic fixtures, but release acceptance uses the real application/database and Orin provider.

| Contract | Required fields/behavior | Owner |
|---|---|---|
| SearchResult/SearchPage | stable researcher/work/source IDs, title/name, snippet, source link, score/reason, optional next cursor, degraded flag | T1 |
| ProposalView | id, team_id, title, sections/content, revision, role, selected source versions, updated_at | T2 |
| SaveProposal | expected_revision + changed fields; returns new revision or 409 | T2 |
| SourceRef | id, version/content_hash, title, origin, proposal_id or explicit public source marker; no implicit public indexing | T1/T2 |
| DraftJob | id, proposal_id, base_revision, source refs, state, output/citations or error, timestamps | Anurag/T2 |
| ModelProvider | `generate(prompt, max_output_tokens, timeout_s)` returns text plus model ID and usage; local adapter and deterministic fixture implement the same shape | Anurag |
| Outcome | pursuit_id, outcome, recorded_at, optional award reference; request idempotency key | T2 |

The contract PR in the first two working days freezes these response fixtures and a minimal OpenAPI schema; it does not freeze a large universal kernel. Shared contract changes need the consumer's review. The existing simplified contracts package is a starting point, not a reason to implement unused abstractions.

## 6. Validation and completion

A working release demonstrates one full browser journey with real persisted records: search → shortlist → create proposal → invite another named user → edit/save/reopen → draft locally from selected sources → inspect citations → accept without overwriting a newer revision → export → record outcome.

Test normal save and stale-save conflict, missing source, failed model call, full queue, worker restart, duplicate outcome submission and a user requesting another team's proposal. These are product correctness tests. Keep tests focused on real failure modes; do not build a security research suite before this journey works.

P1 release checklist: reproducible local startup and seed; actual API/UI integration; durable saves and database backup/restore smoke; local generation on Orin; useful search results; visible errors/retries; membership enforced; no development bypass in deployed mode; no exposed secrets; one successful real-browser journey. Dedicated encrypted backup journals, formal RPO/RTO commitments, crypto-erasure proofs and external security certification are deferred.

## 7. Later security work

After P1, assess actual data sensitivity, usage and deployment needs before choosing mechanisms from the [hardening reference](reference/security-hardening-specification.md). Candidate projects: systematic access-control/RLS review, source audience/provenance rules for genuinely confidential proposals, encryption/key management, hardened websocket sharing/revocation, logging/egress controls, deletion/retention semantics and recovery drills. Estimate them separately. Retaining a `DocumentStore`, membership service and `ModelProvider` boundary now avoids coupling those later changes to every screen.

The product milestone is complete when the workflow is useful and works end to end. Later hardening does not excuse broken saves or access checks, and it is not an upstream dependency for building discovery, editing, drafting or outcomes.
