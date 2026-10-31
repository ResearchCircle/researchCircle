# V2 product-first conventions

Updated 2026-10-30.

## Authority and scope

Follow the [working product specification](17-v2-corrected-specification.md) and [team delivery plan](18-four-person-delivery-plan.md). Their current product milestone supersedes the security-first pilot. Archived references and older chapters do not create hidden release requirements.

## Repository

Build in this repository using existing `src/`, `services/api/`, `frontend/` and contracts. Add cohesive feature adapters under `src/platform/`; avoid a new package/service for every abstraction. Use the existing public Chroma/BM25 retrieval until there is a demonstrated need to migrate. PostgreSQL owns new business records; migration work belongs to T2.

Anurag owns Orin provider/runtime/deployment; T1 data/retrieval; T2 workflow/backend; T3 frontend/E2E. T2 coordinates app/router/migration integration. Shared DTO changes need both producer and consumer review. Pin working project dependencies and document startup; do not assume global Python packages are correct.

## Delivery

Prioritize connected user workflows. Review small PRs and integrate twice weekly. Real saves, source-linked results and local Orin completions are release evidence; fixtures unblock local work but do not substitute for integration.

Keep ordinary account/membership checks, versioned saves, input limits, parameterized queries, safe secret handling and useful errors as part of feature implementation. Advanced encryption, formal policy systems, cryptographic deletion, RLS machinery, journal services and security certification are later projects. Do not add them as dependencies to current tickets.

Use same-origin browser API configuration and internal model endpoints. Keep proposal sources out of the public index unless separately published. No secrets or real private data in fixtures/commits/logs. Run database migrations explicitly; never wipe stores at startup.

Browser E2E lives in the external `~/code/homelab/tiger_research_buddy/` suite following its AGENTS.md; local component/unit tests stay in this repository. Anurag runs shared Orin deployments and hardware acceptance from teammates' reproducible bundles.
