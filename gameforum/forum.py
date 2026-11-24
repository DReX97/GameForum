from flask import render_template, session, request, redirect, url_for
from .database import get_connection

def register_routes(app):
    #display the homepage and handle discussion searches
    @app.route('/')
    def home():
        search = request.args.get('search', '').strip()
        conn = get_connection()

        if search:
            #use parameterised queries to prevent SQL injection
            threads = conn.execute(
                "SELECT * FROM threads WHERE title LIKE ? OR category LIKE ?",
                ('%' + search + '%', '%' + search + '%')
            ).fetchall()
        else:
            #retrieve all discussions when no search term is provided
            threads = conn.execute(
                "SELECT * FROM threads"
            ).fetchall()

        conn.close()

        return render_template(
            'index.html',
            username=session.get('username'),
            threads=threads,
            search=search
        )

    #allow authenticated users to create discussions
    @app.route('/threads/new', methods=['GET', 'POST'])
    def create_thread():

        #prevent unauthenticated users from creating discussions
        if 'user_id' not in session:
            return redirect(url_for('login'))

        error = None

        categories = (
            'General', 'RPG', 'PC Gaming', 'FPS', 'Strategy',
            'Console', 'Horror', 'Adventure', 'Puzzle'
        )

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            category = request.form.get('category', '').strip()
            content = request.form.get('content', '').strip()

            # Validate user input on the server
            if not title or len(title) > 120:
                error = "Please enter a valid title."
            elif category not in categories:
                error = "Please select a valid category."
            elif not content or len(content) > 2000:
                error = "Please enter valid discussion content."
            else:
                conn = get_connection()

                #safely insert the discussion using SQL parameters
                conn.execute(
                    "INSERT INTO threads (title, category, content) VALUES (?, ?, ?)",
                    (title, category, content)
                )

                conn.commit()
                conn.close()

                return redirect(url_for('home'))

        return render_template('create_thread.html', error=error, categories=categories)
