"""Validate citation identities and verbatim support, not semantic entailment."""

import json
import re

from .types import Citation, DraftError, SourceSnapshot


INSUFFICIENT_EVIDENCE = 'Insufficient evidence in the selected sources to draft this section.'


def parse_citations(raw: str, sources: tuple[SourceSnapshot, ...]) -> tuple[str, tuple[Citation, ...], bool]:
    try:
        value = json.loads(raw)
        text, references, insufficient = value['text'], value['citations'], value['insufficient_evidence']
        if not isinstance(text, str) or not isinstance(references, list) or type(insufficient) is not bool:
            raise ValueError
        if insufficient:
            if references:
                raise ValueError
            return INSUFFICIENT_EVIDENCE, (), True
        if not text.strip() or not references:
            raise ValueError
        selected = {source.id: source for source in sources}
        citations = []
        seen = set()
        for reference in references:
            source = selected[reference['source_id']]
            quote = reference['quote']
            if (not isinstance(quote, str) or not quote.strip() or len(quote) > 1000
                    or quote not in source.text or source.id in seen):
                raise ValueError
            seen.add(source.id)
            citations.append(Citation(source.id, source.version, source.content_hash,
                                      source.title, source.origin, quote))
        markers = set(re.findall(r'\[([^\[\]\n]+)\]', text))
        if markers != seen:
            raise ValueError
        return text, tuple(citations), False
    except (ValueError, TypeError, KeyError, IndexError, RecursionError):
        raise DraftError('invalid_citations', 'Draft did not contain valid selected-source citations.') from None
