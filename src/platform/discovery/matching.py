"""Evidence-backed lexical collaborator leads over current public profiles."""

import re
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.models import Source
from ..database.public_records import PublicRecord

_PROFILE_STATUSES = frozenset({'official_profile', 'legacy_profile_snapshot'})
_RIT_DIRECTORY_PATH = re.compile(r'/computing/directory/[a-z0-9][a-z0-9-]*\Z')
_TOKEN = re.compile(r'[^\W_]+', re.UNICODE)
_STOP_WORDS = frozenset(
    [
        'a',
        'an',
        'and',
        'are',
        'as',
        'at',
        'be',
        'by',
        'can',
        'could',
        'for',
        'from',
        'how',
        'in',
        'is',
        'it',
        'me',
        'of',
        'on',
        'or',
        'our',
        'please',
        'that',
        'the',
        'this',
        'to',
        'use',
        'using',
        'was',
        'were',
        'with',
        'we',
        'you',
        'your',
    ]
)
_ALIASES = (
    ('ai', ('ai',), ('artificial', 'intelligence')),
    ('ml', ('ml',), ('machine', 'learning')),
    ('nlp', ('nlp',), ('natural', 'language', 'processing')),
    ('rag', ('rag',), ('retrieval', 'augmented', 'generation')),
)


def _tokens(text: str) -> list[str]:
    return [
        token.casefold()
        for token in _TOKEN.findall(text)
        if token.casefold() not in _STOP_WORDS
    ]


def _contains_phrase(tokens: list[str], phrase: tuple[str, ...]) -> bool:
    return any(
        tuple(tokens[index : index + len(phrase)]) == phrase
        for index in range(len(tokens) - len(phrase) + 1)
    )


def _idea_concepts(
    tokens: list[str],
) -> tuple[dict[str, tuple[frozenset[str], ...]], set[str]]:
    concepts: dict[str, tuple[frozenset[str], ...]] = {}
    alias_labels: set[str] = set()
    consumed: set[str] = set()
    for abbreviation, short_form, long_form in _ALIASES:
        short_present = _contains_phrase(tokens, short_form)
        long_present = _contains_phrase(tokens, long_form)
        if not short_present and not long_present:
            continue
        label = ' '.join(long_form) if long_present else abbreviation.upper()
        variants = (short_form, long_form)
        if not short_present:
            variants = (long_form, short_form)
        concepts[label] = tuple(frozenset(variant) for variant in variants)
        consumed.update(short_form if short_present else ())
        consumed.update(long_form if long_present else ())
        if short_present:
            alias_labels.add(label)

    for token in tokens:
        if token not in consumed:
            concepts.setdefault(token, (frozenset({token}),))
    return concepts, alias_labels


def _matched_evidence(
    variants: tuple[frozenset[str], ...], source_terms: set[str]
) -> frozenset[str] | None:
    return next(
        (variant for variant in variants if variant.issubset(source_terms)), None
    )


def _official_rit_profile(origin: str) -> bool:
    try:
        parts = urlsplit(origin)
        return (
            parts.scheme == 'https'
            and parts.hostname == 'www.rit.edu'
            and parts.username is None
            and parts.password is None
            and parts.port is None
            and not parts.query
            and not parts.fragment
            and _RIT_DIRECTORY_PATH.fullmatch(parts.path) is not None
            and origin == f'https://www.rit.edu{parts.path}'
        )
    except ValueError:
        return False


def _profile_kind(record: PublicRecord, source: Source) -> str | None:
    if record.evidence_kind == 'synthetic':
        return 'synthetic_example'
    metadata = record.metadata_json
    identity_status = (
        metadata.get('identity_status') if isinstance(metadata, dict) else None
    )
    if (
        record.evidence_kind == 'public'
        and identity_status in _PROFILE_STATUSES
        and _official_rit_profile(source.origin)
    ):
        return (
            'snapshot_profile'
            if identity_status == 'legacy_profile_snapshot'
            else 'public_profile'
        )
    return None


def _profile_terms(
    record: PublicRecord, source: Source, candidate_status: str
) -> set[str]:
    if candidate_status == 'synthetic_example':
        return set(_tokens(source.title + ' ' + source.text))

    metadata = record.metadata_json
    if isinstance(metadata, dict):
        for field in ('expertise', 'research_interests'):
            values = metadata.get(field)
            if (
                isinstance(values, list)
                and values
                and all(isinstance(value, str) for value in values)
            ):
                return set(_tokens(' '.join(values)))

    for marker in (
        'Listed areas of expertise:',
        'Listed research interests:',
        'Listed expertise:',
    ):
        if marker in source.text:
            return set(_tokens(source.text.split(marker, 1)[1]))
    return set(_tokens(source.text))


