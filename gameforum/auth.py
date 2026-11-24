
import sqlite3
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_connection


def register_auth_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = None
        registered = False

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                error = "Username and password are required."
            elif len(password) < 15:
                error = "Password must be at least 15 characters."
            else:
                conn = get_connection()

                try:
                    password_hash = generate_password_hash(password)

                    conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, password_hash)
                    )
                    conn.commit()
                    registered = True

                except sqlite3.IntegrityError:
                    error = "Username already exists."

                finally:
                    conn.close()

        return render_template('register.html', error=error, registered=registered)
