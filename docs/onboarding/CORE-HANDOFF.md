# Working core and next work

Updated 2026-11-01. Read this before anything else in onboarding: the core product
exists. Do not rebuild it from earlier starter tickets or fixtures. Where an older
plan or prompt disagrees with this file, check the code and then trust the code.

## Get the code

The ongoing shared integration branch is **`anurag/latest`**. Teammates always
start from its current remote head; `main`, `dev`, `v2` and older ticket branches
are not the current team baseline:

```sh
git clone --branch anurag/latest https://github.com/ResearchCircle/researchCircle.git
cd researchCircle
git switch -c <role>/<ticket>
```

Open ticket PRs against `anurag/latest`. Fetch before starting work; preserve local
changes and use short ticket branches rather than pushing unreviewed work directly
to the shared base. Existing ticket branches can integrate the new base through a
reviewed merge; never reset/clean or force push to discard divergence.

## Run the local product

Requirements: Python 3.12, Docker with Compose, and network access for package/image
installation. No Orin credentials, model download or paid key is required.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r services/api/requirements.txt
.venv/bin/python -m deployment.dev --provider fixture --build
```

Open `http://127.0.0.1:18088`, register a named account, and create a team/proposal.
The command builds the actual API and frontend, starts PostgreSQL, applies Alembic
migrations, seeds six **synthetic** sources, and starts the API/worker/proxy. Repeat
without `--build` when the images already match the checkout. It preserves records
and the original source snapshot. It never creates a development identity switch.

Public records are not seeded. To add them, run these bounded imports (network
required; a repeat run changes nothing):

```sh
COMPOSE="docker compose --env-file dist/core-runtime.env -f deployment/compose.yaml"
$COMPOSE exec -T api python -m services.api.import_public  # 3 Crossref papers and their listed authors
$COMPOSE exec -T api python -m services.api.import_rit     # 3 official RIT faculty profiles
```

Private settings live in ignored `dist/core-runtime.env` with mode 0600. Do not
share that file, `.env`, database dumps, model credentials or browser traces.
Register test users through the UI; no shared password/account is committed.
Use `$COMPOSE ps` to inspect this local stack. Do not remove its volumes when
records matter.

## What is implemented

- Named registration/login/logout, stored hashed sessions and Argon2 passwords.
- Teams, recipient-bound invitations and owner/editor/viewer checks. Member role
  change/removal and last-owner protection exist **in the API only**; there is no UI.
- Proposal creation, listing, revision-checked saves, reopen and visible 409
  reconciliation. Draft acceptance uses the same committed save path.
- Immutable versioned public records, bounded Crossref and RIT profile imports, and
  database-backed BM25 keyword search. Results keep source UUID/version/hash.
- Saved team shortlists with notes, explicit add/remove and role checks. Shortlisting
  never adds a team member. Unsaved notes survive navigation.
- Explicit source attachment/selection, private proposal text sources and exact
  source-version/hash capture. Cited references survive selection changes.
- Persisted draft queue/worker, four queued jobs, one queued/running job per user,
  one generation at a time, cancellation/timeout draining, interrupted-job recovery
  and safe failure states. Draft requests bind to the reviewed revision and evidence.
- Citation IDs and verbatim support quotes, Markdown download, manual team-scoped
  opportunities, submission state/history and idempotent outcomes.
- SQLAlchemy/PostgreSQL, Alembic revisions `0001`–`0004`, scoped images and
  same-origin routing that survives container replacement.

## What this does not prove

- **Search is keyword-only.** Every response is marked `degraded`; there is no
  semantic retrieval yet.
- **The corpus is tiny.** Three papers, their listed authors, three RIT profiles and
  six fictional samples. The collected data snapshot has not been imported.
- **Listed authors are unresolved.** Crossref authors are not linked to the RIT
  profiles, even if they are the same person.
- **RIT facts are not current-status claims.** Affiliation currentness and
  availability are recorded as unknown.
- **Fixture drafts are not inference.** They are labeled excerpts. Citation checks
  validate identity and quoted text, not that a claim follows from its source.
- **Real Orin-backed application acceptance remains pending.** Local Ollama
  application checks are recorded below. A private G14 deployment now exists; see
  [current deployment status](../g14-deployment-status.md). Real drafting remains pending.

## Test with a real model on your own machine

Fixture inference is the default, and the browser suite expects it. To try real drafts, you do not need Orin, the homelab or Anurag's machine. Install [Ollama](https://ollama.com/download), then:

```sh
ollama pull mistral
.venv/bin/python -m deployment.dev --provider ollama --model-id mistral:latest --build
```

Omit `--build` when the images already match the checkout. Run `--provider fixture`
again before using the browser suite. The launcher waits for the API and frontend
through the proxy before reporting `started`; a readiness timeout returns a failure
and preserves the database. Use `--ready-timeout 120` if startup needs more than
the default 60 seconds. Model availability is a separate check.

| Model | Memory used | Drafting checks | Browser drafts | Median draft time |
|---|---:|---:|---:|---:|
| `qwen3:14b` | 10 GB | 6 of 6 | 3 of 3 | 7.2 s |
| `mistral:latest` | 5.5 GB | 5 of 6 | 2 of 2 | 3.3 s |
| `qwen3:8b` | not measured | 3 of 6 | not run | 3.4 s |
| `llama3.2:3b` | not measured | 1 of 6 | not run | 2.7 s |

