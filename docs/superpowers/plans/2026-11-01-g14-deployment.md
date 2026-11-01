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
2. Add optional host bind paths for PostgreSQL/work in the platform Compose file;
   defaults retain existing named volumes. Prove both configurations resolve and
   existing rehearsal behavior still works. New G14 state stays in the project.
3. Transfer reviewed releases/images with checksums to new project directories.
   Store private settings mode 0600, named sessions, local provider and observed
   private Orin address. No inference success is assumed while Orin is offline.
4. After runtime authentication/install, verify permissions, image architecture,
   loopback/private TLS routing, migration/schema gate, registration/save/restart
   persistence and cookie/origin checks on G14. Retain all test records.
5. When approved T1 input and Orin exist, run actual persisted quality cases and a
   browser draft/citation/accept/export journey. Missing dependencies stay pending.
6. Record actual evidence, independent final review and focused local commits.

Interface checks: Compose mount defaults must preserve existing core/rehearsal
volumes; G14 bind directories require the application UID 10001; host launcher is
stdlib-only so Python 3.14 need not install application dependencies. Runtime API
images keep Python 3.12. Private HTTPS must preserve Host and configured scheme.
