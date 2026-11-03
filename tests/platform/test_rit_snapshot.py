import json
import tempfile
import unittest
from pathlib import Path

from src.platform.ingestion.rit_snapshot import (
    MAX_IMPORT_RECORDS,
    load_rit_snapshot,
    prepare_rit_snapshot,
)


def profile(slug: str, **updates) -> dict:
    row = {
        'name': 'Example Researcher',
        'url': f'https://www.rit.edu/computing/directory/{slug}',
        'research_interests': ['Information retrieval', 'Machine learning'],
        'email': 'private@example.test',
        'bio': 'Private biography that must not be imported.',
        'publications': ['Unreviewed paper content'],
    }
    row.update(updates)
    return row


class RitSnapshotTests(unittest.TestCase):
    def test_selects_five_stable_rows_and_excludes_unapproved_fields(self):
        rows = [profile(f'profile-{index:02}') for index in reversed(range(6))]
        rows.append(profile('profile-03'))

        records, counts = prepare_rit_snapshot(rows)

        self.assertEqual(len(records), MAX_IMPORT_RECORDS)
        self.assertEqual(
            counts,
            {
                'scanned': 7,
                'eligible': 6,
                'rejected': 0,
                'duplicate_urls': 1,
                'selected': 5,
            },
        )
        self.assertEqual(
            [row['external_id'].rsplit('/', 1)[-1] for row in records],
            [f'profile-{index:02}' for index in range(5)],
        )
        self.assertEqual(records[0]['evidence_kind'], 'public')
        self.assertEqual(
            records[0]['metadata']['identity_status'], 'legacy_profile_snapshot'
        )
        self.assertNotIn('private@example', str(records))
        self.assertNotIn('Private biography', str(records))
        self.assertNotIn('Unreviewed paper content', str(records))

    def test_rejects_noncanonical_urls_and_malformed_profile_facts(self):
        rows = [
            profile('external', url='https://rit.edu/computing/directory/external'),
            profile(
                'query', url='https://www.rit.edu/computing/directory/query?email=x'
            ),
            profile(
                'wrong-path', url='https://www.rit.edu/computing/people/wrong-path'
            ),
            profile(
                'bad-interest',
                research_interests=['Useful topic', 'contact@example.test'],
            ),
            profile('empty-name', name='  '),
            object(),
        ]

        records, counts = prepare_rit_snapshot(rows)

        self.assertEqual(records, [])
        self.assertEqual(counts['rejected'], len(rows))

    def test_conflicting_duplicate_profile_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'conflicting records'):
            prepare_rit_snapshot(
                [profile('duplicate'), profile('duplicate', name='Different Person')]
            )

    def test_limit_is_bounded_and_boolean_is_not_an_integer_limit(self):
        for limit in (0, MAX_IMPORT_RECORDS + 1, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                prepare_rit_snapshot([], limit)

    def test_loads_only_explicit_expected_file_and_rejects_restricted_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = root / 'rit_data_v2.json'
            valid.write_text(
                json.dumps({'faculty': [profile('fixture')]}), encoding='utf-8'
            )
            self.assertEqual(load_rit_snapshot(valid)[1]['selected'], 1)

            wrong_name = root / 'other.json'
            wrong_name.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'rit_data_v2.json'):
                load_rit_snapshot(wrong_name)

            restricted = root / 'restricted'
            restricted.mkdir()
            restricted_file = restricted / 'rit_data_v2.json'
            restricted_file.write_text(
                json.dumps({'faculty': [profile('restricted')]}), encoding='utf-8'
            )
            with self.assertRaisesRegex(ValueError, 'Restricted-mode'):
                load_rit_snapshot(restricted_file)

    def test_import_is_idempotent_and_interest_search_keeps_source_link(self):
        from src.platform.database import Database
        from src.platform.discovery.public_search import search_public
        from src.platform.ingestion.public_store import import_public_records

        records, _ = prepare_rit_snapshot(
            [profile('integration', research_interests=['Distributed retrieval'])]
        )
        database = Database('sqlite://')
        database.create_schema()
        try:
            with database.session_factory() as session:
                self.assertEqual(
                    import_public_records(session, records),
                    {'inserted': 1, 'unchanged': 0, 'retired': 0},
                )
                session.commit()
                self.assertEqual(
                    import_public_records(session, records),
                    {'inserted': 0, 'unchanged': 1, 'retired': 0},
                )
                results = search_public(session, 'distributed retrieval')
                self.assertEqual(len(results['items']), 1)
                self.assertEqual(results['items'][0]['origin'], records[0]['origin'])
                self.assertEqual(
                    results['items'][0]['identity_status'], 'legacy_profile_snapshot'
                )
                self.assertTrue(results['degraded'])
        finally:
            database.engine.dispose()

    def test_apply_requires_rights_confirmation_before_database_access(self):
        from src.platform.ingestion.import_rit_snapshot import main

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'rit_data_v2.json'
            source.write_text(
                json.dumps({'faculty': [profile('fixture')]}), encoding='utf-8'
            )
            self.assertEqual(main(['--source-file', str(source), '--apply']), 2)


if __name__ == '__main__':
    unittest.main()
