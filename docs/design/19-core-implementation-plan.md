# Core implementation and tomorrow's handoff

User direction: implement the crucial parts of all workstreams in this checkout,
then hand off remaining work tomorrow. Make focused local commits as checks pass;
do not push or deploy to a shared environment. This explicitly expands the earlier
single-workstream scope. Preserve source data and unrelated untracked scripts.

Authority: product-first specification 17 and delivery plan 18. Core priority:
named login → sample discovery → team/proposal → revision save/reopen → attached
source selection → persisted draft job → inspect/accept suggestion → Markdown.
Invitations/membership are part of the core. Opportunities/outcomes and polished
matching can follow the connected loop; no CRDT, DOCX, cloud fallback or new fleet.

## Work split in this checkout

- Backend: database/models/setup, accounts/sessions, teams/invitations, proposals,
  sources/export, their API routes and tests. Own dependency file and app factory.
- Frontend: replace the legacy landing workflow with an accessible same-origin
  client for the contract below, focused component checks and production build.
- Discovery: dependency-light seeded sample retrieval and source-linked results;
  inspect reviewed legacy logic before reuse. No source snapshot mutation.
- Integration: persisted draft jobs/controller adapter, worker process, discovery
  route composition, PostgreSQL/runtime wiring, real HTTP/browser acceptance,
  fixture/schema review and focused commits after producer/consumer checks.

Parallel implementers must stay within assigned files and do not commit; the
integrator stages/commits reviewed task files so staging never races.

## Contract for this core slice

All paths below are under `/api/v2`. JSON errors are
`{error: {code, message, retryable}}`. UUID IDs, snake_case and UTC timestamps.
API calls use an HttpOnly same-origin session cookie; no dev identity switch.

| Method/path | Request | Response |
|---|---|---|
| POST `/auth/register` | email, password, name | `{user: {id,email,name}}`, session cookie |
| POST `/auth/login` | email, password | same |
| GET `/auth/me` | — | same; 401 if signed out |
| POST `/auth/logout` | — | 204 |
| GET/POST `/teams` | POST name | list `{items:[{id,name,role}]}` / one team |
| GET `/teams/{id}` | — | team with members |
| POST `/teams/{id}/invitations` | email, role: editor/viewer | invitation |
| GET `/invitations` | — | `{items:[{id,team_id,team_name,role}]}` |
| POST `/invitations/{id}/accept` | — | `{team_id}` |
| GET/POST `/proposals` | POST team_id,title,content | list `{items:[...]}` / ProposalView |
| GET/PATCH `/proposals/{id}` | PATCH expected_revision + content/title/selected_source_ids | ProposalView or 409 |
| GET/POST `/proposals/{id}/sources` | POST title,text,origin | `{items:[SourceSnapshot]}` / SourceSnapshot |
| POST `/proposals/{id}/sources/attach` | source_id | SourceSnapshot |
| GET `/proposals/{id}/export` | — | current Markdown download |
| GET `/search?q=...` | — | `{items:[SearchResult], degraded, next_cursor:null}` |
| POST `/proposals/{id}/jobs` | section,instruction,source_ids | DraftJob; 202 |
| GET `/proposals/{id}/jobs` | — | `{items:[DraftJob]}` |
| GET `/jobs/{id}` | — | DraftJob |
| POST `/jobs/{id}/cancel` | — | terminal DraftJob; inference may still drain |

ProposalView: id,team_id,title,content,revision,role,selected_sources (SourceRef
objects with id/version/content_hash),updated_at. SourceSnapshot is the existing
drafting dataclass: id,version,content_hash,title,origin,text,proposal_id,is_public.
`content_hash` is SHA-256 of exact UTF-8 normalized text. Public source attachment
still requires an explicit ProposalSource row. Proposal-only sources stay private.

SearchResult: id,source_id,version,content_hash,title,snippet,origin,score,reason,
kind (paper/researcher),evidence_kind (public/synthetic),text. Full sample text is
only public/synthetic. IDs remain stable across imports. A synthetic researcher
must be clearly labeled and must not impersonate a real faculty identity.

DraftJob: id,proposal_id,base_revision,source_refs,state,output,error,created_at,
started_at,finished_at. Output is the existing DraftResult serialized as JSON.
Cancellation uses failed + error.code=cancelled; interrupted jobs use
failed + error.code=interrupted. No automatic acceptance/save or retry.

## Backend integration seam

`src.platform.database.models` provides Base, User, Team, Membership, Invitation,
Proposal, Source, ProposalSource. Source fields match SourceSnapshot. Proposal has
id/team_id/title/content/revision/selected_source_ids/updated_at. ProposalSource has
proposal_id/source_id composite identity. All IDs are canonical UUID strings.

`Database.session_factory()` returns a SQLAlchemy Session. The app exposes it at
`app.state.db`. `services.api.dependencies` provides `get_session`, `current_user`
and `require_proposal(session,user,proposal_id,edit=False)` returning a proposal
after ordinary membership checks (edit allows owner/editor). Route handlers share
the same Session dependency. `create_app(database_url=None)` is the app factory;
the module exports app. Root composition adds jobs/search routers afterward.
Database supports PostgreSQL via psycopg; isolated SQLite is for focused tests.

## Gates

- [ ] Preserve and commit existing provider/drafting/runtime checkpoints.
- [ ] Backend normal/stale save, membership, invitations, session and source tests.
- [ ] Search/import reproducibility and no private source indexing checks.
- [ ] Durable job queue/admission, conditional finish/cancel and restart checks.
- [ ] Browser exercises real API, persisted saves and checked draft acceptance.
- [ ] PostgreSQL restart and backup/restore smoke on disposable development data.
- [ ] One actual Orin draft through the persisted application job path.
- [ ] Build/runtime check and concise remaining-work handoff with small commits.

Fixtures support independent implementation; release evidence distinguishes them
from actual PostgreSQL, browser and Orin execution. Do not mark the full original
milestone complete if opportunities/outcomes or another required gate is deferred.
