"""Validate citation identities and verbatim support, not semantic entailment."""

import json
import re

from .types import Citation, DraftError, SourceSnapshot


INSUFFICIENT_EVIDENCE = 'Insufficient evidence in the selected sources to draft this section.'


def parse_citations(raw: str, sources: tuple[SourceSnapshot, ...]) -> tuple[str, tuple[Citation, ...], bool]:
    try:
        value = json.loads(raw)
    except (ValueError, TypeError, RecursionError):
        raise DraftError('invalid_citations', 'Draft response was not valid citation JSON.') from None
    if not isinstance(value, dict):
        raise DraftError('invalid_citations', 'Draft citation response had missing or invalid fields.')
    text, references, insufficient = value.get('text'), value.get('citations'), value.get('insufficient_evidence')
    if not isinstance(text, str) or not isinstance(references, list) or type(insufficient) is not bool:
        raise DraftError('invalid_citations', 'Draft citation response had missing or invalid fields.')
    if insufficient:
        if references:
            raise DraftError('invalid_citations', 'Draft reported insufficient evidence but also returned citations.')
        return INSUFFICIENT_EVIDENCE, (), True
    if not text.strip() or not references:
        raise DraftError('invalid_citations', 'Draft returned no cited text or supporting references.')
    selected = {source.id: source for source in sources}
    citations = []
    seen = set()
    for reference in references:
        if not isinstance(reference, dict) or not isinstance(reference.get('source_id'), str):
            raise DraftError('invalid_citations', 'Draft citation reference had missing or invalid fields.')
        source_id = reference['source_id']
        if source_id not in selected:
            raise DraftError('invalid_citations', 'Draft cited a source that was not selected.')
        if source_id in seen:
            raise DraftError('invalid_citations', 'Draft returned duplicate references for a cited source.')
        source = selected[source_id]
        quote = reference.get('quote')
        if not isinstance(quote, str) or not quote.strip() or len(quote) > 1000:
            raise DraftError('invalid_citations', 'Draft support quote must be short, nonempty text.')
        if quote not in source.text:
            raise DraftError('invalid_citations', 'Draft support quote did not exactly match its selected source.')
        seen.add(source.id)
        citations.append(Citation(source.id, source.version, source.content_hash,
                                  source.title, source.origin, quote))
    markers = set(re.findall(r'\[([^\[\]\n]+)\]', text))
    if markers != seen:
        raise DraftError('invalid_citations', 'Draft inline citations did not match its supporting references.')
    return text, tuple(citations), False
