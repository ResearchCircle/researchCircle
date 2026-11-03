# Using the previously collected data

## Source and local paths

Anurag sends the collected data folder directly, about 10 GB in 15,986 files. It is not in Git, and you do not need access to his machine. Keep the delivered folder as an immutable source snapshot, preferably outside your checkout. Record its location as `TBR_DATA_SOURCE` and a separate writable location as `TBR_DATA_WORK`. These are **onboarding/adapter configuration names**, not existing legacy environment support. T1 implements explicit path injection for the new adapter; simply exporting a variable does not redirect old code.

Example local arrangement (replace with your own absolute paths):

```text
shared-data/tbr-original/       supplied source copy; never mutated
work-data/tbr-dev/              disposable working copy/index outputs
researchCircle/                Git checkout, separate from those data paths
```

The current `src/utils/config.py` hardcodes PROJECT_ROOT/data and creates directories at import time. `CrawlConfig` defaults to restricted mode and chooses `data/restricted/chroma`; full mode chooses `data/chroma`. Never symlink the only source snapshot into a writable legacy path or assume a new env var overrides it. Pass a working-copy path through an adapter or consciously use a disposable checkout-local copy. Do not create copies until source/destination paths and disk capacity have been checked; never copy a directory into itself or over the source.

## What the folder contains

Counted on 2026-10-31. Confirm against your copy; do not treat these as guarantees.

| Path | Files | Size | Notes |
|---|---|---|---|
| `pdfs/` | 2,932 | 9.4 GB | Source PDFs. Skip them unless your task needs them. |
| `papers/` | 2,932 | 139 MB | Per-paper JSON. |
| `research_cards/` | 2,108 | 11 MB | Distilled paper cards. Likely the most useful starting point. |
| `rit_data_v2.json`, `comprehensive_data.json`, `rit_data.json` | 3 | 3.5 MB | Faculty and paper records (top-level `faculty` keys). |
| `tiger_brain.json`, `*.gml`, `kuzu_db` | 5 | about 155 MB | Graph exports and a graph database. |
| `chroma/` | 14 | 38 MB | Existing vector index. Check its embedding model before querying. |
| `cache/` | 7,842 | 243 MB | Parser output cache. |
| `restricted/` | 124 | 220 MB | A smaller crawl with the same layout. |
| `tiger_research.db` | 1 | 80 MB | **Mostly logs.** Its faculty, publication and tag tables are empty, so do not import from it. |

Stored paths in about 2,990 files point at Anurag's home directory. Those paths do not exist on your machine, so resolve files relative to your copy instead. Publishing rights for the PDFs and paper text have not been reviewed, so never commit or publish them. A scan of the non-PDF text files found no credentials.

If you keep the folder at `data/` inside your checkout, `.gitignore` blocks everything there except `.gitkeep`, `prompts/` and `taxonomies/`. Still treat it as read-only, and write indexes elsewhere.

## Inventory before importing

Inspect names/sizes first without importing project modules. Report counts and schema summaries, not raw people/document contents. Use pathlib/standard library or ordinary filesystem tools; no GPU, crawl or model call is necessary.

```sh
# Set this to the received snapshot on YOUR machine.
export TBR_DATA_SOURCE='/absolute/path/to/received/data'
python - <<'PYCODE'
import os
from pathlib import Path
p = Path(os.environ['TBR_DATA_SOURCE']).expanduser().resolve(strict=True)
assert p.is_dir(), 'Expected an existing directory'
print('Source:', p)
for child in sorted(p.iterdir(), key=lambda x: x.name):
    if child.is_symlink():
        print(child.name, 'symlink; inspect target separately')
    elif child.is_file():
        print(child.name, 'file', child.stat().st_size, 'bytes')
    elif child.is_dir():
        print(child.name, 'directory')
PYCODE
```

T1 records a small manifest with source snapshot label/date, relative path, kind, size, optional checksum, schema/version and usability status. Hash large binaries only when needed for handoff consistency. Inspect JSON shape and a few field names/types; do not print every record. Check all SQLite sidecars and database/index version compatibility before opening a copied database. Obtain a quiescent database snapshot: copying an actively written SQLite/Chroma directory can be inconsistent.

## Expected artifacts are candidates, not promises

| Candidate artifact from legacy code | Potential use | Check first |
|---|---|---|
| `rit_data_v2.json`, `restricted/rit_data_restricted.json`, `comprehensive_data.json` | Faculty/research/publication inputs | Actual schema, record count, external IDs, duplicate profiles and source links |
| `research_cards/` or `restricted/research_cards/` | Distilled paper summaries/concepts/citations | Actual presence; card_id, bibliographic_data, core_content and knowledge_graph shape; extraction quality |
| `pdfs/`, `papers/`, `publications/`, including restricted variants | Source documents and downloaded metadata | File types, provenance, linkage to cards/profile IDs, broken/truncated files |
| `chroma/`, `restricted/chroma/` | Existing public vector index | Storage/collection versions, collection names, model ID, vector dimension, nonempty count; open only a writable working copy |
| `tiger_research.db` | Legacy SQLite faculty/publication/tag data | Read schema using read-only mode; do not treat it as the new application Postgres database |
| `tiger_brain.json`, graph exports, `kuzu_db*` | Public researcher/paper/concept relations | Actual format/version and identity mapping; export JSON on a working copy if binaries are incompatible |
| `prompts/`, `taxonomies/` | Old extraction templates and topic taxonomy | These are reference inputs, not current project instructions or proof the corpus exists |

