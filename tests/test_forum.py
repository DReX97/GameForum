
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

    
    def test_create_thread(self):
        #simulate an authenticated user
        with self.client.session_transaction() as session:
            session['user_id'] = 1

        response = self.client.post('/threads/new', data={
            'title': 'Best RPG games',
            'category': 'RPG',
            'content': 'What games would you recommend?'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Best RPG games', response.data)
        self.assertIn(b'What games would you recommend?', response.data)

    def test_search_threads(self):
        #insert sample discussions into the temporary database
        with self.app.app_context():
            conn = get_connection()

            conn.executemany(
                "INSERT INTO threads (title, category, content) VALUES (?, ?, ?)",
                [
                    ('Best RPG games', 'RPG', 'Game recommendations'),
                    ('Minecraft tips', 'General', 'Building tips')
                ]
            )

            conn.commit()
            conn.close()

        #verify that searching by title returns matching discussions
        response = self.client.get('/?search=Minecraft')
        self.assertIn(b'Minecraft tips', response.data)
        self.assertNotIn(b'Best RPG games', response.data)

        #verify that searching by category works
        response = self.client.get('/?search=RPG')
        self.assertIn(b'Best RPG games', response.data)
        self.assertNotIn(b'Minecraft tips', response.data)

    def test_guest_cannot_create_thread(self):
        #attempt to create a discussion without authentication
        response = self.client.post('/threads/new', data={
            'title': 'Unauthorised discussion',
            'category': 'General',
            'content': 'Guest submission'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/login')

        #verify that the discussion was not created
        response = self.client.get('/')
        self.assertNotIn(b'Unauthorised discussion', response.data)

    def test_invalid_category(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 1

        #bypass HTML validation and submit an invalid category
        response = self.client.post('/threads/new', data={
            'title': 'Test discussion',
            'category': 'InvalidCategory',
            'content': 'Test content'
        })

        self.assertIn(b'Please select a valid category.', response.data)


    # Create a sample discussion in the temporary database
    def create_test_thread(self):
        with self.app.app_context():
            conn = get_connection()

            cursor = conn.execute(
                "INSERT INTO threads (title, category, content) VALUES (?, ?, ?)",
                ('Cyberpunk', 'RPG', 'New game coming')
            )

            thread_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return thread_id

    #Register and authenticate a test user
    def login_test_user(self):
        user_data = {
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        }

        self.client.post('/register', data=user_data)
        self.client.post('/login', data=user_data)

    def test_view_thread(self):
        thread_id = self.create_test_thread()

        response = self.client.get(f'/threads/{thread_id}')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cyberpunk', response.data)
        self.assertIn(b'New game coming', response.data)

    def test_create_comment(self):
        thread_id = self.create_test_thread()
        self.login_test_user()

        response = self.client.post(
            f'/threads/{thread_id}',
            data={'content': 'Looking forward to this game!'},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Looking forward to this game!', response.data)
        self.assertIn(b'gamer1', response.data)

    def test_guest_cannot_comment(self):
        thread_id = self.create_test_thread()

        #attempt to submit a comment without authentication
        response = self.client.post(
            f'/threads/{thread_id}',
            data={'content': 'Guest comment'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/login')

        #verify that the comment was not stored
        response = self.client.get(f'/threads/{thread_id}')
        self.assertNotIn(b'Guest comment', response.data)

    def test_invalid_comment(self):
        thread_id = self.create_test_thread()
        self.login_test_user()

        #verify that empty comments are rejected
        response = self.client.post(
            f'/threads/{thread_id}',
            data={'content': ''}
        )

        self.assertIn(b'Please enter a valid comment.', response.data)

    def test_thread_not_found(self):
        response = self.client.get('/threads/999999')

        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
    