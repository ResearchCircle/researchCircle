# Continuous critical implementation

Current user direction: keep implementing the most critical work across the
workstreams, with focused local commits. Continue until the user explicitly asks
to stop and prepare a handoff. Do not prepare transfer bundles, owner handoffs or
declare the broader product complete merely because a fixture demo passes.

The goal-management tools expose status updates but no objective-text update.
This newer user direction controls the ongoing work despite the older stored title.

## Next priorities

1. Useful public discovery beyond the six synthetic examples: immutable versioned
   public records, bounded public import, database-backed retrieval and provenance.
2. Saved team shortlist with explicit add/remove and role checks; ranking never
   adds members automatically.
3. Evidence-backed collaborator matching and citation quality, truthful degradation
   and no publication of proposal-only sources.
4. Retry actual persisted Orin generation when the observed service is reachable;
   never restart a model fleet or substitute a cloud provider to hide failure.
5. Continue hardening ordinary correctness and connected browser coverage before
   broader polish or advanced infrastructure.

Preserve unrelated files and the immutable received source snapshot. Existing
draft handoff documents are prior work; do not finalize/package them until asked.
Do not push, publish or deploy to a shared/production environment without explicit
authorization. Local development and tests remain authorized.

## Public-source contract for the next slice

`PublicRecord` is metadata for an immutable `Source` snapshot. Source text, version
and hash never change under an existing source UUID. The stable logical
`external_id` may have newer versions: keep old attached snapshots and mark only
the current metadata record searchable. Reimport of identical content is a no-op.

Public-record fields: source_id (PK/FK sources.id), external_id, kind
(paper/researcher), evidence_kind (public/synthetic), is_current, metadata_json,
imported_at. One current version per external_id. Source UUID/version are derived
deterministically from logical identity plus exact normalized content hash.

Public search must join metadata to Source and require is_public=true,
proposal_id=null and is_current=true. Metadata does not grant visibility to a
private source. Unknown author identity, affiliation or eligibility stays unknown.

The next migrations are reserved: 0003 public records, 0004 team shortlist.
Root coordinates shared metadata/app composition; implementers do not stage or
commit concurrently.
