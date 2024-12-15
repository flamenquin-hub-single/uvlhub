import pytest
from flask import Flask
from fakenodo.app.routes import api_bp


@pytest.fixture(scope="module")
def test_client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "localhost:5001"
    app.register_blueprint(api_bp)
    with app.test_client() as client:
        with app.app_context():
            yield client
