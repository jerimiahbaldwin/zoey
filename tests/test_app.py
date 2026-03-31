import json

import pytest

from zoey import app
from zoey.config import AUTH_COOKIE_NAME
from zoey.config import PASSPHRASE


class FakeStore:
    def __init__(self):
        self.bucket = "test-bucket"
        self.writes = []
        self.deletes = []

    def list_files(self, prefix, limit):
        return [f"{prefix}alpha.txt", f"{prefix}beta.txt"][:limit]

    def read_text(self, key):
        return f"contents:{key}"

    def write_text(self, key, content):
        self.writes.append((key, content))

    def delete_file(self, key):
        self.deletes.append(key)

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


def test_delete_file_removes_object(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "DELETE",
            "path": "/",
            "queryStringParameters": {"passphrase": PASSPHRASE, "fileName": "notes.txt"},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert fake_store.deletes == ["notes.txt"]


def test_unlock_get_serves_html(fake_store):
    response = app.lambda_handler({"httpMethod": "GET", "path": "/unlock"}, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/html; charset=utf-8"
    assert "Enter Passphrase" in response["body"]
    assert "show-passphrase" in response["body"]


def test_root_route_serves_unlock_page_when_unauthenticated(fake_store):
    response = app.lambda_handler({"httpMethod": "GET", "path": "/"}, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/html; charset=utf-8"
    assert "Enter Passphrase" in response["body"]


def test_root_route_reads_file_when_authenticated(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "GET",
            "path": "/",
            "queryStringParameters": {"passphrase": PASSPHRASE, "fileName": "notes.txt"},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert parse_body(response)["content"] == "contents:notes.txt"


def test_root_route_lists_files_when_authenticated_without_file_name(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "GET",
            "path": "/",
            "queryStringParameters": {"passphrase": PASSPHRASE, "prefix": "docs/"},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/html; charset=utf-8"
    assert "S3 Files" in response["body"]
    assert "/?fileName=docs%2Falpha.txt" in response["body"]


def test_unlock_post_sets_auth_cookie(fake_store):
    response = app.lambda_handler(
        {
            "httpMethod": "POST",
            "path": "/unlock",
            "body": {"passphrase": PASSPHRASE},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert "Set-Cookie" in response["headers"]
    assert response["headers"]["Set-Cookie"].startswith(f"{AUTH_COOKIE_NAME}=")


def test_protected_route_accepts_valid_auth_cookie(fake_store):
    unlock_response = app.lambda_handler(
        {
            "httpMethod": "POST",
            "path": "/unlock",
            "body": {"passphrase": PASSPHRASE},
        },
        None,
    )
    cookie = unlock_response["headers"]["Set-Cookie"]

    response = app.lambda_handler(
        {
            "httpMethod": "GET",
            "path": "/files",
            "queryStringParameters": {"prefix": "docs/", "limit": "2"},
            "headers": {"Cookie": cookie},
        },
        None,
    )

    assert response["statusCode"] == 200
    body = parse_body(response)
    assert body["files"] == ["docs/alpha.txt", "docs/beta.txt"]
