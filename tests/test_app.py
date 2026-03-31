import json

import pytest

from zoey import app
from zoey.config import PASSPHRASE


class FakeStore:
    def __init__(self):
        self.bucket = "test-bucket"
        self.writes = []

    def list_files(self, prefix, limit):
        return [f"{prefix}alpha.txt", f"{prefix}beta.txt"][:limit]

    def read_text(self, key):
        return f"contents:{key}"

    def write_text(self, key, content):
        self.writes.append((key, content))

    def is_missing_key_error(self, error):
        return False


@pytest.fixture
def fake_store(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(app, "S3Store", lambda: store)
    return store


def parse_body(response):
    return json.loads(response["body"])


def test_health_route_does_not_require_passphrase(fake_store):
    response = app.lambda_handler({"httpMethod": "GET", "path": "/health"}, None)

    assert response["statusCode"] == 200
    assert parse_body(response)["status"] == "ok"


def test_list_files_requires_passphrase(fake_store):
    response = app.lambda_handler({"httpMethod": "GET", "path": "/files", "queryStringParameters": {}}, None)

    assert response["statusCode"] == 403
    assert parse_body(response)["error"] == "Invalid passphrase"


def test_list_files_returns_keys_when_passphrase_matches(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "GET",
            "path": "/files",
            "queryStringParameters": {"passphrase": PASSPHRASE, "prefix": "docs/", "limit": "2"},
        },
        None,
    )

    body = parse_body(response)

    assert response["statusCode"] == 200
    assert body["count"] == 2
    assert body["files"] == ["docs/alpha.txt", "docs/beta.txt"]


def test_write_file_persists_content(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "POST",
            "path": "/",
            "body": {"passphrase": PASSPHRASE, "fileName": "notes.txt", "content": "hello"},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert fake_store.writes == [("notes.txt", "hello")]
