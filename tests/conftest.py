import pytest

from main import app as sanic_app


@pytest.fixture
def app():
    return sanic_app
