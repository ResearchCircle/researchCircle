"""Normalize explicit public/sample records without a database or model import.

Stable source IDs let the application upsert repeated imports. This function only
returns records: it never reads, modifies or indexes a supplied source snapshot.
Public classification is supplied by the caller, not inferred from a filename.
"""

import hashlib
from collections.abc import Iterable, Mapping
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5


def _required(record: Mapping, field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Public/sample records require nonempty identity, text and provenance fields.')
    return value


def import_records(records: Iterable[Mapping]) -> list[dict]:
    """Return stable, deduplicated rows for explicit public or synthetic inputs.

    Same external ID retains its source UUID across versioned text changes.
    Conflicting versions in one batch fail rather than choosing one silently.
    Duplicate text of the same kind is collapsed deterministically. Persistence
    and transactional upserts belong to the application's Source store.
    """
    by_id = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError('A public/sample source must be a mapping.')
        if record.get('is_public') is not True or record.get('proposal_id') is not None:
            raise ValueError('Private or proposal-scoped sources cannot enter public discovery.')
        external_id = _required(record, 'external_id').strip()
        title = _required(record, 'title').strip()
        text = _required(record, 'text')
        origin = _required(record, 'origin').strip()
        version = _required(record, 'version').strip()
        kind, evidence = record.get('kind'), record.get('evidence_kind')
        if kind not in ('paper', 'researcher') or evidence not in ('public', 'synthetic'):
            raise ValueError('Use an explicit paper/researcher kind and public/synthetic evidence classification.')
        if evidence == 'synthetic':
            if not title.casefold().startswith('synthetic ') or not origin.casefold().startswith('synthetic '):
                raise ValueError('Synthetic sources must be labeled in their title and origin; do not invent public links.')
        else:
            try:
                url = urlsplit(origin)
                valid_origin = (url.scheme in ('http', 'https') and bool(url.hostname)
                                and not url.username and not url.password)
            except ValueError:
                valid_origin = False
            if not valid_origin:
                raise ValueError('Public sources require an HTTP source URL without credentials.')
        source_id = str(uuid5(NAMESPACE_URL, f'urn:researchcircle:public-source:{kind}:{external_id}'))
        row = {
            'id': source_id,
            'source_id': source_id,
            'version': version,
            'content_hash': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'title': title,
            'snippet': text[:280],
            'origin': origin,
            'score': 0.0,
            'reason': 'Imported sample; use keyword search for a match reason.' if evidence == 'synthetic'
                      else 'Imported public source; use keyword search for a match reason.',
            'kind': kind,
            'evidence_kind': evidence,
            'text': text,
        }
        previous = by_id.get(source_id)
        if previous is not None and previous != row:
            raise ValueError('One import contains conflicting records for the same source identity.')
        by_id[source_id] = row
    rows = []
    seen_hashes = set()
    for row in sorted(by_id.values(), key=lambda item: item['id']):
        key = (row['kind'], row['content_hash'])
        if key not in seen_hashes:
            rows.append(row)
            seen_hashes.add(key)
    return rows
