import unittest
import json
import hashlib
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import select
from src.platform.database import Database
from src.platform.database.models import Source
from src.platform.database.public_records import PublicRecord
from src.platform.ingestion.public_store import import_public_records
from src.platform.discovery.public_search import search_public
from services.api.routes.search import seed_samples


def record(**updates):
    return dict(external_id='doi:10.example/sensors', title='Synthetic paper: Sensor sampling',
                text='Synthetic temperature sensor sampling at ten minute intervals.', origin='Synthetic test fixture',
                version='v1', kind='paper', evidence_kind='synthetic', is_public=True, proposal_id=None, **updates)


class PublicDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.db=Database('sqlite://')
        self.db.create_schema()
        self.session=self.db.session_factory()

    def tearDown(self):
        self.session.close()
        self.db.engine.dispose()

    def test_idempotent_import_and_immutable_versions(self):
        first=record()
        self.assertEqual(import_public_records(self.session,[first])['inserted'],1)
        old=self.session.scalar(select(Source))
        original=(old.id,old.text,old.version,old.content_hash)
        self.assertEqual(import_public_records(self.session,[first]),dict(inserted=0,unchanged=1,retired=0))
        changed={**first,'text':'Synthetic temperature sensor recorded hourly.'}
        self.assertEqual(import_public_records(self.session,[changed]),dict(inserted=1,unchanged=0,retired=1))
        self.session.refresh(old)
        self.assertEqual(original,(old.id,old.text,old.version,old.content_hash))
        self.assertEqual(len(self.session.scalars(select(Source)).all()),2)
        page=search_public(self.session,'hourly')
        self.assertEqual(len(page['items']),1)
        self.assertNotEqual(page['items'][0]['id'],old.id)
        self.assertEqual(search_public(self.session,'intervals')['items'],[])

    def test_reimport_old_version_reactivates_snapshot_without_mutation(self):
        first=record()
        import_public_records(self.session,[first])
        old=self.session.scalar(select(Source)).id
        import_public_records(self.session,[{**first,'text':'Synthetic changed temperature sensor text.'}])
        import_public_records(self.session,[first])
        self.assertEqual(search_public(self.session,'intervals')['items'][0]['id'],old)
        self.assertEqual(len(self.session.scalars(select(Source)).all()),2)

    def test_new_public_version_preserves_attached_source_reference(self):
        from src.platform.database.models import Team,Proposal,ProposalSource
        import_public_records(self.session,[record()])
        old=self.session.scalar(select(Source))
        self.session.add(Team(id='team',name='Test team'))
        self.session.flush()
        self.session.add(Proposal(id='proposal',team_id='team',title='Saved proposal',content='Old cited text',
                                  selected_source_ids=[old.id]))
        self.session.flush()
        self.session.add(ProposalSource(proposal_id='proposal',source_id=old.id))
        self.session.flush()
        import_public_records(self.session,[{**record(),'text':'Synthetic newer sensor measurement protocol.'}])
        self.assertEqual(self.session.get(Proposal,'proposal').selected_source_ids,[old.id])
        self.assertEqual(self.session.get(ProposalSource,('proposal',old.id)).source_id,old.id)
        self.assertIn('ten minute',self.session.get(Source,old.id).text)

    def test_private_source_with_public_metadata_is_excluded(self):
        import_public_records(self.session,[record()])
        source=self.session.scalar(select(Source))
        source.is_public=False
        self.session.flush()
        self.assertEqual(search_public(self.session,'sensor')['items'],[])

    def test_synthetic_seed_keeps_original_ids_and_is_idempotent(self):
        from src.platform.discovery.search import list_samples
        self.assertEqual(seed_samples(self.session),6)
        self.assertEqual(seed_samples(self.session),0)
        self.assertEqual({x.source_id for x in self.session.scalars(select(PublicRecord))},
                         {x['id'] for x in list_samples()})
        page=search_public(self.session,'sensor')
        self.assertEqual({x['kind'] for x in page['items']},{'paper','researcher'})
        self.assertTrue(page['degraded'])
        self.assertEqual(search_public(self.session,'zzzzzz')['items'],[])

    def test_kinds_have_separate_external_keys(self):
        first=record()
        second={**first,'kind':'researcher','title':'Synthetic researcher: Sensor comparison'}
        import_public_records(self.session,[first,second])
        self.assertEqual(len(self.session.scalars(select(PublicRecord)).all()),2)

    def test_private_import_and_conflicting_batch_fail_before_writes(self):
        for records in [[{**record(),'is_public':False}],
                        [record(),{**record(),'text':'Synthetic conflicting evidence.'}]]:
            with self.assertRaises(ValueError):import_public_records(self.session,records)
        self.assertEqual(self.session.scalars(select(Source)).all(),[])

    def test_verified_public_metadata_search_ranking_and_provenance(self):
        data=json.loads((Path(__file__).parent/'fixtures/public_crossref_metadata.json').read_text())
        records=data['records']
        self.assertEqual(sum(r['kind']=='paper' for r in records),3)
        self.assertEqual(sum(r['kind']=='researcher' for r in records),8)
        self.assertEqual(import_public_records(self.session,records)['inserted'],11)
        self.assertEqual(import_public_records(self.session,records)['unchanged'],11)
        for query,title in [('deep learning','Deep learning'),('internet things','The Internet of Things: A survey'),
                            ('BM25','The Probabilistic Relevance Framework: BM25 and Beyond')]:
            page=search_public(self.session,query)
            self.assertTrue(any(item['title']==title for item in page['items']))
            item=next(item for item in page['items'] if item['title']==title)
            self.assertEqual(item['evidence_kind'],'public')
            self.assertGreater(item['score'],0)
            self.assertIn('BM25',item['reason'])
            self.assertIn(item['snippet'],item['text'])
            self.assertEqual(item['content_hash'],hashlib.sha256(item['text'].encode()).hexdigest())
            self.assertTrue(item['origin'].startswith('https://doi.org/10.'))
            metadata=self.session.get(PublicRecord,item['id']).metadata_json
            self.assertFalse(metadata['abstract_included'])
            self.assertIn('not established',metadata['text_rights'])
            self.assertTrue(metadata['metadata_url'].startswith('https://api.crossref.org/works/'))
            self.assertIn('2026-',metadata['fetched_at'])
            self.assertTrue(metadata['authors'])
        authors=search_public(self.session,'LeCun')['items']
        self.assertTrue(any(item['kind']=='researcher' for item in authors))
        author=next(item for item in authors if item['kind']=='researcher')
        self.assertTrue(author['title'].startswith('Listed author: Yann LeCun'))
        metadata=self.session.get(PublicRecord,author['id']).metadata_json
        self.assertEqual(metadata['identity_status'],'authorship_entry_unresolved')
        self.assertIn('unresolved',author['text'])

    def test_retired_and_proposal_scoped_records_never_enter_search(self):
        from src.platform.database.models import User,Team,Proposal
        import_public_records(self.session,[record()])
        source=self.session.scalar(select(Source))
        public=self.session.get(PublicRecord,source.id)
        public.is_current=False
        self.session.flush()
        self.assertEqual(search_public(self.session,'sensor')['items'],[])
        public.is_current=True
        self.session.add(Team(id='team',name='Test team'))
        self.session.flush()
        self.session.add(Proposal(id='proposal',team_id='team',title='Test proposal',content=''))
        self.session.flush()
        source.proposal_id='proposal'
        self.session.flush()
        self.assertEqual(search_public(self.session,'sensor')['items'],[])

    def test_normalized_line_endings_do_not_create_duplicate_snapshots(self):
        first={**record(),'text':'Synthetic sensor\r\nsampling.'}
        second={**record(),'text':'Synthetic sensor\nsampling.'}
        self.assertEqual(import_public_records(self.session,[first])['inserted'],1)
        self.assertEqual(import_public_records(self.session,[second])['unchanged'],1)


