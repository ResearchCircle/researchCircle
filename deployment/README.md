# Staged v2 runtime

This configuration is prepared for A-P4 integration. It has **not** been deployed.
The present API serves only `/healthz`; T1 retrieval, T2 database/routes/worker and
T3's v2 browser client are absent. Do not interpret Compose validation or a health
response as a working product.

## Validate now

From the repository root, with Python 3.12:

```sh
.venv/bin/python -m deployment.preflight
.venv/bin/python -m deployment.preflight --integration
.venv/bin/python -m unittest discover -s tests/platform -v
```

The first command checks configuration without network access or directory writes.
The integration check currently exits 1 and reports six missing dependencies. It
checks structural prerequisites only, not correctness or release acceptance.

`RuntimeConfig.from_env()` keeps source and working paths separate, selects fixture
or local explicitly, rejects cloud endpoints, and forbids fixture inference and a
development identity switch in the shared demo profile. T2 must actually consume
these settings in its app and persisted worker; a config validator alone cannot
enforce account behavior inside an application.

## Start after integration

1. T2 supplies its reviewed dependency file, migration command,
   named-session configuration and real persisted-job worker entrypoint. T2 reviews
   the proposed `TBR_DB_*` settings and maps them into its database configuration.
   The platform lead builds the API image using that dependency file.
2. The platform lead builds a Next.js image from `frontend/package-lock.json`;
   T3 owns its v2 screens/API client. Browser
   requests use relative `/api/v2` URLs. Existing legacy localhost URLs must be
   replaced in T3's workstream before this stack is useful.
3. Copy `.env.example` to `.env` **in this directory**, and set the actual image
   names, reachable private model URL, observed model ID, worker module and a local
   database password. `.env` is ignored; the example contains no credential.
   The file uses literal `KEY=value` lines, optional enclosing quotes, and full-line
   comments; it does not evaluate shell syntax or expand variables.
4. Run the check, then explicitly start the staged local stack:

```sh
.venv/bin/python -m deployment.start --env-file deployment/.env
.venv/bin/python -m deployment.start --env-file deployment/.env --start
```

The launcher refuses to start while known integration prerequisites or required
settings are missing. It validates Compose first; no containers are started by
the default check. Shell environment values override the literal settings file.
The launcher does not run migrations, seed users, drop databases, or deploy to a
remote host. Follow T2's reviewed migration/seed commands before browser acceptance.

The proxy binds only `127.0.0.1:8080` by default. It forwards `/api/v2/` and
`/healthz` to the internal API and other paths to Next.js, preserving the API path.
Database, API, worker and frontend have no published ports. The Orin model is an
existing internal service; this stack does not start or expose a model fleet.
The configured model URL must be reachable **from containers**. A workstation's
loopback SSH tunnel is not automatically reachable at container localhost.

`postgres-data` preserves application records. `runtime-work` is shared between
API and the single worker for the model lease. Do not scale workers across hosts;
the local file lease is a single-host mechanism. Do not run standalone model
probes concurrently with the application worker. No source snapshot is mounted or
copied by this configuration. Never use `docker compose down -v` on retained data.

## Required validation before calling A-P4 complete

- Real API/model wiring with T2's persisted jobs and ordinary membership checks.
- T1's source-linked public/sample import and search results, with no proposal-only
  sources entering public search.
- T3's full browser workflow: search, team/proposal creation, invitation, save/reopen,
  selected-source generation, citation inspection, stale-revision acceptance handling,
  export and recorded outcome.
- App/worker restart and database backup/restore smoke, retaining records and marking
  abandoned running jobs interrupted. Use T2's reviewed database backup procedure.
- A real-browser run through the same-origin proxy against the actual persisted
  records and Orin; fixtures do not satisfy this gate.

The expected external suite `~/code/homelab/tiger_research_buddy/` is absent on this
machine. No browser test, database restore or product-container startup has been
claimed. Docker Compose v5.5.1 parsed the configuration with clearly synthetic
validation values. Docker Desktop was initially stopped, then started for an
isolated proxy check using already-present images:

```sh
.venv/bin/python -m deployment.proxy_smoke \
  --proxy-image nginx:1.27-alpine --upstream-image python:3.12-slim
```

This passed real HTTP checks for API path/query, health and frontend routing,
external Host/X-Forwarded-Host including the non-default port, and API/frontend
absolute redirects retaining that origin. It created a separate temporary network
and three disposable containers, then removed them. These HTTP upstreams were
fixtures, not the product API or UI. See `scripts/orin/evidence-proxy.json`.
The script does not pull images implicitly. Its tested nginx image differs from
the template's moving staging tag; pin reviewed image digests and rerun with the
chosen image before a reproducible shared deployment.

## Owned image builds

Image packaging belongs to the platform lead. T2 supplies application dependency
requirements; it does not need to build the deployment image. The current bootstrap
API dependency file installs only FastAPI and uvicorn, rather than the legacy ML
stack. It is not the complete application dependency lock and cannot prove the
future database/job service works.

```sh
.venv/bin/python -m deployment.build --print-only
.venv/bin/python -m deployment.build
.venv/bin/python -m deployment.image_smoke
```

Both `tbr-v2-api:development` and `tbr-v2-web:development` built locally. The web
image uses `npm ci` with the checked-in lock and `npm run build`; Node 22 satisfies
the locked Next.js engine requirement `>=20.9.0`. The first real production build
failed at `frontend/src/components/GraphViewer.tsx:17` because `useRef<any>()` omitted
the required initial value. The one-line integration fix supplies `null`; the
production build then passed. T3 should retain that fix when integrating its UI.

The API image was tested offline as UID 10001, imported the drafting service,
completed a fixture draft, and excluded `/app/data`, `/app/.git`, and runtime `.env`.
Its observed bootstrap package versions were FastAPI 0.162.0 and uvicorn 0.54.0.
The two images then ran in disposable containers and returned HTTP 200: `/healthz`
and the existing frontend page. Both ran as `10001:10001`. The API schema still
contained only `/healthz`, so this is packaging evidence, not a v2 workflow.
Container cleanup completed. Exact image IDs are in `scripts/orin/evidence-images.json`.

When T2 provides reviewed runtime requirements inside the allowed build context,
build the API with its actual file, for example:

```sh
.venv/bin/python -m deployment.build --component api \
  --api-requirements services/api/requirements.txt
```

That example path does not exist in this baseline; substitute T2's real file.
The build command rejects source-data, secret and outside-checkout requirements
paths. Dockerfile-specific context allowlists exclude the source snapshot and
environment files. The bootstrap package ranges and base-image tags are not a
complete reproducible release lock; use T2's agreed dependency lock and reviewed
base-image digests for the shared build. No image is pushed by these commands.
