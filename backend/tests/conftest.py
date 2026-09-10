import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.seed import seed


@pytest.fixture(scope="session")
def token() -> str:
    return seed()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
