"""Normalize manually reviewed opportunity data for the existing v2 API."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_IMPORT_RECORDS = 50
MAX_FILE_BYTES = 1_000_000
ELIGIBILITY_VALUES = frozenset({'unknown', 'eligible', 'ineligible'})


def _http_url(value: object) -> str | None:
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise TypeError('source_url must be an HTTP(S) URL or null.')
    try:
        parts = urlsplit(value)
    except ValueError:
        raise ValueError('source_url must be a valid HTTP(S) URL.') from None
    if (parts.scheme not in {'http', 'https'} or not parts.hostname
            or parts.username is not None or parts.password is not None):
        raise ValueError('source_url must be an HTTP(S) URL without credentials.')
    return value


def _deadline(value: object) -> str | None:
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise TypeError('deadline must be an ISO-8601 string or null.')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('deadline must be an ISO-8601 string with a timezone.') from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('deadline must include a timezone offset.')
    return parsed.isoformat()


def prepare_opportunities(rows: object, limit: int = MAX_IMPORT_RECORDS) -> list[dict]:
    """Return bounded API payloads, retaining unknown deadline and eligibility as unknown."""
    if type(limit) is not int or not 1 <= limit <= MAX_IMPORT_RECORDS:
        raise ValueError(f'limit must be an integer from 1 to {MAX_IMPORT_RECORDS}.')
    if not isinstance(rows, list) or len(rows) > MAX_IMPORT_RECORDS:
        raise ValueError(f'opportunities must be a list of at most {MAX_IMPORT_RECORDS} records.')

    prepared = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError('Each opportunity must be an object.')
        title = row.get('title')
        notes = row.get('notes', '')
        eligibility = row.get('eligibility', 'unknown')
        timezone = row.get('deadline_timezone')
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 300:
            raise ValueError('title must contain 1 to 300 non-whitespace characters.')
        if not isinstance(notes, str) or len(notes) > 10_000:
            raise ValueError('notes must be text no longer than 10,000 characters.')
        if not isinstance(eligibility, str) or eligibility not in ELIGIBILITY_VALUES:
            raise ValueError('eligibility must be unknown, eligible, or ineligible.')
        if timezone is not None:
            if not isinstance(timezone, str):
                raise ValueError('deadline_timezone must be an IANA timezone or null.')
            try:
                ZoneInfo(timezone)
            except (ZoneInfoNotFoundError, ValueError):
                raise ValueError('deadline_timezone must be a known IANA timezone.') from None

        source_url = _http_url(row.get('source_url'))
        deadline = _deadline(row.get('deadline'))
        identity = (title.strip().casefold(), source_url)
        if identity in seen:
            raise ValueError('opportunities must not contain duplicate title/source_url pairs.')
        seen.add(identity)
        prepared.append({
            'title': title.strip(),
            'source_url': source_url,
            'deadline': deadline,
            'deadline_timezone': timezone,
            'notes': notes,
            'eligibility': eligibility,
        })
    return prepared[:limit]


def load_opportunities(path: Path, limit: int = MAX_IMPORT_RECORDS) -> list[dict]:
    """Load a bounded, explicitly supplied JSON file without modifying it."""
    if path.is_symlink() or path.suffix.casefold() != '.json':
        raise ValueError('Supply a regular JSON file explicitly.')
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('Opportunity file must be a regular file no larger than 1 MB.')
    try:
        payload = json.loads(resolved.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('Opportunity file must contain valid UTF-8 JSON.') from None
    if not isinstance(payload, dict) or set(payload) != {'opportunities'}:
        raise ValueError('Opportunity file must contain only an opportunities list.')
    return prepare_opportunities(payload['opportunities'], limit)


def filter_opportunities(
    rows: list[dict],
    *,
    query: str = '',
    eligibility: str | None = None,
    deadline_before: datetime | None = None,
) -> list[dict]:
    """Filter normalized opportunity views; undated opportunities do not match a deadline bound."""
    if eligibility is not None and eligibility not in ELIGIBILITY_VALUES:
        raise ValueError('eligibility must be unknown, eligible, or ineligible.')
    if deadline_before is not None and (
        deadline_before.tzinfo is None or deadline_before.utcoffset() is None
    ):
        raise ValueError('deadline_before must include a timezone.')
    needle = query.casefold().strip()
    filtered = []
    for row in rows:
        if needle and needle not in f"{row.get('title', '')} {row.get('notes', '')}".casefold():
            continue
        if eligibility is not None and row.get('eligibility', 'unknown') != eligibility:
            continue
        if deadline_before is not None:
            raw_deadline = row.get('deadline')
            if raw_deadline is None:
                continue
            deadline = datetime.fromisoformat(raw_deadline.replace('Z', '+00:00'))
            if deadline >= deadline_before:
                continue
        filtered.append(row)
    return filtered
