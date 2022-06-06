import pytest
from flask.testing import FlaskClient
from app import create_flask_app


@pytest.fixture
def client():
    return create_flask_app().test_client()


def test_home(client: FlaskClient):
    """should be a successful GET request"""
    resp = client.get('/')
    assert resp.status_code == 200
    assert "Moscow time is:" in resp.text
