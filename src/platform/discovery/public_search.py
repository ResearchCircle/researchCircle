"""Database-backed BM25 retrieval; vectors/semantic ranking remain unavailable."""
from rank_bm25 import BM25Okapi
from sqlalchemy import select

from ..database.models import Source
from ..database.public_records import PublicRecord
from .search import _STOP_WORDS, _TOKEN


def _tokens(text):
    return [token.casefold() for token in _TOKEN.findall(text) if token.casefold() not in _STOP_WORDS]


def search_public(session, query: str, limit: int = 10, kind: str | None = None) -> dict:
    if (not isinstance(query, str) or type(limit) is not int or not 1 <= limit <= 100
            or kind not in (None, 'paper', 'researcher')):
        raise ValueError('Use a string query, an integer limit from 1 to 100, and a valid optional source kind.')
    terms = _tokens(query)
    statement = select(Source, PublicRecord).join(
        PublicRecord, PublicRecord.source_id == Source.id
    ).where(
        PublicRecord.is_current.is_(True),
        Source.is_public.is_(True),
        Source.proposal_id.is_(None),
    )
    if kind is not None:
        statement = statement.where(PublicRecord.kind == kind)
    entries = session.execute(statement).all()
    if not terms or not entries:
        return {'items': [], 'degraded': True, 'next_cursor': None}
    corpus = [_tokens(source.title + ' ' + source.title + ' ' + source.text) or [''] for source, _ in entries]
    # Same reviewed BM25Okapi engine as HybridRetriever; no VectorStore/config import.
    # Positive epsilon avoids losing common-term matches in very small corpora.
    ranker = BM25Okapi(corpus)
    ranker.idf = {term: max(weight, .01) for term, weight in ranker.idf.items()}
    scores = ranker.get_scores(terms)
    items = []
    for (source, metadata), tokens, score in zip(entries, corpus, scores):
        matched = set(tokens) & set(terms)
        if not matched:
            continue
        positions = [m.start() for m in _TOKEN.finditer(source.text) if m.group().casefold() in matched]
        start = max(0, min(positions) - 65) if positions else 0
        items.append(dict(id=source.id, source_id=source.id, version=source.version, content_hash=source.content_hash,
                          title=source.title, snippet=source.text[start:start+280], origin=source.origin, text=source.text,
                          score=round(float(score), 6), reason='BM25 keyword match: ' + ', '.join(sorted(matched)) + '. Semantic retrieval unavailable.',
                          kind=metadata.kind, evidence_kind=metadata.evidence_kind,
                          **({'identity_status': metadata.metadata_json['identity_status']}
                             if metadata.metadata_json.get('identity_status') else {})))
    items.sort(key=lambda row: (-row['score'], row['id']))
    return {'items': items[:limit], 'degraded': True, 'next_cursor': None}
