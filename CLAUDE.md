# Repository working instructions

Read `AGENTS.md` first and follow its product-first scope, ownership boundaries, data handling and implementation rules.

## Current sources of truth

- `docs/design/17-v2-corrected-specification.md`: active product specification.
- `docs/design/18-four-person-delivery-plan.md`: assignments, interfaces and delivery milestones.
- `docs/onboarding/README.md`: local setup and role-specific starter prompts.
- `docs/onboarding/DATA-HANDOFF.md`: inventory and reuse of the separately supplied data snapshot.

The initial goal is a working discovery → team → proposal → local draft → export → outcome workflow. Advanced security is scheduled later. Historical plans, archived hardening designs and legacy setup commands do not create current release requirements.

## Starting work

Inspect the current branch, working-tree changes and actual files before implementing the assigned ticket. Preserve unrelated work. Use project-local environments, inspect dependency manifests and run focused checks for the owned slice. Planned routes, migrations and helpers may not exist yet; do not report them as working without verification.

The existing API entry point is `services.api.app:app`. Local frontend setup uses the checked-in npm lock. Follow the onboarding guide for exact setup expectations; legacy cloud credentials are not required for fixture-based development. Only the platform lead handles Orin deployment and real model validation.

## Data and publication

The platform lead shares collected data separately. Resolve its local snapshot path on the current machine; keep it unchanged and use a separate working directory for imports and indexes. Do not run destructive index/reset or full crawl/distillation scripts as a setup shortcut.

Do not commit credentials, environment values, private documents, collected database/index binaries or machine-specific home-directory paths. Do not print their contents in reports. Add only small synthetic or approved sanitized fixtures. Follow the shared file-ownership and review rules in `AGENTS.md`; stage only task files, and push only when explicitly authorized.

Every handoff distinguishes fixture-based progress from verified database/browser/Orin integration and includes actual test commands/results. Never invent source IDs, citations, data counts or verification evidence. Do not add automated authorship, attribution trailers or tool footers to repository artifacts.
