from fakenodo.app.routes import api_bp
from flask import Flask

def create_app():
    app = Flask(__name__)
    with app.app_context():
        app.register_blueprint(api_bp)
    return app
