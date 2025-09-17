from flask import Flask
from .routes import api

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api, url_prefix="/api")
    
    # Dodaj rutu za glavnu stranicu
    @app.route("/")
    def index():
        from flask import render_template
        return render_template('index.html')
    
    return app
