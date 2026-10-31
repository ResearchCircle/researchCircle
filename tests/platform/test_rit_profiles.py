import unittest
import contextlib
import io
from unittest.mock import patch
from src.platform.ingestion.rit_profiles import PROFILE_URLS, parse_profile, fetch_profiles, ProfileRedirectHandler
from src.platform.ingestion.public_store import import_public_records
from src.platform.database import Database
from src.platform.database.models import Source
from src.platform.database.public_records import PublicRecord
from src.platform.discovery.public_search import search_public
from sqlalchemy import select


HTML='''<html><head><meta name="description" content="PRIVATE BIO CONTACT"></head><body>
<h1>Christopher Homan</h1><p>Department of Computing</p><p>Long expressive biography. contact@example.test</p>
<section><h2>Areas of Expertise</h2><ul><li>Machine learning</li><li>Information retrieval</li></ul></section>
<h2>Currently Teaching</h2><p>Unrelated course and contact information</p></body></html>'''


class RitProfileTests(unittest.TestCase):
    def test_cli_configuration_error_is_sanitized_before_network(self):
        from services.api.import_rit import main
        output=io.StringIO()
        with (patch('services.api.import_rit.Database', side_effect=ValueError('PRIVATE DATABASE CREDENTIAL')),
             patch('services.api.import_rit.fetch_profiles') as fetch,
             contextlib.redirect_stderr(output)):
            self.assertEqual(main(),1)
        fetch.assert_not_called()
        self.assertNotIn('PRIVATE',output.getvalue())

    def test_official_directory_div_keyword_structure(self):
        html='''<h1>Christopher Homan</h1><div><div>Areas of Expertise</div>
        <div><div>Machine learning</div><div>Information retrieval</div></div></div>
        <div>Teaching and other unrelated material</div>'''
        self.assertEqual(parse_profile(html,PROFILE_URLS[0],'date')['metadata']['expertise'],
                         ['Machine learning','Information retrieval'])

    def test_only_short_official_keyword_facts_are_retained(self):
        row=parse_profile(HTML,PROFILE_URLS[0],'2026-10-31T00:00:00Z')
        self.assertEqual(row['title'],'Christopher Homan')
        self.assertEqual(row['external_id'],PROFILE_URLS[0])
        self.assertEqual(row['origin'],PROFILE_URLS[0])
        self.assertEqual(row['metadata']['identity_status'],'official_profile')
        self.assertEqual(row['metadata']['department'],'Department of Computing')
        self.assertEqual(row['metadata']['expertise'],['Machine learning','Information retrieval'])
        self.assertNotIn('Long expressive biography',str(row))
        self.assertNotIn('contact@example',str(row))
        self.assertNotIn('PRIVATE',str(row))
        self.assertNotIn('Currently Teaching',row['text'])

    def test_missing_or_ambiguous_profile_fails_closed(self):
        for html in [HTML.replace('<h1>Christopher Homan</h1>',''), HTML.replace('Areas of Expertise','Bio'),
                     HTML.replace('<li>Machine learning</li><li>Information retrieval</li>',''),
                     HTML.replace('Christopher Homan','Other Researcher'),
                     HTML+'<h1>Someone Else</h1>']:
            with self.subTest(html=html),self.assertRaises(ValueError):parse_profile(html,PROFILE_URLS[0],'date')
        with self.assertRaises(ValueError):parse_profile(HTML,'https://other.example/profile','date')

    def test_other_lists_outside_immediate_expertise_group_are_excluded(self):
        html='''<main><h1>Christopher Homan</h1><ul><li>UNRELATED BEFORE</li></ul>
        <h2>Areas of Expertise</h2><ul><li>Machine learning</li></ul>
        <h2>Other section</h2><ul><li>UNRELATED AFTER</li></ul></main>'''
        row=parse_profile(html,PROFILE_URLS[0],'date')
        self.assertEqual(row['metadata']['expertise'],['Machine learning'])
        self.assertNotIn('UNRELATED',str(row))

    def test_fetched_at_does_not_change_snapshot_and_identity_status_is_exposed(self):
        db=Database('sqlite://')
        db.create_schema()
        try:
            with db.session_factory() as session:
                first=parse_profile(HTML,PROFILE_URLS[0],'2026-10-31T00:00:00Z')
                second=parse_profile(HTML,PROFILE_URLS[0],'2026-11-01T00:00:00Z')
                self.assertEqual(first['text'],second['text'])
                self.assertEqual(import_public_records(session,[first])['inserted'],1)
                self.assertEqual(import_public_records(session,[second])['unchanged'],1)
                self.assertEqual(len(session.scalars(select(Source)).all()),1)
                self.assertEqual(search_public(session,'retrieval')['items'][0]['identity_status'],'official_profile')
        finally:db.engine.dispose()

    def test_fixed_allowlist_redirect_and_body_bounds(self):
        with patch('src.platform.ingestion.rit_profiles.build_opener') as build:
            for urls,timeout in [([],15),(['https://private.example'],15),(PROFILE_URLS,16),(PROFILE_URLS,0)]:
                with self.assertRaises(ValueError):fetch_profiles(urls,timeout)
            build.assert_not_called()
            response=build.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value=PROFILE_URLS[0]
            response.read.return_value=b'x'*(2*1024*1024+1)
            with self.assertRaises(ValueError):fetch_profiles([PROFILE_URLS[0]])
            response.read.return_value=HTML.encode()
            response.geturl.return_value='https://private.example'
            with self.assertRaises(ValueError):fetch_profiles([PROFILE_URLS[0]])
        with self.assertRaises(ValueError):ProfileRedirectHandler().redirect_request(None,None,302,'',{},'https://private.example')
