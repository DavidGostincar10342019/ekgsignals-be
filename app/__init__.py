from flask import Flask
from .routes import main
from .routes_pdf import pdf_bp
from .routes_visualizations import viz_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(main, url_prefix="/api")
    app.register_blueprint(pdf_bp, url_prefix="/api")
    app.register_blueprint(viz_bp, url_prefix="/api/visualizations")
    
    # Dodaj rutu za glavnu stranicu
    @app.route("/")
    def index():
        from flask import render_template
        return render_template('index.html')
    
    return app