The directory name `restricted` means a limited crawl mode in legacy code. It does not prove a privacy classification or grant permission to publish its contents. Verify source/provenance and use only approved sample/public records for the early product.

## Rules for reuse

1. Preserve source snapshot and stable external IDs. Keep raw content separate from normalized records, generated fixtures and new indexes.
2. Inspect `VectorStore.clear()` before any legacy index entry point: it deletes and recreates a collection. Do not invoke clear/reset/recreate on supplied data. Chroma PersistentClient/get-or-create may write or migrate a directory even during exploratory use, so use a working copy.
3. Verify embedding identity/dimension before querying with a new encoder. Legacy config names `nomic-ai/nomic-embed-text-v1.5` but also contains an ONNX fallback, so configuration alone does not establish the stored model. If unknown/incompatible, use text/BM25 on extracted records first or rebuild a **new** index at a separate output path with recorded provenance.
4. Do not run `scripts/setup_v2.py` as a bootstrap: it crawls and references an obsolete LanceManager import. Do not run the full crawl/download/distillation pipeline to replace missing data without a specific request. Many legacy paths call Gemini or local model services.
5. T1 owns normalization/import. T2 consumes normalized source IDs/metadata and independently seeds business records. T3 consumes small sanitized response fixtures; no full corpus is needed in the frontend. Anurag receives a small source-linked retrieval example for real drafting validation.
6. Add only tiny synthetic/sanitized test fixtures with clear provenance. Never Git-add the supplied folder, PDFs, SQLite/index binaries or machine-specific absolute paths. Inspect ignore rules with `git check-ignore` before staging: not every artifact under data/ is ignored.
7. If the snapshot is missing/incomplete, report exactly which files are absent, implement a synthetic smoke path and keep the real-data acceptance pending. Do not invent counts, researchers, source URLs or claims of successful import.

## Handoff from T1

Deliver the manifest, selected usable input formats, field mapping, stable source ID rule, duplicate/rejection counts, the read-only input/writable output contract, an idempotent small import example, 3–5 source-linked queries, and the exact test command. Label synthetic evidence separately from shared-corpus evidence. Missing model/index compatibility is a bounded dependency, not a reason to block the whole team.

### T1 local snapshot pass

The local checkout contains the ignored source snapshot. A sanitized count/schema manifest is at [the T1 snapshot inventory](../qa/evidence/t1-snapshot-inventory.json); it contains no machine-specific path or raw profile/document text. The adapter reads only an explicitly supplied `rit_data_v2.json` and selects at most five records with a canonical HTTPS RIT computing-directory URL, a short name and bounded research-interest labels. Its field mapping is `name` to title, `url` to external ID and provenance, and `research_interests` to searchable text. It does not retain biography, email, education, publications, awards, lab, college, title, or course fields. The canonical profile URL is the external identity; `import_public_records` generates immutable source-version IDs from that identity and the content hash. Identical reimports are unchanged; changed content retires the prior public snapshot without mutating its source.

The observed scan counted 1,002 records, found 99 eligible profile facts, rejected 903, and selected five. The five passed ephemeral SQLite idempotence/source-link checks and were then imported into the isolated local app database after the user confirmed reuse for that local app: first import inserted five; reimport left all five unchanged. Five live collaborator queries returned canonical source-linked profiles. This confirmation is local to this app and does not establish approval for another deployment. Profile affiliation/currentness remains unknown; paper/card rights remain unreviewed and those records are excluded.

Start with non-persistent validation:

```sh
python -m src.platform.ingestion.import_rit_snapshot \
  --source-file /absolute/path/to/data/rit_data_v2.json
```

Database writes require an explicitly configured application database and both
`--apply --confirm-public-source-rights`. The user confirmed the five selected
profile facts for this isolated local app, and that bounded import has completed;
this is not a blanket grant for another deployment or for other snapshot content.
The explicit flag remains required for every write. The snapshot path must not
point into `restricted/`. PDFs/cards remain excluded, vector-index compatibility
is unverified, and search remains BM25-only/degraded.

Focused adapter and in-memory persistence tests:

```sh
.venv/bin/python -m pytest tests/platform/test_rit_snapshot.py -q
```

### Manual opportunity data

`src/platform/ingestion/opportunities.py` accepts a JSON envelope containing at
most 50 manually reviewed records and emits payloads for the existing
`POST /api/v2/opportunities` contract. It preserves source URLs, requires timezone
offsets for known deadlines, validates optional IANA timezone names, and defaults
eligibility to `unknown`; it never infers deadline or eligibility. The matching
filter contract supports case-insensitive text in title/notes, exact eligibility,
and an offset-aware `deadline_before` bound; undated opportunities do not match a
deadline bound. The API route remains membership-scoped and the UI's manual form
continues to use that same route.

`tests/platform/fixtures/opportunities-sample.json` contains synthetic-only
examples; it is not a real funding call. API integration tests import those
payloads through the existing route and verify that unknown values and source
links survive. Query parameters on the API list route still need review with T2
before adding a shared server-side filter contract.
