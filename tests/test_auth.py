import tempfile
import unittest
from pathlib import Path
from werkzeug.security import check_password_hash

from gameforum import create_app
from gameforum.database import get_connection


class AuthTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.app = create_app({
            'TESTING': True,
            'DATABASE': str(Path(self.temp_dir.name) / 'test.db')
        })

        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registration(self):
        response = self.client.post('/register', data={
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful!', response.data)

        # Verify that the password is stored as a hash
        with self.app.app_context():
            conn = get_connection()
            try:
                user = conn.execute(
                    "SELECT password_hash FROM users WHERE username = ?",
                    ('gamer1',)
                ).fetchone()
            finally:
                conn.close()

        self.assertIsNotNone(user)
        self.assertNotEqual(user['password_hash'], 'ExamplePassword123!')
        self.assertTrue(
            check_password_hash(user['password_hash'], 'ExamplePassword123!')
        )

    def test_duplicate_username(self):
        user_data = {
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        }

        self.client.post('/register', data=user_data)
        response = self.client.post('/register', data=user_data)

        self.assertIn(b'Username already exists.', response.data)

    def test_short_password(self):
        response = self.client.post('/register', data={
            'username': 'gamer1',
            'password': 'short'
        })

        self.assertIn(
            b'Password must be at least 15 characters.',
            response.data
        )

    
    def test_login(self):
        user_data = {
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        }

        self.client.post('/register', data=user_data)

        response = self.client.post(
            '/login', data=user_data, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in as gamer1', response.data)

    def test_invalid_login(self):
        self.client.post('/register', data={
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        })

        response = self.client.post('/login', data={
            'username': 'gamer1',
            'password': 'WrongPassword'
        })

        self.assertIn(b'Invalid username or password.', response.data)

        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)

    def test_logout(self):
        user_data = {
            'username': 'gamer1',
            'password': 'ExamplePassword123!'
        }

        self.client.post('/register', data=user_data)
        self.client.post('/login', data=user_data)

        response = self.client.post('/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)



if __name__ == '__main__':
    unittest.main()
