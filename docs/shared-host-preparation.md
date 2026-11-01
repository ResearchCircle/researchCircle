# Shared-host preparation

Prepared 2026-11-01. This is a reviewable staging procedure, not an executed shared
installation. T1's approved drafting excerpts and real Orin acceptance remain
pending. No shared services, ingress settings or existing databases were changed.

## Observed readiness

- Existing local workspace `tbr-core` remains running with its original database.
- Default development API/web images are ARM64. Separate
  `tbr-v2-api:shared-prep-amd64` and `tbr-v2-web:shared-prep-amd64` images were built
  successfully for Linux AMD64 without replacing those development tags.
- A later check on 2026-11-01 connected to G14 through Tailscale SSH after its
  authentication check. The LAN alias still timed out. G14 reports x86-64,
  Ubuntu 26.04.1 LTS and 821.9 GB free disk space, matching the prepared AMD64
  image architecture. Docker, Compose, containerd, Podman and nerdctl were absent;
  the Docker service and socket were absent too. Noninteractive sudo failed.
- Tailscale 1.104.2 is running, with no Serve configuration. Observed listening
  TCP ports were 22, 53, 631, 41590 and 46742; recheck before binding a port.
  The Orin peer was offline. No packages were installed and no remote settings,
  services, ingress or source data were changed. Container runtime installation
  and actual front-door validation remain prerequisites.
- No newer teammate implementation branch was present in the fetched remotes.
  The cumulative integration baseline remains `b179a7e`.

## HTTPS contract

`TBR_PUBLIC_SCHEME=http` preserves direct loopback development access. Set it to
`https` only when a trusted TLS front door terminates HTTPS and forwards to the
loopback proxy while preserving the browser's complete Host, including a port
when present. The front door must reject or redirect plain HTTP at that public
address. The application does not acquire TLS just by changing this setting.

The nginx container renders `deployment/nginx.conf` as a template at startup. It
uses the configured public scheme for API/frontend forwarding and ignores any
client-supplied `X-Forwarded-Proto`. Host is preserved. Uvicorn trusts forwarded
headers on the unpublished API within this single application's private Compose
network. Every container on that network is inside the trusted application
boundary. Do not publish an API port or attach untrusted containers. Only the
proxy's loopback port is published; the front door is a separate explicit setup.
Use the launcher to recreate services after this configuration change; restarting
an old proxy container does not update its mount/environment configuration.

A controlled local TLS front door verified registration, Secure/HttpOnly/SameSite
cookies, authenticated proposal saves, retained sessions after API/worker restart,
login and rejected foreign/wrong-scheme origins. This proves the deployment
contract, not that a particular Tailscale Serve or other target ingress preserves
Host. Verify the selected front door before sharing its address.

## Prepare artifacts locally

Use unique tags for a reviewed revision. Build on the target natively, or specify
its observed architecture when building here. The following AMD64 build matches
the architecture subsequently observed on G14:

```sh
.venv/bin/python -m deployment.build --platform linux/amd64 \
  --api-tag tbr-v2-api:shared-prep-amd64 \
  --web-tag tbr-v2-web:shared-prep-amd64

docker image inspect tbr-v2-api:shared-prep-amd64 tbr-v2-web:shared-prep-amd64 \
  --format '{{.RepoTags}} {{.Architecture}} {{.Id}}'
```

After committing and reviewing the exact revision, prepare a local bundle. These
commands neither copy source data nor push an image:

```sh
release=$(git rev-parse --short=12 HEAD)
bundle_dir="dist/shared-host/$release"
mkdir -p "$bundle_dir"
chmod 700 "$bundle_dir"
git rev-parse HEAD > "$bundle_dir/revision.txt"
git archive --format=tar.gz --output="$bundle_dir/source.tar.gz" HEAD \
  deployment src services packages frontend migrations pyproject.toml alembic.ini
docker image save --output "$bundle_dir/images.tar" \
  tbr-v2-api:shared-prep-amd64 tbr-v2-web:shared-prep-amd64
(cd "$bundle_dir" && shasum -a 256 source.tar.gz images.tar > SHA256SUMS)
```

The source archive includes only the named tracked build/runtime roots. It omits
collected `data/`, settings, database records, local output and unrelated scripts.
Image build contexts also exclude source snapshots and private settings. T2's
complete dependency lock/base-image digest review is still outstanding.

## Target procedure after host/access selection and deployment approval

1. Inspect `uname -m`, free disk, `docker version`, `docker compose version`,
   listening ports and the existing ingress configuration read-only. Match the
   image architecture; select an unused loopback port. Keep existing services.
2. Transfer the reviewed bundle to a new release directory outside any source
   snapshot. Verify checksums, run `docker image load --input images.tar`, then
   extract `source.tar.gz` into that directory. Alternatively build there natively.
   Loading these distinct staging tags does not deploy containers.
3. Create private runtime settings outside the release with mode 0600 from
   `deployment/.env.example`. Set a unique `COMPOSE_PROJECT_NAME`, the reviewed
   image tags, fresh database password, `TBR_PROFILE=demo`, local provider and
   observed reachable Orin URL/model. Use a separate work path. Never copy a
   developer's runtime settings or point at an existing project's database volume.
   The host source path is validation metadata: this launcher does not import or
   mount the source snapshot. Container work uses a new named volume.
4. Validate first, then use the gated launcher for the explicitly approved start:

   ```sh
   python3 -m deployment.start --env-file /absolute/private/runtime.env
   python3 -m deployment.start --env-file /absolute/private/runtime.env --start
   ```

   Run in a project Python environment with `services/api/requirements.txt`
   installed. Direct `docker compose up` bypasses the migration/schema gate.
5. Configure the approved private TLS front door to the selected loopback port,
   preserving Host. Inspect actual registration/login cookie flags and a
   same-origin save through that front door. Check registration, saved revision,
   API/worker restart and both retained-session/fresh-login reopen. Record actual
   image IDs, schema head and observed URL without credentials.
6. Separately verify Orin reachability/idleness, then run the fixed T1-approved
   drafting pack and one persisted browser job. Inspect claim support and accept
   without overwriting newer edits. Startup health alone does not prove this.

If checks fail, stop only this new project, preserve its settings/volumes and
inspect the failure. Never use `down -v`, database drops, resets, reindexing or a
source copy as a troubleshooting shortcut. T2 retains backup/restore/schema/lock
ownership; T1 retrieval and T3 frontend/browser work stay with their owners.
