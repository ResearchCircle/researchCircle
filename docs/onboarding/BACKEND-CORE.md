# Core backend setup and handoff

This slice implements named accounts, stored sessions, teams, invitations,
proposals, revision saves, attached sources and current Markdown export. The API
uses `/api/v2` and the browser's same-origin `tbr_session` HttpOnly cookie. There
is no development identity bypass. Owner/editor/viewer membership controls reads,
edits and invitations. Invitations target existing registered users and are
accepted in the app; sending email is not required.

## Fresh local PostgreSQL setup

Use the existing project environment, or create one with Python 3.12:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r services/api/requirements.txt
```

Set `TBR_DATABASE_URL` to your disposable development PostgreSQL database using
`postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`. Alternatively supply
`TBR_DB_HOST`, `TBR_DB_PORT` (default 5432), `TBR_DB_NAME`, `TBR_DB_USER` and
`TBR_DB_PASSWORD`. Keep credentials in local environment settings outside Git.
Individual settings correctly encode passwords containing URL punctuation.
There is no implicit SQLite or default-password fallback. SQLite is explicitly
injected only by isolated tests.

From the checkout root:

```sh
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m services.api.bootstrap
.venv/bin/python -m uvicorn services.api.app:app --host 127.0.0.1 --port 8000
```

Alembic records the schema revision and a repeated `upgrade head` preserves
existing records. Run migrations before API/worker startup. Web startup does not
create tables. The initial migration covers accounts, sessions, teams,
memberships, invitations, proposals, sources, proposal-source links and draft
jobs. Future schema changes require a new revision; keep the baseline unchanged.
Bootstrap is for explicit development initialization/sample import. It does not
reset the database. Do not downgrade or reset a database containing useful data.

Use the same-origin frontend/proxy for browser requests. Cookie security follows
HTTPS, or set `TBR_COOKIE_SECURE=true` when HTTPS terminates at a trusted proxy.
Cross-origin browser writes return `origin_rejected`; no wildcard credentialed
CORS configuration is provided.

## Core request examples

Register with `POST /api/v2/auth/register`:

```json
{"email":"owner@example.test","password":"a sufficiently long password","name":"Owner"}
```

The response is `{ "user": { "id", "email", "name" } }` plus the session cookie.
Create a team using `POST /teams` with `{"name":"Research"}`, then create a
proposal using `POST /proposals` with `team_id`, `title` and `content`.

A proposal starts at revision 1. Save with
`PATCH /proposals/{id}` and `{"expected_revision":1,"content":"Updated text"}`.
Success follows the database commit and returns revision 2. Reusing revision 1
returns HTTP 409 with `error.code=revision_conflict`; the newer content stays
stored. A database failure returns an error rather than claiming a save succeeded.

Create private proposal evidence with `POST /proposals/{id}/sources` using
`title`, `text` and `origin`. Text is normalized to NFC and LF line endings, then
its exact stored UTF-8 bytes are SHA-256 hashed. Public search evidence requires
an explicit `POST /proposals/{id}/sources/attach` with `source_id`. Sources from
another private proposal cannot be attached. Selecting evidence is a normal
revision save using `selected_source_ids`; every selected ID must already be
attached. Source selection returns exact ID/version/hash references.

`GET /proposals/{id}/export` downloads the current Markdown and selected source
references. `POST /teams/{id}/invitations` accepts `email` and `role` (editor or
viewer); only owners may invite. The recipient lists `GET /invitations` and calls
`POST /invitations/{id}/accept`. Viewers can read and export but cannot save,
create sources or draft.

## Evidence and remaining work

```sh
.venv/bin/python -m unittest tests.platform.test_workflow_core -v
.venv/bin/python -m unittest discover -s tests/platform -v
```

Focused tests use temporary SQLite files with real SQLAlchemy transactions and
API cookies. They verify saves after reopening, stale independent sessions,
viewer/editor permissions, invitation acceptance, private/public source
attachment, password/session storage, expired/revoked sessions, failed writes,
origin checks and fresh/repeated migration behavior. SQLite evidence does not
prove PostgreSQL behavior. The integration handoff records actual PostgreSQL,
worker, browser and local-model checks separately.

Remaining product scope includes opportunity/pursuit/outcome records, richer
membership administration and other work deferred in plan 19. This core slice
is not the complete P1 release.
