# Platform integration update

Review branch: `anurag/a-p4-shared-host`.
Shared review baseline: `b179a7e` (`anurag/a-p1-provider` when last fetched).

## Problem and resulting behavior

A fresh shared installation could start API/worker processes before the database
was migrated, and process health could pass while account/job tables were absent.
The shared launcher now waits for PostgreSQL health, applies the existing Alembic
migrations, checks the actual schema and then starts application services. A failed
gate blocks new application startup. Configuration-only execution does not migrate
or start services. No schema definitions or numbered migrations were changed.

The earlier startup fix waits for the real API health response and web HTML through
the proxy. It bounds slowly streamed responses and makes development Compose and
readiness use the same effective port. Citation failures retain `invalid_citations`
and report fixed, specific reasons without retaining raw failed model output.

## Included evidence

| Evidence | What it establishes | Scope limit |
|---|---|---|
| [Fresh installation](../deployment/evidence-fresh-start.json) | Fresh PostgreSQL volume, schema `0004_team_shortlist`, registration, revision-checked save, restart, retained named session, fresh-login reopen and retained volumes. | Isolated local development fixture profile; not target-host or model acceptance. |
| [Scripted application scenarios](../scripts/orin/evidence-simulated-application.json) | Two-source acceptance/export, insufficient evidence, invalid quotes, truncation, concurrent-save protection and cancellation/draining against PostgreSQL. | Authored responses through an in-process API client. |
| [Scripted browser checks](../scripts/orin/evidence-scripted-browser.json) | Citation display, append/save/export, failed/cancelled states and disabled stale acceptance in the real UI. | Synthetic simulation database and fixture model responses. |

The updated platform suite ran 183 tests: **181 passed**, with the two opt-in
proxy tests skipped in the default run. Both proxy tests passed separately on
native ARM64 and locally emulated AMD64 application images. The fresh-install rehearsal also
verified that the schema-gate file in the tested image matches the checkout;
runtime image IDs are recorded in its evidence.

## Shared-host preparation

The proxy previously lost the external HTTPS scheme, rejecting valid browser
writes and failing to set secure cookies. `TBR_PUBLIC_SCHEME` now explicitly
selects HTTP or HTTPS at the trusted front door; nginx renders its config and
overwrites client scheme headers. The unpublished API trusts forwarded headers
inside the single trusted application network. Do not publish its port or attach
untrusted peers. Host preservation remains an actual target-ingress check.

Separate AMD64 application images built successfully and passed the controlled
TLS checks under local emulation, including login/cookies, proposal saves,
restart persistence and rejected foreign/wrong-scheme origins. Native ARM64
checks and the HTTP replacement/spoof smoke also passed. Builds support an
explicit `--platform` while preserving the native default and existing image tags.

[Preparation procedure](shared-host-preparation.md) and
[local evidence](../deployment/evidence-shared-preparation.json) document the
transfer path and limits. A follow-up connected to G14 over Tailscale SSH:
x86-64, 821.9 GB free, Ubuntu 26.04.1 LTS, no Docker/Compose or configured Serve
ingress. The LAN path still timed out; noninteractive sudo was unavailable.
The AMD64 image architecture matches this host, but runtime installation and
actual front-door/persistence checks remain pending. No remote service, package
or ingress changes were made. Orin was reported offline by Tailscale.

## Data preservation

No parsed/downloaded source files, existing databases or volumes were deleted,
cleared or reindexed. The snapshot check found **15,986 preexisting files**, zero
removed/changed files and zero additions. SHA-256 comparisons covered 15,871 files;
the remaining 115 larger/linked files were compared through size/mtime metadata.
The content-hash limit and counts are recorded with the evidence.

Rehearsals use new `tbr-fresh-*` projects, private settings under ignored
`dist/rehearsals/`, and separate named volumes. Output paths inside or above source
snapshots, including their transitive symlink targets, are rejected. Link cycles
are handled without following them indefinitely. Cleanup stops only the new project's services and retains
its volumes/settings. Existing application projects are not stopped or repurposed.
Build contexts exclude collected data, repository metadata and private settings.

## Setup and verification

```sh
.venv/bin/python -m unittest discover -s tests/platform -q
.venv/bin/python -m deployment.build
.venv/bin/python -m deployment.rehearse
```

The recorded rehearsal used available `postgres:16.6-alpine` and
`nginx:1.27-alpine` images via `--db-image` and `--proxy-image`. This does not replace
T2's pending dependency lock/base-image digest review.

For an authorized shared target, fill the private runtime settings from
`deployment/.env.example`, then validate before starting:

```sh
.venv/bin/python -m deployment.start --env-file /path/to/private-runtime.env
.venv/bin/python -m deployment.start --env-file /path/to/private-runtime.env --start
```

The shared launcher still requires the local provider and named sessions; fixture
and Ollama modes remain development-only. A successful startup is separate from
real model, browser and target-host release acceptance.

## Review focus and remaining gates

- Confirm healthy-DB → migration/schema gate → application/worker ordering and
  failure behavior in `deployment/start.py` and `deployment/schema.py`.
- Confirm rehearsal project isolation, source-path exclusion and retained-volume
  behavior in `deployment/rehearse.py`.
- Review the existing citation diagnostics and scripted evidence as platform
  changes; they introduce no new API DTO or frontend requirement.
- [Drafting acceptance criteria](design/22-drafting-acceptance-criteria.md) are
  defined. T1 confirmed the reviewed excerpts are not ready. Expected facts,
  forbidden claims and exact support must be populated/reviewed before scoring.
- Real Orin generation quality/latency and a successful persisted browser job
  remain pending. The earlier failed attempt remains in the evidence record.
- Shared-target selection/authorization and target-host persistence/routing checks
  remain pending. Nothing in this update has been pushed or deployed to a shared
  environment.

Retrieval/matching remain with T1; database schema, routes and dependency locks
remain with T2; member UI and browser-suite development remain with T3. This
update changes platform-owned deployment/drafting code, its tests and evidence.

Inspect the cumulative update with:

```sh
git log --oneline b179a7e..anurag/a-p4-shared-host
git diff --stat b179a7e..anurag/a-p4-shared-host
```