Use `mistral` unless you have the memory for `qwen3:14b`, which also handled the two-source case that `mistral` failed. A failed check is a safe failure: the job ends with `invalid_citations` and nothing is added to the proposal.

Measured on 2026-10-31 on an Apple M4 Max with a small synthetic set, so expect different speed on other machines and treat the scores as a rough guide. These checks prove each quote appears word for word in the source, not that the draft's claims are right, so read the drafts. Ollama results never count as Orin acceptance, and the shared demo launcher refuses this provider.

## Evidence

See [core acceptance](../qa/core-acceptance.md) and its JSON evidence. On 2026-10-31,
at commit `50c4041`, using a rebuilt fixture stack: 147 backend tests, 19 frontend
tests, the production build and the core, shortlist and tracking browser stories
passed. These are fixture and synthetic-corpus results.

Real standalone Orin completions passed earlier. The first persisted Orin job failed
citation validation, and later attempts could not start because SSH/model status
timed out. SSH timed out again on 2026-10-31. Do not claim a real-Orin browser
journey.

## Next work

| Owner | Task | Done means |
|---|---|---|
| T1 | Inventory the received data snapshot read-only, then import a reviewed subset through `import_public_records` with a separate work path. | Reimport is idempotent; 3–5 real queries return linked public evidence; proposal-only sources never enter search; corpus/index/model identity is reported honestly. |
| T1 | Add `src/platform/discovery/matching.py`: evidence-backed collaborator ranking, including author-to-profile resolution only where evidence supports it. | Results show reasons and gaps; ranking never enrolls anyone; missing identity/evidence stays unknown. |
| T1 | Add semantic retrieval behind the existing search contract once model/index compatibility is known; then the opportunity import (D-P3). | `degraded` becomes false only when semantic retrieval really ran; unknown deadlines/eligibility stay unknown. |
| T2 | Rerun `deployment.backup_smoke` and `deployment.membership_smoke` against schema `0004`, and add any missing PostgreSQL regressions. | Restore fingerprints cover public records and shortlists; role change/removal, duplicate retries and migrations lose no data. |
| T2 | Add a complete Python dependency lock and reviewed base-image digests. | A fresh image build is reproducible and the existing test commands still pass. |
| T3 | Build member role change/removal UI on the existing `PATCH`/`DELETE /teams/{id}/members/{member_id}` routes. | Owners can manage members; the last-owner error is shown clearly; a browser story covers it. |
| T3 | Extend browser coverage to busy/offline/mobile states, improve conflict/source usability, and add `docs/qa/product-demo.md`. | Existing stories stay green; failed saves preserve edits; no synthetic source appears as real evidence. |
| T1 + T2 + T3; platform integration | **R-V2-1: Restore Collaboration Hub** — idea input, evidence-backed faculty matching and shortlist/proposal continuation. | Connected browser journey with real source-linked candidates and explicit gaps; no automatic enrollment or unsupported impact scores. |
| T1 + T2 + T3; platform integration | **R-V2-2: Restore graph visualization** — reviewed graph data/route and interactive workspace surface. | Actual stable nodes/relationships render with inspectable provenance; public graph excludes proposal-only sources. |
| Platform lead + T1 + T2 + T3 | **R-V2-3: Restore previous research chat** — multi-turn grounded Q&A, conversation/source UX and reviewed v2 contracts. | Real local-model chat with supported citations, truthful failures and shared inference admission; private context stays scoped. |
| Platform lead | Restore Orin reachability, complete one persisted model-backed browser job, fix the citation failure if it recurs, and finish shared-demo model acceptance. Private G14 deployment, schema/startup, HTTPS and restart persistence passed on 2026-11-01. | Actual cited output is inspected and accepted without overwrite; deployed provider is local; sessions, restart persistence and routing work on the target. |

The three restoration tickets are pending additional v2 scope, not active features.
See [restoration details and ownership](../design/23-v2-remaining-feature-restoration.md).
Existing P1 acceptance does not prove these features have been restored.

Coordinate producer/consumer changes rather than creating a second DTO or application
root. [Plan 19](../design/19-core-implementation-plan.md) describes the core contract;
the source files are authoritative. The next migration number is `0005`.

## Real model mode (platform lead only)

```sh
.venv/bin/python -m deployment.dev --provider local \
  --base-url http://PRIVATE_ORIN_IP:8000/v1 --model-id OBSERVED_MODEL_ID
```

Those capitalized values are placeholders, not a claimed service. Do not swap or
restart a serving model merely to run a smoke. Do not silently fall back to cloud
inference. Once reachable, request a short section through the UI and record job
ID, actual model/usage, source refs, citation inspection and revision-safe acceptance.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests/platform -q
cd frontend
npm ci
node --test tests/*.test.mjs
npm run build
```

The browser suite is not in this repository, and its home (the homelab repository)
has no remote. The platform lead shares a copy as `tbr-browser-suite.tar.gz`. Unpack
it anywhere outside this checkout, then:

```sh
cd tiger_research_buddy
npm ci
npx playwright install chromium
TIGER_RESEARCH_BUDDY_REPO=/absolute/path/to/this/checkout \
  BASE_URL=http://127.0.0.1:18088 npm test
```

T3 owns changes to this suite and should agree with the platform lead where it lives
from now on, so that it does not fork.

Remaining P1/release acceptance is not erased by a green fixture demo.
