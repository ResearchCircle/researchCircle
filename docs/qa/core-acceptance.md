# Local core acceptance record

Updated 2026-10-31 at commit `50c4041`. Scope: working local research workflow
against real PostgreSQL, with labeled synthetic and small bounded public sources. Shared deployment and real-corpus quality are not
claimed. The model-backed application check remains incomplete.

| Check | Evidence | What it proves |
|---|---|---|
| Backend checks | 147 tests passed using `python -m unittest discover -s tests/platform -q` | Accounts, membership, saves, source isolation, jobs, errors, migrations, outcomes and runtime behavior; focused DB tests include isolated SQLite. |
| Frontend checks | 19 Node checks and a production build passed | API payloads, stale suggestion handling, safe links, tracking retry keys and timezone conversion. |
| Real browser core | [browser-core.json](evidence/browser-core.json) | Named registration, team/proposal, source search/attachment/selection, persisted fixture job/citation review, revision-safe append, reopen/export, second-user invite/edit and owner 409 preserving edits. |
| Real browser shortlist | [browser-shortlist.json](evidence/browser-shortlist.json) | Saved paper/candidate with no member added, notes surviving refresh and team changes, guarded team switching, removal persistence, and read-only viewer controls with a server 403. |
| Official profiles | Live fetch of the three allowlisted RIT pages; import ran twice on the local PostgreSQL stack (3 inserted, then 3 unchanged); checked once in a browser | Expertise-keyword search returns the right profile, labeled "Researcher profile" with its official link. The label check was a one-off script, not a stored browser story. |
| Real browser tracking | [browser-tracking.json](evidence/browser-tracking.json) | Unknown fields stay unknown; manual opportunity/submission/outcome/history persist; same-key retry returns the same outcome and changed payload returns 409. |
| PostgreSQL concurrency | [database smoke](../../scripts/orin/evidence-postgres-core.json) | Four queued admissions, one active job per user, actual concurrent saves returning 200/409, captured snapshot roundtrip and interrupted-job state. |
| Backup/restore | [restore smoke](../../scripts/orin/evidence-backup-restore.json) | Restored development records match canonical row fingerprints; source DB and backup retained. This run includes tracking tables but predates public records and shortlists; repeat the command for schema `0004`. |
| Proxy replacement | [proxy smoke](../../scripts/orin/evidence-proxy-replacement.json) | Real HTTP routing/query/Host/redirect behavior and replacement API DNS recovery, using disposable HTTP fixtures. |
| Images | Local API/frontend builds and actual running core stack | Source snapshots and environment files excluded; non-root runtime; migration/seed/start sequence exercised. |
| Real Orin | Earlier provider completions; first application job rejected invalid citations; reachability probes timed out, including SSH again on 2026-10-31 | Provider availability was observed earlier, but no successful persisted real-model browser journey is claimed. |

Browser runs used the rebuilt stack from `deployment.dev --provider fixture --build`. The core browser run saved revision 4 after accepting the suggestion; a second
named user saved revision 5. The stale owner save returned 409 and retained local
edits. Browser artifacts record the source/job IDs and actual fixture model ID,
not passwords, source dumps or an invented endpoint. `checkout_dirty` was true because
unrelated local scripts and these documentation edits were present; none affect the running images.

Fixes made from observed failures: missing React ref initializer; simultaneous
invitation acceptance; proxy loss of external port; stale Docker upstream IP after
API recreation; shutdown persistence failure retaining a lease/exposing SQL error
parameters; and unavailable model-status probes leaving jobs queued indefinitely.
Focused regressions failed before each relevant implementation fix and passed afterward.

Current reproducible local start and owner assignments are in
[CORE-HANDOFF.md](../onboarding/CORE-HANDOFF.md). The external browser suite is in
the homelab repository at `tiger_research_buddy/`, branch `tbr/core-browser-suite`, commit `5077b60`.
