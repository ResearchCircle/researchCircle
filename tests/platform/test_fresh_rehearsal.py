"""Fresh-install evidence must use new resources outside collected data."""
import importlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


IMAGES = {'TBR_API_IMAGE': 'fixture-api', 'TBR_WEB_IMAGE': 'fixture-web',
          'TBR_DB_IMAGE': 'postgres:16-alpine', 'TBR_PROXY_IMAGE': 'nginx:stable-alpine'}


class FreshRehearsalTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('deployment.rehearse'), 'Fresh installation rehearsal is missing')
        return importlib.import_module('deployment.rehearse')

    def test_rehearsal_cannot_write_inside_or_above_source_snapshot(self):
        module = self.module()
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'snapshot'
            source.mkdir()
            sentinel = source / 'previously-parsed.txt'
            sentinel.write_bytes(b'Previously parsed source must remain byte-for-byte unchanged.')
            before = sentinel.read_bytes()
            for output in (source, source / 'output', Path(tmp)):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    module.prepare_rehearsal(output, 18092, IMAGES, source)
            self.assertEqual(sentinel.read_bytes(), before)
            self.assertEqual([path.name for path in source.iterdir()], ['previously-parsed.txt'])

    def test_every_run_has_a_new_private_project_and_preserves_prior_settings(self):
        module = self.module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'snapshot'
            source.mkdir()
            output = root / 'working'
            first_path, first = module.prepare_rehearsal(output, 18092, IMAGES, source)
            first_bytes = first_path.read_bytes()
            second_path, second = module.prepare_rehearsal(output, 18093, IMAGES, source)
            self.assertNotEqual(first['COMPOSE_PROJECT_NAME'], second['COMPOSE_PROJECT_NAME'])
            self.assertTrue(first['COMPOSE_PROJECT_NAME'].startswith('tbr-fresh-'))
            self.assertNotEqual(first['TBR_DB_PASSWORD'], second['TBR_DB_PASSWORD'])
            self.assertEqual(first_path.read_bytes(), first_bytes)
            self.assertEqual(first_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(second_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(first['TBR_PROFILE'], 'development')
            self.assertEqual(first['TBR_MODEL_PROVIDER'], 'fixture')
            self.assertEqual(first['TBR_DEV_IDENTITY'], 'false')
            self.assertEqual(list(source.iterdir()), [])

    def test_output_cannot_enter_a_symlinked_source_directory(self):
        module = self.module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, received = root / 'snapshot', root / 'received-papers'
            source.mkdir()
            received.mkdir()
            (source / 'papers').symlink_to(received, target_is_directory=True)
            nested = root / 'nested-source'
            nested.mkdir()
            (received / 'more').symlink_to(nested, target_is_directory=True)
            (nested / 'back').symlink_to(source, target_is_directory=True)
            sentinel = received / 'already-downloaded.pdf'
            sentinel.write_bytes(b'Synthetic preservation sentinel')
            for output in (source / 'papers' / 'output', received / 'output', nested / 'output'):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    module.prepare_rehearsal(output, 18092, IMAGES, source)
            self.assertEqual(sentinel.read_bytes(), b'Synthetic preservation sentinel')
            self.assertEqual({path.name for path in received.iterdir()}, {'already-downloaded.pdf', 'more'})
            path, _ = module.prepare_rehearsal(root / 'working', 18092, IMAGES, source)
            self.assertTrue(path.exists(), 'A source-link cycle must not prevent safe separate output')


if __name__ == '__main__':
    unittest.main()
