import base64

from zoey.request import build_request


def test_build_request_supports_rest_api_shape():
    request = build_request(
        {
            "httpMethod": "post",
            "path": "files",
            "body": '{"content": "hello"}',
            "queryStringParameters": {"limit": "5"},
        }
    )

    assert request.method == "POST"
    assert request.path == "/files"
    assert request.body == {"content": "hello"}
    assert request.query == {"limit": "5"}


def test_build_request_supports_http_api_base64_body():
    encoded_body = base64.b64encode(b'{"content": "hello"}').decode("utf-8")

    request = build_request(
        {
            "requestContext": {"http": {"method": "POST"}},
            "rawPath": "/",
            "body": encoded_body,
            "isBase64Encoded": True,
        }
    )

    assert request.method == "POST"
    assert request.path == "/"
    assert request.body == {"content": "hello"}


def test_build_request_uses_event_as_body_when_body_is_missing():
    request = build_request({"method": "GET", "fileName": "default.txt"})

    assert request.method == "GET"
    assert request.body == {"method": "GET", "fileName": "default.txt"}
