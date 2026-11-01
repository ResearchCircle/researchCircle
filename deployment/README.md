# Local runtime and deployment handoff

The connected local core now exists: named sessions, teams/proposals, sources,
persisted jobs, editor/citations, Markdown export and manual opportunity/outcome
tracking. It has been checked against PostgreSQL and in a real browser. Current
ownership and remaining acceptance are in [CORE-HANDOFF.md](../docs/onboarding/CORE-HANDOFF.md).
This is not a shared deployment or proof of real-corpus/model quality.

## Fresh local start

Use Python 3.12 and Docker with Compose, from the checkout root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r services/api/requirements.txt
.venv/bin/python -m deployment.dev --provider fixture --build
```

Open `http://127.0.0.1:18088` and register through the UI. This builds the actual
images using the checked-in frontend npm lock and minimal API requirements,
starts PostgreSQL, upgrades Alembic, seeds six labeled synthetic sources, and
starts the API, worker, frontend and proxy. Repeat without `--build` when images
match the checkout. Existing records and the source snapshot are preserved.
There is no shared default password or development identity switch.

The launcher reports `started` only after the API health response and frontend
HTML respond through the local proxy. It waits up to 60 seconds; use
`--ready-timeout 120` for slower startup (maximum 300 seconds). A readiness timeout
returns a failure and preserves the settings, containers and database for inspection.
This checks HTTP readiness, not model availability or release acceptance.

Private settings are in ignored `dist/core-runtime.env`, mode 0600. They are reused,
not regenerated on every run. Do not share settings or database dumps. Source and
work paths must be separate; no source snapshot is mounted or copied into images.
Fixture inference returns labeled excerpts and needs no Orin credentials or paid key.

The proxy publishes only a loopback port. API, worker, frontend and database remain
internal. API paths/query strings and external Host/port are preserved. Docker
service names are re-resolved after container replacement. Use this same-origin
proxy for the browser; cross-origin writes are rejected.

```sh
docker compose --env-file dist/core-runtime.env -f deployment/compose.yaml ps
.venv/bin/python -m deployment.preflight --integration
```

Preflight checks structure/configuration, not release acceptance. Stop services
without deleting volumes. Do not remove retained data as a setup shortcut. Web
startup does not create tables; new schema changes require new migrations.

## Ollama on your own machine

For real-model testing without Orin, follow [CORE-HANDOFF.md](../docs/onboarding/CORE-HANDOFF.md). `--provider ollama` runs only in the development profile; the shared demo launcher refuses it. Token counts are estimates, and idle means reachable, because Ollama exposes neither.

## Local model mode

Only the platform lead needs the existing Orin service. Observe the served model
and confirm reachability/idleness first. Do not restart/swap it merely for a smoke.

```sh
.venv/bin/python -m deployment.dev --provider local --base-url http://PRIVATE_ORIN_IP:8000/v1 --model-id OBSERVED_MODEL_ID
```

Capitalized values are placeholders, not a claimed endpoint. The model URL must be
reachable from containers; host loopback tunnels are not automatically container
localhost. There is no cloud fallback. The served chat tokenizer enforces 8192 input
tokens and generation requests at most 512 output tokens. Unavailable model status
fails waiting work truthfully; busy/draining inference never admits a second call.

One worker uses the shared runtime-work volume for its single-host model lease.
Do not scale workers across hosts. UI cancellation/timeout does not prove inference
ended. Shutdown waits for the actual call and sanitizes failed persistence writes.
Abandoned running jobs are interrupted, not silently redelivered.

An `invalid_citations` job now identifies the failed check in its fixed error
message: response JSON/fields, selected source, support quote, duplicate reference
or inline marker. These diagnostics contain no model output or source text. The
checks still validate identity and verbatim quotes; claim support requires review.

Actual Orin-backed application acceptance remains pending. Earlier standalone
completions passed, but one persisted application run failed citation validation;
later SSH/status probes timed out. A fixture browser pass is not Orin acceptance.

## Verification and retained data

Authored model responses can exercise the application while Orin is offline:

```sh
.venv/bin/python -m scripts.orin.simulated_application
```

This runs the real API routes and persisted worker against temporary SQLite, with
two named users and synthetic sources. It checks two-source acceptance/export,
insufficient evidence, invalid quotes, truncated output, a concurrent save that
must reject stale acceptance, and cancellation that must discard late output and
hold follow-up work until the first response drains. Responses are scripted; no
model service is called.

To run those same cases on PostgreSQL, first start the local fixture stack, then:

```sh
docker compose -p tbr-core --env-file dist/core-runtime.env -f deployment/compose.yaml \
  run --rm -T --no-deps --volume "$PWD/scripts/orin:/app/scripts/orin:ro" \
  api python -m scripts.orin.simulated_application --postgres
```

The PostgreSQL run creates, migrates and retains a new `tbr_simulation_*` database;
scenario records never enter the existing workspace. The command refuses a shared
demo profile. Its JSON summary contains no passwords or full source text. These
checks cover API/worker behavior through an in-process client, not browser or Orin
acceptance, model quality, measured token usage or inference latency.

```sh
.venv/bin/python -m unittest discover -s tests/platform -q
.venv/bin/python -m deployment.build --print-only
.venv/bin/python -m deployment.backup_smoke
```

Pause the local worker and finish other writes before backup comparison. The backup
smoke is restricted to tbr-core: it writes an ignored private dump, restores into a
new database, compares all public-table row fingerprints, and retains original,
restore and backup. It never drops the original database.

The disposable proxy replacement/redirect check uses already-present images:

```sh
.venv/bin/python -m deployment.proxy_smoke --proxy-image nginx:1.27-alpine --upstream-image python:3.12-slim
```

It checks actual HTTP routing and replacement DNS using fixtures, not the product
UI. Real browser suites live in `~/code/homelab/tiger_research_buddy/`; see
[core acceptance](../docs/qa/core-acceptance.md) for actual evidence.

Both application images run as UID 10001. Scoped build contexts exclude source
snapshots, repository metadata and environment files. Requirements currently use
tested version ranges; a complete dependency lock and reviewed base-image digests
remain backend/deployment follow-up. Build commands do not push images.

`deployment.start --env-file deployment/.env --start` remains the explicit shared
demo launcher. It requires real named-session/local-model settings, does not run
migrations, and does not prove release acceptance. Shared deployment still needs
the actual Orin-backed journey, target-host persistence checks and authorization.
