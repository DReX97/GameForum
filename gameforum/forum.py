def register_routes(app):

    # Display the homepage
    @app.route('/')
    def home():
        return "Welcome to GameForum!"