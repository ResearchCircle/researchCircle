"""Bounded anonymous Crossref DOI metadata import; never downloads paper text."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_DOIS = ('10.1038/nature14539', '10.1016/j.comnet.2010.05.010', '10.1561/1500000019')


def normalize_crossref(message: dict, fetched_at: str) -> dict:
    doi = message['DOI'].lower()
    titles = message.get('title', [])
    if not re.fullmatch(r'10\.\d{4,9}/\S+', doi) or not titles or not isinstance(titles[0], str):
        raise ValueError('Crossref did not return a valid DOI/title.')
    title = titles[0]
    authors = [' '.join(part for part in (person.get('given', ''), person.get('family', '')) if part)
               for person in message.get('author', [])]
    authors = [name for name in authors if name]
    date = message.get('published', {}).get('date-parts', [[]])[0]
    year = date[0] if date and type(date[0]) is int else None
    # Title and bibliographic facts only. TDM license links do not establish an
    # open abstract license, so no abstract/full-paper text is copied or inferred.
    text = f'Title: {title}. Authors: {"; ".join(authors) if authors else "not supplied"}. '
    text += f'Publication year: {year if year else "unknown"}. DOI: {doi}.'
    return dict(external_id='doi:' + doi, title=title, text=text, origin='https://doi.org/' + doi,
                kind='paper', evidence_kind='public', is_public=True, proposal_id=None,
                metadata=dict(doi=doi, authors=authors, year=year, fetched_at=fetched_at,
                              provider='Crossref REST API', metadata_url='https://api.crossref.org/works/' + quote(doi, safe=''),
                              publisher_license_links=message.get('license', []), abstract_included=False,
                              text_rights='Bibliographic facts only; abstract/full-text reuse license not established.'))


def authorship_entries(paper: dict, limit: int = 10) -> list[dict]:
    """Listed authorship facts, never resolved faculty identities or profiles."""
    records = []
    metadata = paper['metadata']
    for index, name in enumerate(metadata['authors'][:limit]):
        text = (f"Listed author: {name}. Publication: {paper['title']}. "
                f"Publication year: {metadata['year'] if metadata['year'] else 'unknown'}. DOI: {metadata['doi']}. "
                'This is a publication authorship entry; researcher identity, current affiliation and contact details are unresolved.')
        records.append(dict(external_id=paper['external_id'] + f'#author:{index}',
                            title=f"Listed author: {name} — {paper['title']}", text=text, origin=paper['origin'],
                            kind='researcher', evidence_kind='public', is_public=True, proposal_id=None,
                            metadata={**metadata, 'author_name': name, 'author_position': index,
                                      'identity_status': 'authorship_entry_unresolved',
                                      'paper_external_id': paper['external_id']}))
    return records


def fetch_crossref(dois=DEFAULT_DOIS, timeout_s: float = 15) -> list[dict]:
    dois = tuple(dict.fromkeys(dois))
    if not 1 <= len(dois) <= 5 or not 0 < timeout_s <= 30:
        raise ValueError('Fetch one to five DOI records with a timeout up to 30 seconds.')
    results = []
    remaining_authors = 10
    for doi in dois:
        if not isinstance(doi, str) or not re.fullmatch(r'10\.\d{4,9}/\S{1,900}', doi):
            raise ValueError('Invalid DOI.')
        url = 'https://api.crossref.org/works/' + quote(doi, safe='')
        request = Request(url, headers={'User-Agent': 'ResearchCircle/0.1 (bounded public metadata import)', 'Accept': 'application/json'})
        with urlopen(request, timeout=timeout_s) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Crossref metadata exceeded its size limit.')
        message = json.loads(raw)['message']
        if message.get('DOI', '').casefold() != doi.casefold():
            raise ValueError('Crossref returned metadata for another DOI.')
        paper = normalize_crossref(message, datetime.now(timezone.utc).isoformat())
        results.append(paper)
        authors = authorship_entries(paper, remaining_authors)
        results.extend(authors)
        remaining_authors -= len(authors)
    return results
