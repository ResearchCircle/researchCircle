# Using the previously collected data

## Source and local paths

Anurag's source path: `/Users/anurag/Startups/TBR/tiger_research_buddy/data`.

Other machines will have a different absolute path. Keep the delivered folder as an immutable source snapshot, preferably outside your checkout. Record its location as `TBR_DATA_SOURCE` and a separate writable location as `TBR_DATA_WORK`. These are **onboarding/adapter configuration names**, not existing legacy environment support. T1 implements explicit path injection for the new adapter; simply exporting a variable does not redirect old code.

Example local arrangement (replace with your own absolute paths):

```text
shared-data/tbr-original/       supplied source copy; never mutated
work-data/tbr-dev/              disposable working copy/index outputs
researchCircle/                Git checkout, separate from those data paths
```

The current `src/utils/config.py` hardcodes PROJECT_ROOT/data and creates directories at import time. `CrawlConfig` defaults to restricted mode and chooses `data/restricted/chroma`; full mode chooses `data/chroma`. Never symlink the only source snapshot into a writable legacy path or assume a new env var overrides it. Pass a working-copy path through an adapter or consciously use a disposable checkout-local copy. Do not create copies until source/destination paths and disk capacity have been checked; never copy a directory into itself or over the source.

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
