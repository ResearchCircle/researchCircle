# G14 deployment execution

Authorization: install Docker/Compose, deploy private HTTPS, verify migrations and
restart persistence, then evaluate T1-approved drafting and the real browser flow.
Keep all project artifacts and application data under `~/researchCircle` on G14.
Preserve existing source snapshots, databases and unrelated work. No cloud model
calls, fixture substitution in demo mode, source-data copying or public Funnel.

1. Prepare the project directories and reviewed interactive runtime installer.
   Docker/Compose are absent; sudo requires interactive authentication. The
   installer uses existing signed Ubuntu packages (simulated: seven installs,
   zero removals), enables Docker and grants the existing login user access.
   Configure only empty private Serve ingress, preserving any existing config.
   Before package installation, configure Docker's data-root and containerd's root
   under `~/researchCircle/runtime/`. Refuse existing foreign roots, nonempty old
   runtime data and symlink output paths; preserve unrelated config with private
   backups. OS packages/service pointers remain in standard system locations.
   Keep local configuration when package installation supplies a default file.
2. Add optional host bind paths for PostgreSQL/work in the platform Compose file;
   defaults retain existing named volumes. Prove both configurations resolve and
   existing rehearsal behavior still works. New G14 state stays in the project.
3. Transfer reviewed releases/images with checksums to new project directories.
   Store private settings mode 0600, named sessions, local provider and observed
   private Orin address. No inference success is assumed while Orin is offline.
4. After runtime authentication/install, load the bundle and initialize only the
   newly prepared worker bind directory with UID/GID 10001 before the gated start:
   `docker run --rm --user 0 --entrypoint chown --mount
   type=bind,source=/home/anurag/researchCircle/state/tbr-researchcircle/work,target=/work
   tbr-v2-api:g14-deploy 10001:10001 /work`.
   Verify permissions, image architecture,
   loopback/private TLS routing, migration/schema gate, registration/save/restart
   persistence and cookie/origin checks on G14. Retain all test records.
5. When approved T1 input and Orin exist, run actual persisted quality cases and a
   browser draft/citation/accept/export journey. Missing dependencies stay pending.
6. Record actual evidence, independent final review and focused local commits.

Interface checks: Compose mount defaults must preserve existing core/rehearsal
volumes; G14 bind directories require the application UID 10001; host launcher is
stdlib-only so Python 3.14 need not install application dependencies. Runtime API
images keep Python 3.12. Private HTTPS must preserve Host and configured scheme.

Final review resolutions: both daemon stores now honor the project-root requirement;
worker bind ownership is explicit; installer reads TBR_HTTP_PORT from private
settings instead of assuming the env example's default; evidence distinguishes
historical shared-preparation runs from current storage verification.

## Execution evidence

- Tasks 1–4 completed: interactive install succeeded; Docker/Compose and both
  daemon roots verified; checksummed app release/images loaded; private Serve
  certificate/Host/scheme confirmed; gated schema `0004` and real PostgreSQL,
  API/worker restart plus retained/fresh login and browser save/export passed.
- Local suite: 192 run, 189 passed, three opt-in checks skipped. Three bind-storage
  and two default-volume TLS checks passed separately; seven runtime-storage
  preservation tests passed. `deployment/evidence-g14-deployment.json` records
  actual image IDs, paths, statuses and the scope of browser checks.
- Task 5 pending: Orin still reports offline; approved T1 excerpts are not present
  in fetched branches. No real drafting/model quality pass is claimed.
- Task 6 completed for the deployed platform slice: review findings addressed,
  data preservation checked and local commits/evidence recorded. No push/PR/merge.