def _match_reason(
    candidate_status: str,
    matched_terms: list[str],
    evidence_terms: list[str],
    alias_labels: set[str],
) -> str:
    if candidate_status == 'synthetic_example':
        return (
            'Synthetic example only; it is not a real person. Overlapping profile '
            f'terms: {", ".join(evidence_terms)}.'
        )
    reason = f'Listed profile facts contain: {", ".join(evidence_terms)}.'
    expanded = sorted(set(matched_terms) & alias_labels)
    if expanded:
        reason += (
            ' Fixed abbreviation expansion used for '
            + ', '.join(expanded)
            + '; this is not semantic matching.'
        )
    if candidate_status == 'snapshot_profile':
        reason += ' This is a directory snapshot; profile currentness is unknown.'
    return reason + ' Keyword overlap only; availability is unknown.'


def match_collaborators(session: Session, idea: str, limit: int = 5) -> dict:
    if not isinstance(idea, str) or len(idea) > 1000:
        raise ValueError('Use a research idea no longer than 1000 characters.')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('Use an integer match limit from 1 to 20.')

    tokens = _tokens(idea)
    concepts, alias_labels = _idea_concepts(tokens)

    statement = (
        select(Source, PublicRecord)
        .join(PublicRecord, PublicRecord.source_id == Source.id)
        .where(
            PublicRecord.is_current.is_(True),
            PublicRecord.kind == 'researcher',
            Source.is_public.is_(True),
            Source.proposal_id.is_(None),
        )
    )
    records = session.execute(statement).all()
    matches = []
    covered_profile_terms: set[str] = set()
    eligible_profile_count = 0

    for source, record in records:
        candidate_status = _profile_kind(record, source)
        if candidate_status is None:
            continue
        source_terms = _profile_terms(record, source, candidate_status)
        if candidate_status in {'public_profile', 'snapshot_profile'}:
            eligible_profile_count += 1
            for label, variants in concepts.items():
                if _matched_evidence(variants, source_terms) is not None:
                    covered_profile_terms.add(label)

        matched_terms = sorted(
            label
            for label, variants in concepts.items()
            if _matched_evidence(variants, source_terms) is not None
        )
        if not matched_terms:
            continue

        evidence_terms = sorted(
            {
                term
                for label in matched_terms
                for term in _matched_evidence(concepts[label], source_terms) or ()
            }
        )
        coverage_score = round(len(matched_terms) / len(concepts), 6)
        matches.append(
            {
                'source_id': source.id,
                'version': source.version,
                'content_hash': source.content_hash,
                'title': source.title,
                'snippet': source.text[:280],
                'origin': source.origin,
                'kind': record.kind,
                'evidence_kind': record.evidence_kind,
                'identity_status': (
                    record.metadata_json.get('identity_status')
                    if isinstance(record.metadata_json, dict)
                    else None
                ),
                'candidate_status': candidate_status,
                'matched_terms': matched_terms,
                'evidence_terms': evidence_terms,
                'idea_coverage': coverage_score,
                'reason': _match_reason(
                    candidate_status, matched_terms, evidence_terms, alias_labels
                ),
            }
        )

    matches.sort(
        key=lambda item: (
            -item['idea_coverage'],
            -len(item['evidence_terms']),
            item['candidate_status'] == 'synthetic_example',
            item['title'].casefold(),
            item['source_id'],
        )
    )
    uncovered_terms = [
        label for label in concepts if label not in covered_profile_terms
    ]
    return {
        'items': matches[:limit],
        'degraded': True,
        'method': 'keyword_overlap',
        'coverage': {
            'eligible_profile_count': eligible_profile_count,
            'matching_profile_count': sum(
                item['candidate_status'] in {'public_profile', 'snapshot_profile'}
                for item in matches
            ),
            'uncovered_terms': uncovered_terms,
            'note': (
                'Coverage describes only currently imported canonical RIT directory profiles; '
                'a gap does not mean no researcher works on that topic.'
                if concepts
                else 'No searchable idea terms were provided.'
            ),
        },
        'next_cursor': None,
    }
