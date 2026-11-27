import secrets
from .auth import register_auth_routes
from pathlib import Path
from flask import Flask
from .forum import register_routes
from .database import setup_database


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)

    #Use a separate database for vulverability demo
    app.config['DATABASE'] = 'database/gameforum_insecure.db'

    #Allow tests to use a separate database
    if test_config is not None:
        app.config.update(test_config)

    #Ensure the database folder exists
    Path(app.config['DATABASE']).parent.mkdir(exist_ok=True)

    with app.app_context():
        setup_database()

    register_routes(app)
    register_auth_routes(app)

    return app
