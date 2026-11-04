"""Bulk-import the local paper corpus (data/papers/*.json + data/pdfs/*.pdf).

Writes each paper as a public Source + PublicRecord, with metadata_json.pdf_file
pointing at the companion file under /app/data/pdfs so the Read-PDF route can
serve it. Idempotent: re-running imports the same identities without duplication.
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

from src.platform.database import Database
from src.platform.ingestion.public_store import import_public_records


PAPERS_DIR = os.environ.get('TBR_PAPERS_DIR', '/app/data/papers')
PDFS_DIR = os.environ.get('TBR_PDFS_DIR', '/app/data/pdfs')


def _record_for_paper(path: str, pdf_dir: Path) -> dict | None:
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        return None
    title = (data.get('title') or '').strip()
    abstract = (data.get('abstract') or '').strip()
    pdf_url = (data.get('pdf_url') or '').strip()
    pdf_local = (data.get('pdf_local') or '').strip()
    if not title or not abstract or not pdf_url.startswith(('http://', 'https://')):
        return None
    pdf_name = Path(pdf_local).name if pdf_local else Path(path).with_suffix('.pdf').name
    if not pdf_name.lower().endswith('.pdf'):
        return None
    if not (pdf_dir / pdf_name).exists():
        return None
    stem = Path(path).stem
    text = abstract if len(abstract) >= 120 else f'{abstract}\n\n{(data.get("extracted_text") or "")[:1500]}'.strip()
    return {
        'external_id': f'paper:{stem}',
        'title': title[:300],
        'text': text,
        'origin': pdf_url,
        'version': 'corpus-v1',
        'kind': 'paper',
        'evidence_kind': 'public',
        'is_public': True,
        'proposal_id': None,
        'metadata': {'pdf_file': pdf_name},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--papers-dir', default=PAPERS_DIR, help='Directory of paper JSON records')
    parser.add_argument('--pdfs-dir', default=PDFS_DIR, help='Directory of companion PDF files')
    parser.add_argument('--limit', type=int, default=0, help='Optional cap for testing (0 = all)')
    parser.add_argument('--batch', type=int, default=200, help='Batch size per commit')
    args = parser.parse_args()

    pdf_dir = Path(args.pdfs_dir)
    if not pdf_dir.is_dir():
        print(json.dumps({'status': 'failed', 'message': f'PDF directory {pdf_dir} missing'}), file=sys.stderr)
        return 1
    paths = sorted(glob.glob(os.path.join(args.papers_dir, '*.json')))
    if args.limit:
        paths = paths[: args.limit]

    database = Database()
    database.engine  # validate config early
    totals = dict(inserted=0, unchanged=0, retired=0, skipped=0)
    batch: list[dict] = []
    for p in paths:
        rec = _record_for_paper(p, pdf_dir)
        if rec is None:
            totals['skipped'] += 1
            continue
        batch.append(rec)
        if len(batch) >= args.batch:
            with database.session_factory() as session:
                counts = import_public_records(session, batch)
                session.commit()
            for k, v in counts.items():
                totals[k] = totals.get(k, 0) + v
            batch = []
    if batch:
        with database.session_factory() as session:
            counts = import_public_records(session, batch)
            session.commit()
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v

    print(json.dumps({'status': 'imported', 'evidence': 'local_corpus', 'scanned': len(paths), **totals}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