class CrossrefFetchTests(unittest.TestCase):
    def test_fact_only_normalization_excludes_unlicensed_abstract_and_affiliation_claims(self):
        from src.platform.ingestion.crossref import normalize_crossref
        record=normalize_crossref(dict(DOI='10.1234/test',title=['Sensor paper'],author=[dict(given='A',family='Author',affiliation=[dict(name='Unverified current employer')])],
                                       published={'date-parts':[[2020]]},abstract='COPYRIGHT ABSTRACT'), '2026-10-31T00:00:00Z')
        self.assertEqual(record['metadata']['authors'],['A Author'])
        self.assertNotIn('COPYRIGHT',str(record))
        self.assertNotIn('employer',str(record))
        self.assertFalse(record['metadata']['abstract_included'])
        from src.platform.ingestion.crossref import authorship_entries
        authors=authorship_entries(record)
        self.assertEqual(len(authors),1)
        self.assertEqual(authors[0]['metadata']['identity_status'],'authorship_entry_unresolved')
        self.assertEqual(authors[0]['kind'],'researcher')
        self.assertEqual(authors[0]['origin'],record['origin'])
        self.assertNotIn('employer',str(authors))

    def test_fetch_bounds_before_network_and_rejects_mismatched_doi(self):
        from src.platform.ingestion.crossref import fetch_crossref
        with patch('src.platform.ingestion.crossref.urlopen') as network:
            for dois in [[], ['10.1234/'+str(n) for n in range(6)], ['https://private.example']]:
                with self.assertRaises(ValueError):fetch_crossref(dois)
            network.assert_not_called()
            response=network.return_value.__enter__.return_value
            response.read.return_value=json.dumps({'message':{'DOI':'10.1234/wrong'}}).encode()
            with self.assertRaises(ValueError):fetch_crossref(['10.1234/test'])
            request=network.call_args[0][0]
            self.assertEqual(request.full_url,'https://api.crossref.org/works/10.1234%2Ftest')
