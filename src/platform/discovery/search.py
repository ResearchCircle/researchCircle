"""Deterministic keyword search over explicitly public/sample records.

The legacy HybridRetriever was inspected: its module imports NumPy, rank_bm25
and VectorStore; the matcher also initializes configuration/graph dependencies.
This small degraded adapter deliberately imports none of those modules. It does
not claim BM25, embeddings, semantic similarity or graph-based matching.
"""

import re
from collections.abc import Iterable, Mapping

from ..ingestion.import_public import import_records
from .samples import SAMPLE_RECORDS


_TOKEN = re.compile(r'[^\W_]+', re.UNICODE)
_STOP_WORDS = frozenset('a an and are as at be by for from in is it of on or that the this to was were with'.split())


def _terms(text: str) -> set[str]:
    return {term for token in _TOKEN.findall(text) if (term := token.casefold()) not in _STOP_WORDS}


class SampleSearch:
    """Pure lexical fallback. Proposal-scoped input is rejected before indexing."""

    def __init__(self, records: Iterable[Mapping]):
        self._rows = tuple(import_records(records))

    def list_samples(self) -> list[dict]:
        return [dict(row) for row in self._rows]

    def search(self, query: str, limit: int = 10) -> dict:
        if not isinstance(query, str):
            raise ValueError('Search query must be a string.')
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Search limit must be an integer from 1 to 100.')
        terms = _terms(query)
        matches = []
        if terms:
            for source in self._rows:
                title_matches = terms & _terms(source['title'])
                text_matches = terms & _terms(source['text'])
                matched = title_matches | text_matches
                if not matched:
                    continue
                row = dict(source)
                row['score'] = round((len(matched) + .25 * len(title_matches)) / len(terms), 6)
                row['reason'] = f'Keyword match: {", ".join(sorted(matched))}. Lexical ranking only; no semantic retrieval.'
                positions = [match.start() for match in _TOKEN.finditer(row['text'])
                             if match.group().casefold() in matched]
                start = max(0, min(positions) - 65) if positions else 0
                row['snippet'] = row['text'][start:start + 280]
                matches.append(row)
        matches.sort(key=lambda row: (-row['score'], row['id']))
        return {'items': matches[:limit], 'degraded': True, 'next_cursor': None}


_DEFAULT = SampleSearch(SAMPLE_RECORDS)


def list_samples() -> list[dict]:
    """Return fresh source rows for explicit public-source database seeding."""
    return _DEFAULT.list_samples()


def search(query: str, limit: int = 10) -> dict:
    """Return deterministic source-linked sample results; never search private data."""
    return _DEFAULT.search(query, limit)
