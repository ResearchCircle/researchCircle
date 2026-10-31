# V2 product-first four-person delivery plan

Updated: 2026-10-30. **Working product first; advanced security later.** Supersedes the earlier 12–16-week security-first pilot schedule and A0–A4/D0–D4/W0–W4/F0–F4 ticket assignments.

**Goal:** a usable discovery → team → proposal → local draft → export → outcome platform.

**Spec:** [working product specification](17-v2-corrected-specification.md). This is a delivery plan for product functionality, not a security-platform build. The [old security-first plan](reference/security-first-delivery-plan.md) is deferred reference only.

## 1. Work split

| Person | Primary responsibility | Concrete result |
|---|---|---|
| **Anurag** | Orin inference, model integration, drafting/RAG quality, shared deployment and end-to-end integration | Local drafts from real selected sources, usable latency, running shared app |
| **Teammate 1** | Data ingestion, researcher/paper search, retrieval, shortlist ranking/explanations, opportunity data | Useful searchable corpus and evidence-backed collaborator matches |
| **Teammate 2** | Application backend/database: accounts, teams, invitations, proposals/revisions, sources, pursuits/outcomes, draft job persistence and export | Complete persisted workflow with normal account/membership behavior |
| **Teammate 3** | Frontend/user journey: search, shortlist, teams, editor, job/results/citations, export/outcomes; component and browser tests | A user can complete the entire workflow in the browser |

Anurag handles the work that actually requires Orin. Ordinary login/membership belongs to T2; there is no dependency on Anurag building an authorization framework first. T1/T2/T3 work locally using synthetic data and the deterministic provider supplied by Anurag. Real hardware verification is a release integration step, not a blocker for every PR.

Security hardening has **no active work package** in the first product milestone. No key service, encrypted CRDT log, revocation journal, policy engine, formal crypto-erasure, complex RLS setup or security certification is required to finish these tickets.

## 2. File ownership and working agreements

| Owner | Main paths and reused modules |
|---|---|
| Anurag | `src/platform/models/`, `src/platform/drafting/`, `scripts/orin/`, deployment configuration; adapt `src/generation/synthesizer.py` and local client code where useful |
| T1 | `src/platform/discovery/`, `src/platform/ingestion/`; reuse `src/retrieval/hybrid_retriever.py`, `src/collaboration/matcher.py`, public vector-store/crawler code |
| T2 | `src/platform/workflow/`, `src/platform/database/`, `services/api/routes/`, `migrations/`, `services/worker/`; API app composition |
| T3 | `frontend/src/`, `frontend/tests/`, external homelab browser suite, `docs/qa/` |
| Shared | `packages/contracts/src/tigerexchange_contracts/` (Anurag integrates DTOs with T2), `pyproject.toml`/app dependency locks (T2), frontend package/lock (T3), deployment runtime config (Anurag) |

Use `src/platform` inside the existing distribution to avoid packaging a dozen new libraries before features work. It imports reviewed legacy algorithms through adapters. Each module owns clear responsibilities; feature modules do not import frontend or process entry points. Exact implementation filenames below are planned, not a claim they already exist.

T2 coordinates numbered migrations and app/router composition. Anurag owns Orin credentials and shared deployment; nobody else needs SSH. Shared DTO changes are reviewed by the producing and consuming owners. Short feature branches, small reviewed PRs and integration at least twice a week. No rewrite of somebody else's migration after merge. Never commit secrets or real private proposal fixtures.

## 3. First two days: unblock everyone

- **Anurag:** publish ModelProvider interface and fixture completion, confirm one real Orin request, create shared run/environment instructions. Choose one model that works; do not spend the sprint switching model fleets.
- **T1:** build a small public/sample corpus from current artifacts; return one real SearchPage and researcher match fixture; identify extraction/index code worth reusing.
- **T2:** bring up Postgres/migrations/API, define team/proposal/revision/source/job/outcome schemas, provide draft OpenAPI/JSON fixtures and seeded test users.
- **T3:** configure a same-origin API client, wire search/results against the shared fixture, sketch the complete journey with loading/empty/error states.

Freeze the small shared contracts from spec §5 together within two working days. Do not wait for all database tables or model optimization to merge the first connected screen. Seeded identity is an explicit P0 development mode; named sessions replace it before a shared P1 alpha.

## 4. Work packages

For each ticket: add the focused behavioral check, implement against the shared contract, run the relevant tests, open a reviewed PR and include a short reproducible demo. A fixture-only feature is ready for integration, not complete. Browser E2E lives in `~/code/homelab/tiger_research_buddy/` following `homelab/AGENTS.md`, with `TIGER_RESEARCH_BUDDY_REPO` pointing here; component/API tests stay in this repo.

