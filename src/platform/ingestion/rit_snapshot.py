"""Prepare a small, privacy-filtered import from the legacy RIT snapshot."""

import json
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

SNAPSHOT_NAME = 'rit_data_v2.json'
MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_SNAPSHOT_ROWS = 5_000
MAX_IMPORT_RECORDS = 5
MAX_INTERESTS = 8
MAX_TEXT_LENGTH = 120
_PROFILE_PATH = re.compile(r'/computing/directory/[a-z0-9][a-z0-9-]*\Z')


def _short_text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError
    result = unicodedata.normalize('NFC', value).strip()
    if (
        not result
        or len(result) > MAX_TEXT_LENGTH
        or '@' in result
        or '://' in result
        or any(ord(char) < 32 or ord(char) == 127 for char in result)
        or '<' in result
        or '>' in result
    ):
        raise ValueError
    return result


def _profile_url(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        raise ValueError from None
    if (
        parts.scheme != 'https'
        or parts.hostname != 'www.rit.edu'
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
        or not _PROFILE_PATH.fullmatch(parts.path)
        or value != f'https://www.rit.edu{parts.path}'
    ):
        raise ValueError
    return value


def _normalize_profile(row: object) -> dict:
    if not isinstance(row, Mapping):
        raise TypeError
    name = _short_text(row.get('name'))
    origin = _profile_url(row.get('url'))
    raw_interests = row.get('research_interests')
    if not isinstance(raw_interests, list) or not raw_interests:
        raise ValueError
    interests = []
    seen = set()
    for raw_interest in raw_interests:
        interest = _short_text(raw_interest)
        if interest.casefold() not in seen:
            interests.append(interest)
            seen.add(interest.casefold())
    if not interests:
        raise ValueError
    interests = interests[:MAX_INTERESTS]
    return {
        'external_id': origin,
        'title': name,
        'text': f'RIT directory snapshot profile for {name}. Listed research interests: {"; ".join(interests)}.',
        'origin': origin,
        'version': 'rit_data_v2_snapshot',
        'kind': 'researcher',
        'evidence_kind': 'public',
        'is_public': True,
        'proposal_id': None,
        'metadata': {
            'identity_status': 'legacy_profile_snapshot',
            'profile_url': origin,
            'snapshot_source': SNAPSHOT_NAME,
            'research_interests': interests,
            'affiliation_currentness': 'not independently established',
            'text_rights': 'Name and listed research-interest terms only; source reuse is subject to operator review.',
        },
    }


def prepare_rit_snapshot(
    rows: object, limit: int = MAX_IMPORT_RECORDS
) -> tuple[list[dict], dict[str, int]]:
    """Return at most five deterministically selected, filtered profile records."""
    if type(limit) is not int or not 1 <= limit <= MAX_IMPORT_RECORDS:
        raise ValueError(
            f'Import limit must be an integer from 1 to {MAX_IMPORT_RECORDS}.'
        )
    if not isinstance(rows, list) or len(rows) > MAX_SNAPSHOT_ROWS:
        raise ValueError('Snapshot faculty data must be a bounded list.')

    eligible = {}
    rejected = 0
    duplicates = 0
    for row in rows:
        try:
            record = _normalize_profile(row)
        except (TypeError, ValueError):
            rejected += 1
            continue
        previous = eligible.get(record['external_id'])
        if previous is not None:
            if previous != record:
                raise ValueError(
                    'Snapshot has conflicting records for one profile URL.'
                )
            duplicates += 1
            continue
        eligible[record['external_id']] = record

    selected = [eligible[url] for url in sorted(eligible)[:limit]]
    return selected, {
        'scanned': len(rows),
        'eligible': len(eligible),
        'rejected': rejected,
        'duplicate_urls': duplicates,
        'selected': len(selected),
    }


def load_rit_snapshot(
    source_file: Path, limit: int = MAX_IMPORT_RECORDS
) -> tuple[list[dict], dict[str, int]]:
    """Read only the explicit, bounded snapshot file; never write to its source."""
    if source_file.name != SNAPSHOT_NAME or source_file.is_symlink():
        raise ValueError(f'Supply a regular {SNAPSHOT_NAME} file explicitly.')
    resolved = source_file.resolve(strict=True)
    if 'restricted' in (part.casefold() for part in resolved.parts):
        raise ValueError('Restricted-mode snapshots are not accepted by this importer.')
    if not resolved.is_file() or resolved.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError('Snapshot must be a regular file no larger than 32 MiB.')
    try:
        data = json.loads(resolved.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('Snapshot must contain valid UTF-8 JSON.') from None
    if not isinstance(data, Mapping) or not isinstance(data.get('faculty'), list):
        raise TypeError('Snapshot must contain a faculty list.')
    return prepare_rit_snapshot(data['faculty'], limit)
