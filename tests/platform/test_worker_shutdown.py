import contextlib
import io
import unittest
from unittest.mock import Mock

from sqlalchemy.exc import SQLAlchemyError

from services.worker.generate import close_worker


class WorkerShutdownTests(unittest.TestCase):
    def test_persistence_error_is_sanitized_and_engine_is_disposed(self):
        worker, database = Mock(), Mock()
        worker.close.side_effect = SQLAlchemyError('PRIVATE draft output in SQL parameters')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertFalse(close_worker(worker, database))
        worker.close.assert_called_once_with(wait=True)
        database.engine.dispose.assert_called_once()
        self.assertNotIn('PRIVATE', output.getvalue())
        self.assertIn('could not be persisted', output.getvalue())

    def test_normal_shutdown_disposes_engine(self):
        worker, database = Mock(), Mock()
        self.assertTrue(close_worker(worker, database))
        database.engine.dispose.assert_called_once()


if __name__ == '__main__':
    unittest.main()