| Ticket / owner | Deliverable and planned files | Dependencies | Acceptance / reviewer |
|---|---|---|---|
| **A-P1 / Anurag** | `src/platform/models/provider.py`, `fixtures.py`, `scripts/orin/smoke.py`: local provider, deterministic fixture, reproducible model config | none | Same call shape works locally and on Orin; unavailable provider returns a real error. T2 reviews DTOs. |
| **A-P2 / Anurag** | `src/platform/drafting/service.py`, `citations.py`: assemble selected-source prompt, return draft with source IDs, model/context limits | A-P1, D-P1 source refs | Known source produces usable cited output; missing evidence is identified; citations reference supplied sources. T1 reviews evidence. |
| **A-P3 / Anurag** | `services/worker/generate.py` with T2: consume persisted jobs, serialize inference, timeout/retry behavior | A-P2, B-P3 | Browser job reaches success/error; restart marks interrupted jobs; old running inference is finished/aborted before next admission. T2 reviews persistence integration. |
| **A-P4 / Anurag** | Shared demo deploy/start scripts, environment template, integration fixes and measured drafting report | U-P3 + B-P4 + D-P2 | Real Orin-backed complete browser workflow; restart preserves records; no fake provider in deployed demo. T3 reviews journey. |
| **D-P1 / T1** | `src/platform/ingestion/import_public.py`, `discovery/search.py`: corpus import, stable IDs/provenance, existing retrieval adapter | shared search/source DTOs | Reimport does not duplicate; real queries return source-linked results; source/embedding versions recorded. Anurag reviews adapter. |
| **D-P2 / T1** | `discovery/matching.py`, `shortlists.py`: researcher matches with evidence/reasons and coverage gaps | D-P1 | Representative topics produce useful candidates; user can curate; no invented researcher identity. T3 reviews usefulness. |
| **D-P3 / T1** | `ingestion/opportunities.py`, sample opportunity data and query/filter contract | B-P1 schema agreement | Manual import works, deadlines/unknown eligibility displayed accurately; sources linked. T2 reviews DTO/storage. |
| **D-P4 / T1** | Search/drafting gold examples and quality report; improve bad matches/citation retrieval | D-P2, A-P2 | Reproducible public queries and expert-reviewed examples; distinguish missing data from model failure. Anurag reviews quality. |
| **B-P1 / T2** | `src/platform/database/`, migrations, `workflow/accounts.py`, `teams.py`, proposal skeleton/routes | none; agree DTOs early | Fresh local setup, named session login, team/proposal create/list/reopen, ordinary object membership checks. T3 reviews API usability. |
| **B-P2 / T2** | `workflow/proposals.py`, `sources.py`, `invitations.py`: revision saves, selected sources, in-app invite accept | B-P1 | Saves survive restart; stale revision 409; owner/editor/viewer behavior; invited second user can open proposal; unrelated user cannot. T3 reviews editor contract. |
| **B-P3 / T2** | `workflow/jobs.py`, jobs table/status/result routes; source upload/reference validation | B-P2, A-P1 DTOs | Persist job/source/base revision, bound queue, clear failure/retry, result limited to members; fixture works before Orin adapter. Anurag reviews worker handoff. |
| **B-P4 / T2** | `workflow/pursuits.py`, `outcomes.py`, `export.py`: opportunity link, status transitions, Markdown export | B-P2, D-P3 contract | Full record history; duplicate outcome request returns prior result; export preserves current text/citations. T1 reviews data semantics. |
| **U-P1 / T3** | `frontend/src/lib/api.ts`, discovery/shortlist/opportunity screens | shared fixtures then D-P1/D-P2 APIs | Real results and clear loading/empty/error states; curated shortlist passed to proposal flow. T1 reviews. |
| **U-P2 / T3** | Named login, team/proposal list, membership screens and ordinary editor | B-P1/B-P2 fixtures then APIs | Create/edit/save/reopen; saving/error/conflict states truthful; invitation flow works for second user. T2 reviews. |
| **U-P3 / T3** | Draft instruction/source selection, queued/running/result UI, citations, accept suggestion | B-P3 + A-P2 fixture then A-P3 | Generate, inspect and accept draft; no silent overwrite after concurrent edit; failed/busy jobs recover visibly. Anurag reviews. |
| **U-P4 / T3** | Export/outcome UI, homelab E2E and `docs/qa/product-demo.md` | U-P1–U-P3, B-P4 | One real browser journey covers the whole release with database persistence and real Orin output. T2 + Anurag review. |

