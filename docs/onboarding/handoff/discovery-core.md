# Discovery core handoff

The connected sample slice exposes:

```python
from src.platform.discovery.search import list_samples, search

rows = list_samples()
page = search('sensor greenhouse', limit=10)
```

`list_samples()` returns six source rows: three synthetic paper examples and three
synthetic collaborator profiles. Each title and origin explicitly identifies the
synthetic evidence. None represents real faculty, a real paper, an institution or
a real contact address. There are no fabricated public URLs.

Rows include `id`, `source_id` (the same UUID), `version`, `content_hash`, `title`,
`snippet`, `origin`, `score`, `reason`, `kind`, `evidence_kind` and `text`. The
application may seed these explicitly approved sample rows as public sources, but
attaching them to a proposal still requires the ordinary explicit attachment row.
No proposal content is automatically added to discovery.

Search returns `{items, degraded: true, next_cursor: null}`. It matches keywords in
title/text with a small title boost and deterministic tie ordering. Empty,
stop-word-only and unmatched queries return an empty list. Scores are ranking
values, not calibrated probabilities. Snippets are exact substrings of source
text. This is a dependency-free lexical fallback, not semantic retrieval, BM25,
graph matching or a claim of reviewed collaborator relevance.

## Import and identity

`src.platform.ingestion.import_public.import_records(records)` normalizes explicit
public/sample inputs into the same row shape. Each input supplies `external_id`,
`title`, `text`, `origin`, `version`, `kind`, `evidence_kind`, `is_public=True`, and
no proposal scope. Private or proposal-scoped inputs fail before indexing.

IDs use UUID5 of the kind and stable external ID. A versioned text update keeps its
source ID and changes its SHA-256 text hash. Hashes cover exact UTF-8 text; no
normalization silently changes supplied evidence. Repeated identical batches
produce the same rows; duplicate text within a kind is collapsed deterministically;
conflicting records for one identity fail rather than choosing a version silently.
Cross-identifier deduplication is a batch rule, not a persisted alias-resolution
service. T1 must define durable aliases when integrating a larger corpus.

The importer performs no filesystem, database, crawl, embedding or network I/O.
Actual database upserts and persisted reimport checks belong to the application
integration; deterministic normalization alone does not prove storage durability.

## Reuse inspected and verification

`src/retrieval/hybrid_retriever.py` implements BM25 plus vector RRF, but imports
NumPy, rank_bm25 and VectorStore. `src/collaboration/matcher.py` imports graph,
database and configuration modules. Importing these paths would couple this small
slice to heavyweight initialization and legacy configuration side effects. They
were inspected without importing them. The new adapter does not reproduce their
semantic or graph claims. A later reviewed adapter may inject their retrieval
results once public-corpus/model compatibility is known.

```sh
.venv/bin/python -m unittest discover -s tests/platform -p test_discovery_core.py -v
```

Result: 11 tests passed. Checks cover stable identities and exact hashes,
deduplication, malformed/private/proposal-scoped input rejection, synthetic
provenance, matching/nonmatching queries, repeatability, limits, caller mutation
isolation and absence of legacy model/configuration imports. No source snapshot
was read or modified, and no model or external service was called.

## Remaining work

- T1 supplies a reviewed source-linked public corpus and identity/alias mapping.
- T1 integrates the reviewed retrieval and matcher behind the small pure boundary,
  records corpus/index/model versions and evaluates evidence-backed shortlists.
- The application integrates source seeding, search routing, explicit proposal
  attachment and persisted import checks. Search results alone do not prove that
  complete journey or production data ingestion works.
