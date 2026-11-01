# G14 deployment status

Deployed and checked 2026-11-01 at **https://g14.taild3eaea.ts.net**. Access requires
an allowed Tailscale connection and a named application account. Register through
the UI; there is no shared default account/password. No public Funnel was enabled.

## What is running

Docker 29.1.3, Compose 2.40.3, PostgreSQL, API, worker, frontend and nginx are running
on G14 AMD64. The application profile is `demo`, provider `local`, with development
identity disabled. App revision: `5b10581d4103`. Host setup: `01e24b4`.

Everything belonging to this deployment is under `/home/anurag/researchCircle`:

- `releases/5b10581d4103/`: verified source/build/runtime files.
- `artifacts/5b10581d4103/`: image/source archives, revision and checksums.
- `config/runtime.env`: private settings, mode 0600; do not print or share it.
- `state/tbr-researchcircle/postgres/` and `work/`: persistent application data.
- `runtime/docker/` and `runtime/containerd/`: daemon-managed images/container data.
- `setup/`: interactive installer and guarded runtime-storage configuration helper.
- `evidence/` and `logs/`: deployment checks and operational output.
- `inputs/`: empty source input area; the collected snapshot was not transferred.

OS packages and service pointer/configuration files remain in their standard
system locations. Existing configuration is preserved with private backups;
nonempty old runtime data or conflicting storage roots require manual review.
No existing source data, databases or volumes were deleted or relocated.

Only nginx publishes an application port: `127.0.0.1:18088`. Tailscale Serve
terminates private HTTPS and preserves Host. Nginx overwrites the scheme using
`TBR_PUBLIC_SCHEME=https`. API/database ports are unpublished. The application's
private Compose network contains trusted application containers only.

## Verified behavior

See [actual evidence](../deployment/evidence-g14-deployment.json):

- TLS certificate validation, frontend HTML and actual API health through Serve.
- Same-origin browser requests accepted; foreign origins rejected; client scheme
  headers cannot override the configured public HTTPS scheme.
- Registration/login issue Secure, HttpOnly, SameSite session cookies.
- Fresh database migration/schema gate reached `0004_team_shortlist` before worker
  startup; actual schema remained valid after restarts.
- Proposal save committed revision 2; a stale save returned 409.
- PostgreSQL/API/worker restart retained the session, saved revision and text.
  A fresh login also reopened the saved proposal; anonymous access was rejected.
- Real browser registration, team/proposal creation, edit/save, restart/reload and
  reopen passed. The actual 93-byte Markdown download contained saved text.
- Local backend suite: 189 passed, three opt-in checks skipped. Three bind-storage
  and HTTPS checks passed separately; two default-volume HTTPS checks also passed.
  Seven runtime-configuration tests cover preservation, foreign roots and symlinks.

All synthetic acceptance accounts/teams/proposals are retained and explicitly named.
No public corpus was seeded/imported and no inference request was made by these
checks. Startup and save acceptance do not establish real drafting quality.

## Operations

From G14, with the installed Docker group access:

```sh
cd ~/researchCircle/releases/5b10581d4103
python3 -m deployment.start --env-file ../../config/runtime.env
python3 -m deployment.start --env-file ../../config/runtime.env --start
docker compose --env-file ../../config/runtime.env -f deployment/compose.yaml ps
```

Use the gated launcher for startup/migrations. Before first worker startup its new
work bind directory was assigned UID/GID 10001 using the reviewed API image. Keep
that ownership if restoring into a new work directory; never point it at sources.
Stop only this application with Compose `stop` when needed. Retain settings and
all persistent storage; do not use database drops, `down -v`, resets or pruning as
setup/troubleshooting shortcuts.

## Remaining acceptance

Orin still reports offline. T1's reviewed excerpts/expected facts/forbidden claims
are not present in fetched branches. The configured local endpoint does not fall
back to a fixture or cloud model. Real drafting quality, usage/latency and the
persisted model-backed citation/accept/export browser journey remain pending both
inputs. T1 owns corpus/retrieval/matching; T2 owns remaining backup/restore and
lock/digest review; T3 owns member UI and broader browser UX coverage.

Git changes remain local; deployment used direct checksum-verified source/image
transfer. No push, PR or merge was performed.
