"""Three allowlisted official profiles, retaining only short structured facts."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import math
from urllib.request import HTTPRedirectHandler, Request, build_opener


PROFILE_URLS = tuple('https://www.rit.edu/computing/directory/' + slug for slug in (
    'cmhvcs-christopher-homan', 'rxzvcs-richard-zanibbi', 'zxbvcs-zachary-butler'))
EXPECTED_NAMES = dict(zip(PROFILE_URLS, ('Christopher Homan', 'Richard Zanibbi', 'Zachary Butler')))
MAX_BODY = 2 * 1024 * 1024


class _Node:
    def __init__(self, tag, parent=None):
        self.tag, self.parent, self.children = tag, parent, []

    def text(self):
        return ' '.join(' '.join(child.text() if isinstance(child, _Node) else child for child in self.children).split())

    def nodes(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.nodes()


class _ProfileParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node('root')
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, self.current)
        self.current.children.append(node)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
            self.current = node

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, value):
        if self.current.tag not in ('script','style','noscript'):
            self.current.children.append(value)


def parse_profile(html: str, url: str, fetched_at: str) -> dict:
    if url not in PROFILE_URLS or not isinstance(html, str) or len(html.encode('utf-8')) > MAX_BODY:
        raise ValueError('Use a bounded allowlisted official profile.')
    parser = _ProfileParser()
    try:
        parser.feed(html)
        nodes = list(parser.root.nodes())
        names = {node.text() for node in nodes if node.tag == 'h1' and node.text()}
        if len(names) != 1:
            raise ValueError
        name = names.pop()
        if name != EXPECTED_NAMES[url]:
            raise ValueError
        headings = [node for node in nodes if node.text().casefold().rstrip(':') == 'areas of expertise'
                    and node.tag in ('div','h2','h3','h4')]
        areas = []
        for heading in headings:
            siblings = heading.parent.children
            position = siblings.index(heading)
            group = next((node for node in siblings[position+1:] if isinstance(node, _Node)), None)
            if group is None or group.tag not in ('div','ul','ol'):
                continue
            # The official directory places one div group directly after the
            # expertise label. Also support a directly following semantic list.
            # Never consume earlier lists or subsequent page sections.
            for item in group.children:
                if isinstance(item, _Node) and ((group.tag in ('ul','ol') and item.tag == 'li')
                                                or (group.tag == 'div' and item.tag == 'div')):
                    value = item.text()
                    if value and value not in areas:
                        if len(value) > 70 or len(value.split()) > 8 or '@' in value or '://' in value:
                            raise ValueError
                        areas.append(value)
        if not areas:
            raise ValueError
        areas = areas[:6]
        departments = {node.text() for node in nodes if node.text().startswith('Department of ')
                       and len(node.text()) <= 100 and len(node.text().split()) <= 12
                       and '@' not in node.text() and '://' not in node.text()}
        department = next(iter(departments)) if len(departments) == 1 else None
    except (ValueError, RecursionError):
        raise ValueError('Official profile is missing an unambiguous name or structured expertise keywords.') from None
    text = f'Official RIT profile: {name}. '
    if department:
        text += f'Listed department: {department}. '
    text += 'Listed areas of expertise: ' + '; '.join(areas) + '.'
    return dict(external_id=url, title=name, text=text, origin=url, kind='researcher',
                evidence_kind='public', is_public=True, proposal_id=None,
                metadata=dict(identity_status='official_profile', profile_url=url, name=name,
                              department=department, expertise=areas, fetched_at=fetched_at,
                              text_rights='Name, listed department and short expertise facts only; no biography or contact information retained.',
                              availability='unknown', affiliation_currentness='not independently established'))


class ProfileRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Profile redirects are disabled; canonical provenance must match the allowlist.')


def fetch_profiles(urls=PROFILE_URLS, timeout_s: float = 15) -> list[dict]:
    urls = tuple(dict.fromkeys(urls))
    if (not 1 <= len(urls) <= 3 or any(url not in PROFILE_URLS for url in urls)
            or type(timeout_s) not in (int,float) or not 0 < timeout_s <= 15 or not math.isfinite(timeout_s)):
        raise ValueError('Fetch one to three fixed official profiles with a timeout up to 15 seconds.')
    opener = build_opener(ProfileRedirectHandler())
    records = []
    for url in urls:
        request = Request(url, headers={'User-Agent':'ResearchCircle/0.1 (bounded official profile facts)', 'Accept':'text/html'})
        with opener.open(request, timeout=timeout_s) as response:
            if response.geturl() != url:
                raise ValueError('Official profile provenance changed.')
            body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise ValueError('Official profile exceeded the response limit.')
        records.append(parse_profile(body.decode('utf-8'), url, datetime.now(timezone.utc).isoformat()))
    return records
