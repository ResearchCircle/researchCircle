# V2: working product first

Updated 2026-10-30. Current priority: a working platform; advanced security follows later.

New team members: start with [repo setup and copy-paste role prompts](../onboarding/README.md). Read [the data handoff guide](../onboarding/DATA-HANDOFF.md) before opening or importing the separately shared data snapshot.

1. [Working product specification](17-v2-corrected-specification.md) — current features, architecture, scope and acceptance.
2. [Four-person delivery plan](18-four-person-delivery-plan.md) — Anurag/Teammate 1/2/3 assignments, dependencies and schedule.
3. [Conventions](CONVENTIONS-single-box.md) — repository working rules.
4. [Milestones](14-build-runbook-and-phases.md) — demo, alpha and later work.

## What we build now

Discovery → shortlist/team → proposal editor → selected-source local drafting → review/export → outcome tracking. Start with a normal versioned editor; real-time CRDT editing is an enhancement after the core journey works.

| Person | Active focus |
|---|---|
| Anurag | Orin inference, drafting quality, integration and deployment |
| Teammate 1 | Public data, retrieval, matching and opportunities |
| Teammate 2 | Workflow backend/database, ordinary accounts/membership, saves/jobs/export/outcomes |
| Teammate 3 | Frontend and browser journey/E2E |

The [former hardening specification](reference/security-hardening-specification.md) and [security-first schedule](reference/security-first-delivery-plan.md) are deferred reference. They do not block this release. The [audit](16-v2-critical-review-and-revised-plan.md) records earlier defects, not current scope or estimates.

Chapters 01–13 and 15 and the old JSON briefs remain historical. Their precedence/frozen/copy-verbatim instructions are withdrawn. Current specification controls product scope; current team plan controls ownership. Working code and tests must demonstrate completion; mock-only screens are not an integrated product.
