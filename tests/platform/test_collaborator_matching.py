import hashlib
import unittest

from sqlalchemy import func, select

from src.platform.database import Database
from src.platform.database.models import Membership, Source
from src.platform.database.public_records import PublicRecord
from src.platform.discovery.matching import match_collaborators
from src.platform.ingestion.public_store import import_public_records


def profile(external_id, text, **updates):
    return {
        'external_id': external_id,
        'title': updates.pop('title', 'Researcher profile'),
        'text': text,
        'origin': updates.pop(
            'origin', 'https://www.rit.edu/computing/directory/test-profile'
        ),
        'version': 'v1',
        'kind': 'researcher',
        'evidence_kind': updates.pop('evidence_kind', 'public'),
        'is_public': True,
        'proposal_id': None,
        'metadata': updates.pop('metadata', {'identity_status': 'official_profile'}),
        **updates,
    }


class CollaboratorMatchingTests(unittest.TestCase):
    def setUp(self):
        self.database = Database('sqlite://')
        self.database.create_schema()
        self.session = self.database.session_factory()

    def tearDown(self):
        self.session.close()
        self.database.engine.dispose()

    def test_returns_source_linked_profiles_with_explicit_keyword_reasons(self):
        records = [
            profile(
                'rit:distributed',
                'Listed expertise: distributed systems and retrieval.',
            ),
            profile(
                'rit:vision',
                'Listed expertise: computer vision and robotics.',
                origin='https://www.rit.edu/computing/directory/vision',
            ),
        ]
        paper = {
            **records[0],
            'external_id': 'doi:10.1000/distributed',
            'title': 'Distributed retrieval study',
            'kind': 'paper',
        }
        import_public_records(self.session, [*records, paper])

        result = match_collaborators(self.session, 'distributed retrieval')

        self.assertEqual(len(result['items']), 1)
        item = result['items'][0]
        expected = self.session.scalar(
            select(Source).where(Source.origin == records[0]['origin'])
        )
        self.assertEqual(item['source_id'], expected.id)
        self.assertEqual(item['candidate_status'], 'public_profile')
        self.assertEqual(item['matched_terms'], ['distributed', 'retrieval'])
        self.assertEqual(item['evidence_terms'], ['distributed', 'retrieval'])
        self.assertEqual(item['idea_coverage'], 1.0)
        self.assertIn('availability is unknown', item['reason'])
        self.assertIn('keyword overlap', item['reason'].lower())
        self.assertEqual(result['method'], 'keyword_overlap')
        self.assertEqual(result['coverage']['eligible_profile_count'], 2)
        self.assertEqual(result['coverage']['uncovered_terms'], [])
        self.assertTrue(result['degraded'])

    def test_expands_common_abbreviations_and_reports_profile_coverage_gaps(self):
        records = [
            profile(
                'rit:ai',
                'Listed research interests: Artificial Intelligence.',
                title='AI profile',
            ),
            profile(
                'rit:nlp',
                'Listed research interests: Natural language processing.',
                title='NLP profile',
                origin='https://www.rit.edu/computing/directory/nlp',
            ),
        ]
        import_public_records(self.session, records)

        result = match_collaborators(self.session, 'AI and NLP climate science')

        self.assertEqual(
            {item['title'] for item in result['items']}, {'AI profile', 'NLP profile'}
        )
        ai_match = next(
            item for item in result['items'] if item['title'] == 'AI profile'
        )
        self.assertEqual(ai_match['matched_terms'], ['AI'])
        self.assertEqual(ai_match['evidence_terms'], ['artificial', 'intelligence'])
        self.assertIn('Fixed abbreviation expansion', ai_match['reason'])
        self.assertAlmostEqual(ai_match['idea_coverage'], 0.25)
        self.assertEqual(result['coverage']['uncovered_terms'], ['climate', 'science'])
        self.assertEqual(result['coverage']['eligible_profile_count'], 2)
        self.assertEqual(result['coverage']['matching_profile_count'], 2)
        self.assertIn(
            'does not mean no researcher works on that topic',
            result['coverage']['note'],
        )

    def test_ignores_question_filler_and_profile_template_words(self):
        import_public_records(
            self.session,
            [
                profile(
                    'rit:ai',
                    'Listed expertise: Artificial Intelligence.',
                    title='Researcher profile',
                )
            ],
        )

        result = match_collaborators(
            self.session, 'How can we use artificial intelligence?'
        )

        self.assertEqual(len(result['items']), 1)
        self.assertEqual(
            result['items'][0]['matched_terms'], ['artificial intelligence']
        )
        self.assertEqual(result['items'][0]['idea_coverage'], 1.0)
        self.assertEqual(match_collaborators(self.session, 'research')['items'], [])

    def test_phrase_alias_requires_all_profile_terms_or_the_acronym(self):
        import_public_records(
            self.session,
            [
                profile(
                    'rit:partial',
                    'Listed expertise: document processing.',
                    title='Partial phrase profile',
                )
            ],
        )

        result = match_collaborators(self.session, 'natural language processing')

        self.assertEqual(result['items'], [])
        self.assertEqual(
            result['coverage']['uncovered_terms'], ['natural language processing']
        )

    def test_supports_ml_nlp_rag_aliases_and_snapshot_status(self):
        records = [
            profile(
                'rit:ml',
                'Listed research interests: Machine learning.',
                title='ML profile',
            ),
            profile(
                'rit:rag',
                'Listed research interests: Retrieval augmented generation.',
                title='RAG profile',
                origin='https://www.rit.edu/computing/directory/rag',
            ),
            profile(
                'rit:snapshot',
                'Listed research interests: Natural language processing.',
                title='Snapshot profile',
                origin='https://www.rit.edu/computing/directory/snapshot',
                metadata={'identity_status': 'legacy_profile_snapshot'},
            ),
        ]
        import_public_records(self.session, records)

        result = match_collaborators(self.session, 'ML RAG NLP')

        by_title = {item['title']: item for item in result['items']}
        self.assertEqual(
            set(by_title), {'ML profile', 'RAG profile', 'Snapshot profile'}
        )
        self.assertEqual(
            by_title['ML profile']['evidence_terms'], ['learning', 'machine']
        )
        self.assertEqual(
            by_title['RAG profile']['evidence_terms'],
            ['augmented', 'generation', 'retrieval'],
        )
        self.assertEqual(
            by_title['Snapshot profile']['candidate_status'], 'snapshot_profile'
        )
        self.assertIn('currentness is unknown', by_title['Snapshot profile']['reason'])
        self.assertEqual(result['coverage']['eligible_profile_count'], 3)
        self.assertEqual(result['coverage']['uncovered_terms'], [])

    def test_snapshot_importer_profiles_match_with_freshness_caveat_and_provenance(
        self,
    ):
        from src.platform.ingestion.rit_snapshot import prepare_rit_snapshot

        records, _ = prepare_rit_snapshot(
            [
                {
                    'name': 'Example Researcher',
                    'url': 'https://www.rit.edu/computing/directory/snapshot-example',
                    'research_interests': ['Machine learning'],
                    'email': 'excluded@example.test',
                }
            ]
        )
        import_public_records(self.session, records)

        result = match_collaborators(self.session, 'ML')

        self.assertEqual(len(result['items']), 1)
        item = result['items'][0]
        self.assertEqual(item['candidate_status'], 'snapshot_profile')
        self.assertEqual(item['origin'], records[0]['origin'])
        self.assertEqual(item['evidence_terms'], ['learning', 'machine'])
        self.assertIn('currentness is unknown', item['reason'])
        self.assertNotIn('excluded@example.test', str(item))

    def test_excludes_unresolved_authors_private_and_nonmatching_records(self):
        records = [
            profile(
                'author:unknown',
                'Listed expertise: climate systems and sensing.',
                metadata={'identity_status': 'authorship_entry_unresolved'},
                origin='https://doi.org/10.1000/unresolved',
            ),
            profile(
                'rit:private',
                'Listed expertise: climate systems.',
                origin='https://www.rit.edu/computing/directory/private',
            ),
            profile(
                'rit:fake',
                'Listed expertise: climate systems.',
                origin='https://example.com/computing/directory/fake',
            ),
            profile(
                'rit:unrelated',
                'Listed expertise: classical literature.',
                origin='https://www.rit.edu/computing/directory/unrelated',
            ),
        ]
        import_public_records(self.session, [records[0], records[2], records[3]])
        private_text = records[1]['text']
        self.session.add(
            Source(
                id='private-source',
                version='v1',
                content_hash=hashlib.sha256(private_text.encode()).hexdigest(),
                title=records[1]['title'],
                origin=records[1]['origin'],
                text=private_text,
                is_public=False,
                proposal_id=None,
            )
        )
        self.session.flush()
        self.session.add(
            PublicRecord(
                source_id='private-source',
                external_id='researcher:private',
                kind='researcher',
                evidence_kind='public',
                is_current=True,
                metadata_json={'identity_status': 'official_profile'},
            )
        )
        self.session.commit()

        result = match_collaborators(self.session, 'climate sensing')

        self.assertEqual(result['items'], [])

    def test_labels_synthetic_examples_and_does_not_invent_public_identity(self):
        synthetic = profile(
            'synthetic:sample',
            'Synthetic researcher example: water quality sensors.',
            title='Synthetic researcher: water quality',
            origin='Synthetic example only',
            evidence_kind='synthetic',
            metadata={},
        )
        official = profile(
            'rit:water',
            'Listed expertise: water quality sensors.',
            title='Official water profile',
            origin='https://www.rit.edu/computing/directory/water',
        )
        import_public_records(self.session, [synthetic, official])

        result = match_collaborators(self.session, 'water quality sensors')

        self.assertEqual(
            [item['candidate_status'] for item in result['items']],
            ['public_profile', 'synthetic_example'],
        )
        item = result['items'][1]
        self.assertEqual(item['candidate_status'], 'synthetic_example')
        self.assertIn('not a real person', item['reason'])
        self.assertEqual(item['origin'], 'Synthetic example only')

    def test_api_route_returns_source_linked_keyword_matches(self):
        from fastapi.testclient import TestClient

        from services.api.app import create_app

        app = create_app('sqlite://')
        app.state.db.create_schema()
        try:
            with app.state.db.session_factory() as session:
                import_public_records(
                    session,
                    [
                        profile(
                            'rit:water',
                            'Listed expertise: water quality sensor measurements.',
                        )
                    ],
                )
                session.commit()
            with TestClient(app) as client:
                response = client.post(
                    '/api/v2/collaborators/matches',
                    json={'idea': 'water quality measurements'},
                )
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertTrue(body['degraded'])
            self.assertEqual(body['method'], 'keyword_overlap')
            self.assertEqual(
                body['items'][0]['origin'],
                'https://www.rit.edu/computing/directory/test-profile',
            )
            self.assertNotIn('text', body['items'][0])
            self.assertEqual(
                body['items'][0]['matched_terms'], ['measurements', 'quality', 'water']
            )
            invalid = client.post('/api/v2/collaborators/matches', json={'idea': '  '})
            self.assertEqual(invalid.status_code, 422)
        finally:
            app.state.db.engine.dispose()

    def test_authenticated_match_can_be_saved_without_enrolling_researcher(self):
        from fastapi.testclient import TestClient

        from services.api.app import create_app

        app = create_app('sqlite://')
        app.state.db.create_schema()
        try:
            with app.state.db.session_factory() as session:
                import_public_records(
                    session,
                    [
                        profile(
                            'rit:water',
                            'Listed expertise: water quality sensor measurements.',
                        )
                    ],
                )
                session.commit()
                source_id = session.scalar(
                    select(Source.id).where(
                        Source.origin
                        == 'https://www.rit.edu/computing/directory/test-profile'
                    )
                )

            with TestClient(app) as client:
                registered = client.post(
                    '/api/v2/auth/register',
                    json={
                        'email': 'researcher@example.test',
                        'name': 'Researcher',
                        'password': 'a sufficiently long password',
                    },
                )
                self.assertEqual(registered.status_code, 201, registered.text)
                team = client.post('/api/v2/teams', json={'name': 'Water research'})
                self.assertEqual(team.status_code, 201, team.text)
                team_id = team.json()['id']

                matches = client.post(
                    '/api/v2/collaborators/matches',
                    json={'idea': 'water quality measurements'},
                )
                self.assertEqual(matches.status_code, 200, matches.text)
                self.assertEqual(matches.json()['items'][0]['source_id'], source_id)

                saved = client.post(
                    f'/api/v2/teams/{team_id}/shortlist',
                    json={
                        'source_id': source_id,
                        'note': 'Match evidence: measurements, quality, water.',
                    },
                )
                self.assertEqual(saved.status_code, 201, saved.text)
                self.assertEqual(saved.json()['source_id'], source_id)
                self.assertEqual(
                    saved.json()['note'],
                    'Match evidence: measurements, quality, water.',
                )
                self.assertEqual(
                    client.get(f'/api/v2/teams/{team_id}/shortlist').json()['items'],
                    [saved.json()],
                )

                created_proposal = client.post(
                    '/api/v2/proposals',
                    json={
                        'team_id': team_id,
                        'title': 'Water quality sensor study',
                        'content': '',
                    },
                )
                self.assertEqual(
                    created_proposal.status_code, 201, created_proposal.text
                )
                proposal_id = created_proposal.json()['id']
                attached = client.post(
                    f'/api/v2/proposals/{proposal_id}/sources/attach',
                    json={'source_id': source_id},
                )
                self.assertEqual(attached.status_code, 201, attached.text)
                self.assertEqual(attached.json()['id'], source_id)
                self.assertEqual(
                    client.get(f'/api/v2/proposals/{proposal_id}/sources').json()[
                        'items'
                    ][0]['id'],
                    source_id,
                )

            with app.state.db.session_factory() as session:
                memberships = session.scalar(
                    select(func.count())
                    .select_from(Membership)
                    .where(Membership.team_id == team_id)
                )
                self.assertEqual(memberships, 1)
        finally:
            app.state.db.engine.dispose()

    def test_empty_nonlexical_and_invalid_limits_fail_or_return_no_matches(self):
        self.assertEqual(match_collaborators(self.session, 'the and of')['items'], [])
        for idea, limit in [(None, 5), ('topic', 0), ('topic', 21), ('topic', True)]:
            with self.subTest(idea=idea, limit=limit), self.assertRaises(ValueError):
                match_collaborators(self.session, idea, limit)


if __name__ == '__main__':
    unittest.main()
