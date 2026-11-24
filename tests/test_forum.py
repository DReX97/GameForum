
import tempfile
import unittest
from pathlib import Path

from gameforum import create_app
from gameforum.database import get_connection


class ForumTests(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for testing
        self.temp_dir = tempfile.TemporaryDirectory()

        self.app = create_app({
            'TESTING': True,
            'DATABASE': str(Path(self.temp_dir.name) / 'test.db')
        })

        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_homepage(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to GameForum!', response.data)

    def test_database_tables(self):
        with self.app.app_context():
            conn = get_connection()

            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()

            conn.close()

        table_names = [table['name'] for table in tables]

        self.assertIn('users', table_names)
        self.assertIn('threads', table_names)


if __name__ == '__main__':
    unittest.main()
    