Focused backend tests belong in `tests/platform/`; frontend component tests in `frontend/tests/`. Use real local database for persistence/revision/membership tests. No requirement to stand up a separate adversarial security test platform before finishing these tickets.

## 5. API handoffs

All responses use the shared DTOs; JSON field names come from the contract/OpenAPI PR, not independent frontend guesses. Browser base URL is `/api/v2`. IDs never stand in for membership checks.

| Surface | Backend producer | Frontend consumer | Expected operations |
|---|---|---|---|
| Search/researchers/shortlists | T1 algorithms, T2 route composition | T3 U-P1 | query, result details, curated candidates |
| Accounts/teams/proposals | T2 | T3 U-P2 | login/session, team/proposal create/list/read, revision save, invite/accept |
| Proposal sources | T2 storage + T1 public source IDs | T3 U-P3 | attach/list selected sources, no automatic public indexing |
| Draft jobs | T2 records/routes + Anurag worker/provider | T3 U-P3 | submit, poll status, inspect result/citations, accept by normal revision save |
| Opportunities/pursuits/outcomes | T1 import + T2 domain/routes | T3 U-P1/U-P4 | manual import/link, update status, record idempotent outcome |
| Markdown export | T2 | T3 U-P4 | download current proposal with references |

The first contract PR records endpoint names and example success/error bodies. Poll job status initially; streaming and CRDT protocols are not prerequisites. Do not add a second API or let the browser call the model server directly.

## 6. Schedule

Availability is unknown. These are full-time planning ranges for four suitably experienced contributors, not commitments. Review completed slices and Orin evidence at the end of week 1, then re-estimate.

| Window | Anurag | T1 | T2 | T3 | Demonstration |
|---|---|---|---|---|---|
| Week 1 | A-P1 model/local fixture | D-P1 corpus/search | B-P1 database/core API | U-P1 connected search, proposal shell | Search real corpus; create and reopen a saved sample proposal |
| Week 2 | A-P2 source-grounded drafting | D-P2 matching | B-P2 revisions/invites | U-P2 editor/team flow | Curate candidates; two users open proposal; save/conflict behavior works |
| Weeks 3–4 | A-P3 jobs/inference + integration | D-P3 opportunities + retrieval fixes | B-P3 jobs, B-P4 lifecycle/export | U-P3 drafting + U-P4 outcome/export | Complete real browser loop including Orin generation |
| Weeks 5–6 | A-P4 deployment/quality fixes | D-P4 evidence/quality | integration defects and persistence checks | E2E/usability/polish | Usable P1 alpha and repeated walkthroughs |
| Weeks 7–8 if needed | Orin/performance contingency | data quality fixes | collaboration enhancements if baseline stable | polish or P2 concurrent-editor work | P1 stabilization; P2 features only after core loop works |

Target **2–3 weeks for a connected product demo**, **4–6 weeks for the usable alpha**, with **6–8 weeks as a contingency range** if data, dependencies or Orin serving need repair. This is a narrower milestone than the old secure pilot; the shorter date does not mean advanced security was completed faster.

Budget approximately **14–21 focused engineer-weeks** across the four people: Anurag 3–5, T1 3–5, T2 4–6, T3 4–5, including local integration and ordinary feature tests. Four-person coordination and Anurag's final hardware run mean calendar time is not total effort divided mechanically by four. Part-time contributors extend these ranges.

## 7. Merge and deployment gates

Merge working slices frequently. Each PR includes test results, sample input/output, consumer handoff and known limitations. Reserve two shared integration sessions per week. Anurag keeps a simple Orin test queue of commit/command/fixture/expected result so teammates can request validation without SSH.

P0 demo acceptance: real search + real saves + one local draft in the browser. P1 alpha acceptance: complete user journey, named account/membership behavior, honest save/conflict handling, background job/restart errors, Markdown export, idempotent outcome record, local deployment/start instructions and one database backup/restore smoke test.

Advanced security mechanisms are not merge gates for these tickets. Later security review gets separate tickets once product behavior stabilizes. Existing access/permission failures and data-loss bugs remain normal product bugs to fix, not reasons to invent a larger infrastructure project.

## 8. After the platform works

Choose the next work from user feedback: real-time collaboration if edit conflicts are common; DOCX if Markdown export is insufficient; richer retrieval/graph views if matches are weak; automatic funding feeds if manual import hurts usage. Then schedule the security-hardening project against the actual data/deployment model, using the archived reference as input rather than a mandatory checklist of services to build.

No teammate is assigned security hardening during the initial product milestone. Anurag stays focused on making local inference and the integrated platform useful.
