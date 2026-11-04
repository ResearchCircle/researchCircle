"""Database-backed hybrid BM25 and dense semantic retrieval over public records."""

from rank_bm25 import BM25Okapi
from sqlalchemy import select

from ..database.models import Source
from ..database.public_records import PublicRecord
from .search import _STOP_WORDS, _TOKEN
from .semantic import SemanticVectorizer, reciprocal_rank_fusion

_VECTORIZER = SemanticVectorizer(dim=256)


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN.findall(text) if token.casefold() not in _STOP_WORDS]


def search_public(session, query: str, limit: int = 10, kind: str | None = None, semantic: bool = False) -> dict:
    """Execute search over public records.

    If `semantic=True`, executes hybrid retrieval combining BM25 keyword matching
    and dense semantic vector ranking with Reciprocal Rank Fusion (RRF), setting `degraded: False`.
    If `semantic=False` (default BM25 mode), returns BM25 ranking with `degraded: True`.
    """
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
        return {'items': [], 'degraded': not semantic, 'next_cursor': None}

    corpus = [_tokens(source.title + ' ' + source.title + ' ' + source.text) or [''] for source, _ in entries]
    ranker = BM25Okapi(corpus)
    ranker.idf = {term: max(weight, .01) for term, weight in ranker.idf.items()}
    bm25_scores = ranker.get_scores(terms)

    if not semantic:
        # Standard BM25-only retrieval mode
        items = []
        for (source, metadata), tokens, score in zip(entries, corpus, bm25_scores):
            matched = set(tokens) & set(terms)
            if not matched:
                continue
            positions = [m.start() for m in _TOKEN.finditer(source.text) if m.group().casefold() in matched]
            start = max(0, min(positions) - 65) if positions else 0
            items.append(dict(
                id=source.id, source_id=source.id, version=source.version, content_hash=source.content_hash,
                title=source.title, snippet=source.text[start:start+280], origin=source.origin, text=source.text,
                score=round(float(score), 6), reason='BM25 keyword match: ' + ', '.join(sorted(matched)) + '. Semantic retrieval unavailable.',
                kind=metadata.kind, evidence_kind=metadata.evidence_kind,
                **({'identity_status': metadata.metadata_json['identity_status']}
                   if metadata.metadata_json.get('identity_status') else {})
            ))
        items.sort(key=lambda row: (-row['score'], row['id']))
        return {'items': items[:limit], 'degraded': True, 'next_cursor': None}

    # Hybrid Semantic + BM25 Mode (semantic=True)
    bm25_ranked = []
    for (source, _), raw_score in zip(entries, bm25_scores):
        if raw_score > 0:
            bm25_ranked.append((source.id, float(raw_score)))
    bm25_ranked.sort(key=lambda x: -x[1])
    bm25_ranked_ids = [doc_id for doc_id, _ in bm25_ranked]

    # Semantic Vector scoring
    query_vec = _VECTORIZER.encode(query)
    semantic_scores = {}
    for source, _ in entries:
        doc_text = f"{source.title}. {source.text}"
        doc_vec = _VECTORIZER.encode(doc_text)
        sim = _VECTORIZER.similarity(query_vec, doc_vec)
        if sim >= 0.18:  # Strict relevance threshold to avoid false positives
            semantic_scores[source.id] = sim

    semantic_ranked = sorted(semantic_scores.items(), key=lambda x: -x[1])
    semantic_ranked_ids = [doc_id for doc_id, _ in semantic_ranked]

    rrf_scores = reciprocal_rank_fusion(bm25_ranked_ids, semantic_ranked_ids, rrf_k=60)

    items = []
    for (source, metadata), tokens in zip(entries, corpus):
        if source.id not in rrf_scores:
            continue

        matched = set(tokens) & set(terms)
        sim = semantic_scores.get(source.id, 0.0)
        score = rrf_scores[source.id]

        positions = [m.start() for m in _TOKEN.finditer(source.text) if m.group().casefold() in matched]
        start = max(0, min(positions) - 65) if positions else 0

        if matched and sim >= 0.18:
            reason = (
                f"BM25 & Semantic hybrid match (RRF score: {score:.4f}, semantic similarity: {sim:.2f}). "
                f"Matched terms: {', '.join(sorted(matched))}."
            )
        elif matched:
            reason = f"BM25 keyword match: {', '.join(sorted(matched))}. RRF score: {score:.4f}."
        else:
            reason = f"Semantic conceptual match (similarity: {sim:.2f}, RRF score: {score:.4f})."

        items.append(dict(
            id=source.id,
            source_id=source.id,
            version=source.version,
            content_hash=source.content_hash,
            title=source.title,
            snippet=source.text[start:start+280],
            origin=source.origin,
            text=source.text,
            score=round(float(score), 6),
            reason=reason,
            kind=metadata.kind,
            evidence_kind=metadata.evidence_kind,
            **({'identity_status': metadata.metadata_json['identity_status']}
               if metadata.metadata_json.get('identity_status') else {})
        ))

    items.sort(key=lambda row: (-row['score'], row['id']))
    return {'items': items[:limit], 'degraded': False, 'next_cursor': None}
