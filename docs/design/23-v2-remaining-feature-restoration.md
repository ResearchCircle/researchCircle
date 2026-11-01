# Remaining v2 feature restoration

Added 2026-11-01. The original Collaboration Hub, graph visualization and research
chat are explicitly part of the remaining v2 work. Their source files are retained,
but none of these original screens is connected to the current workspace or
available in the deployed app. Restoring a component import alone is insufficient.

The shared integration branch is `anurag/latest`. Start ticket branches from its
current remote head and target reviews there. Existing P1 stability and real-model
acceptance remain in [CORE-HANDOFF](../onboarding/CORE-HANDOFF.md#next-work).
The earlier graph/P2 scheduling does not remove it from this remaining v2 backlog;
P1 completion must not be reported as completion of all restored v2 features.

## R-V2-1: Collaboration Hub

Restore the idea-to-collaborator journey using existing teams, proposals, public
source records and saved shortlists. Retained starting points:
`frontend/src/components/CollaborationHub.tsx` and `src/collaboration/matcher.py`.
Inspect legacy imports before reuse; do not initialize or modify the received
source snapshot as a shortcut.

- **T1:** evidence-backed researcher matching, supported author/profile resolution,
  reasons, provenance and explicit gaps. Unknown identity/availability stays unknown.
- **T2:** review/compose the v2 routes and storage contract; reuse existing records
  where appropriate. Coordinate any new schema with the consuming owners.
- **T3:** restore the idea form, match results and explicit shortlist/proposal
  actions in workspace navigation, with loading/empty/degraded/error states.
- **Platform lead:** integrate the owned provider/deployment slice if model-based
  summaries are included, and verify the connected journey.

Acceptance: a representative idea returns real source-linked candidates; a user
can inspect the reasons, curate a shortlist and continue to a proposal. Ranking
never enrolls a collaborator. Any restored impact/SDG summary must be identified
as a suggestion; numerical scores require a reviewed meaning and evidence.

## R-V2-2: Graph visualization

Reconnect `frontend/src/components/GraphViewer.tsx` to reviewed public relationship
data through the same-origin v2 API. Existing graph modules remain reuse candidates,
not verified adapters or permission to rebuild/reindex the source snapshot.

- **T1:** define stable node/edge identities, supported relationships, provenance
  and an explicitly versioned graph snapshot/adapter.
- **T2:** review and compose the graph read contract/routes; enforce existing
  membership boundaries wherever proposal-scoped data is involved.
- **T3:** wire graph navigation, pan/zoom and node/edge inspection with source links,
  plus honest empty/error states. Keep it connected to discovery evidence.
- **Platform lead:** verify deployment routing and cross-surface integration.

Acceptance: actual researcher/work/topic relationships render with inspectable
support; relevant nodes open their evidence. No fabricated edges, placeholder
identities or private proposal sources in the public graph. Missing graph data
remains empty/unavailable rather than being replaced by a fabricated demonstration.

## R-V2-3: Previous research chat

Restore multi-turn research Q&A and inspectable source citations as a distinct
workspace surface. Proposal drafting does not supply this conversational workflow.
Retained starting points: `frontend/src/components/ChatInterface.tsx`,
`CitationPanel.tsx` and the reviewed portions of `src/chatbot/`.

- **Platform lead:** adapt grounded chat inference to the current local provider,
  context limits and shared single-generation admission/cancel/drain behavior.
  Never revive an implicit cloud fallback or let chat bypass draft serialization.
- **T1:** provide approved retrieval/context and stable source identities for answers.
- **T2:** review chat/job/session contracts and compose routes; agree conversation
  history ownership/persistence before adding tables or migrations.
- **T3:** reconnect conversation/history and source inspection, retain useful prior
  controls, and provide truthful busy/offline/failure/cancel states.

Acceptance: successive questions use the intended conversation context, supported
answers cite actual approved sources, and missing evidence is explicit. A named
user cannot access another team's private context. Chat and drafting share one
model admission path. Fixture checks are development evidence; real local-model
conversation/citation acceptance remains a separate required check.

## Integration and completion

Replace all legacy browser calls to `http://localhost:8000/api/idea`, `/api/graph`
and `/api/chat` with reviewed same-origin `/api/v2` contracts. The browser must not
call a developer's localhost, a model server or a cloud provider directly.
Producer/consumer owners review contracts together; T2 retains route/migration
composition and T3 retains frontend/browser implementation.

For each restoration, record focused backend/component checks, a real browser
journey, data/provider identity and fixture-versus-real limitations. Existing login,
saves, membership, drafting, export and outcomes must continue to work. Preserve
all parsed/downloaded data and existing databases. None of these tickets is marked
implemented or passed by this planning update, and Orin recovery alone does not
complete them.
