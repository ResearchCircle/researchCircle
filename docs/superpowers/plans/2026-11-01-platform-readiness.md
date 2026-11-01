# Platform Readiness Implementation Plan

**Goal:** Deliver the three objectives in
[Platform readiness objective](../../design/21-platform-readiness-goal.md).

**Execution:** Implement tasks in this session with focused tests, independent
review and small local commits.

**Architecture:** Deployment invokes the existing Alembic migrations in the same
API image and environment used by the worker. A schema check must pass before
application startup. A separate Docker project proves fresh-install persistence.

**Stack:** Python 3.12, Docker Compose, PostgreSQL, SQLAlchemy/Alembic, HTTPX.

## Constraints and review focus

- Never delete source data, existing databases or volumes; retain rehearsal data.
- Migration failure or a stamped but incomplete schema must stop worker startup.
- Configuration-only execution must not migrate or start services.
- Existing rows must survive repeat migration and restart.
- Keep secrets out of errors/evidence; check one effective runtime configuration.
- Preserve teammate ownership and require approved T1 excerpts for quality claims.

## Task 1: Database gate and launcher ordering

Files: `deployment/schema.py`, `deployment/start.py`,
`tests/platform/test_schema_gate.py`, `tests/platform/test_runtime.py`.

- [ ] Add failing behavior tests: fresh schema upgrade, repeat upgrade preserves
  records, missing application table at recorded head fails verification, failed
  migration prevents API/worker startup, dry-run performs no migrations.
- [ ] Implement `upgrade_and_verify(database=None) -> dict` using existing Alembic
  revisions, current-head comparison and metadata drift check. Emit safe errors.
- [ ] Implement `start_stack(command, env, ready_timeout)` with DB-only startup,
  one-off schema gate, application startup and existing HTTP readiness checks.
- [ ] Run focused and complete platform tests, review and commit only task files.

## Task 2: Fresh installation rehearsal

Files: `deployment/rehearse.py`, `deployment/evidence-fresh-start.json`,
`deployment/README.md`, relevant tests under `tests/platform/`.

- [ ] Create an explicit fixture-only rehearsal with a new project/volume, private
  settings and loopback port. Reuse the shared startup orchestration.
- [ ] Register a synthetic named user, create/save a proposal, restart API/worker,
  then reopen through the persisted session and a fresh login.
- [ ] Verify Alembic head, retain the database/volumes, and stop only new containers.
- [ ] Compare the source snapshot against its read-only baseline. Record safe
  counts/digests and actual results, not credentials or source contents.
- [ ] Review and commit the rehearsal and evidence.

## Task 3: Drafting acceptance criteria

Files: `docs/design/22-drafting-acceptance-criteria.md`, owned evaluation interfaces
under `scripts/orin/` only if required by approved input format.

- [ ] Identify T1's reviewed excerpt pack and require origin, immutable source
  identity/version/hash, expected facts, forbidden claims and supporting quotes.
- [ ] Define pass/fail cases for faithful single/two-source drafting, insufficient
  evidence, disagreement, numeric fidelity and instructions embedded in sources.
- [ ] Define separate structural and human claim-support judgments, plus actual
  model/usage/latency recording. Keep real execution pending until inputs/Orin exist.
- [ ] Review and commit criteria without importing or altering collected data.

## Task 4: Integration update

File: `docs/platform-integration-update.md`.

- [ ] Compare against the team's pushed baseline and summarize the final platform
  changes, test commands, evidence and unresolved real-model gates.
- [ ] Include startup, citation diagnostics and existing simulation evidence in one
  reviewable update. Do not push or open a PR without a request.
