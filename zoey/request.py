import base64
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    body: dict
    query: dict
    headers: dict


def build_request(event):
    return Request(
        method=_extract_method(event),
        path=_normalize_path(_extract_path(event)),
        body=_extract_json_body(event),
        query=_extract_query_params(event),
        headers=_extract_headers(event),
    )


def _extract_method(event):
    if not isinstance(event, dict):
        return ""

    method = event.get("httpMethod")
    if method:
        return str(method).upper()

    request_context = event.get("requestContext", {})
    method = request_context.get("http", {}).get("method")
    if method:
        return str(method).upper()

    method = event.get("method")
    if method:
        return str(method).upper()

    return ""


def _extract_json_body(event):
    if not isinstance(event, dict):
        return {}

    body = event.get("body")
    if body is None:
        return event

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        body_text = body
        if event.get("isBase64Encoded"):
            body_text = base64.b64decode(body).decode("utf-8")

        if body_text.strip() == "":
            return {}

        try:
            return json.loads(body_text)
        except json.JSONDecodeError:
            return {}

    return {}


def _extract_query_params(event):
    if not isinstance(event, dict):
        return {}

    params = event.get("queryStringParameters")
    if isinstance(params, dict):
        return params

    return {}


def _extract_headers(event):
    if not isinstance(event, dict):
        return {}

    headers = event.get("headers")
    if not isinstance(headers, dict):
        return {}

    normalized = {}
    for key, value in headers.items():
        if key is None:
            continue

        normalized[str(key).lower()] = "" if value is None else str(value)

    return normalized


def _extract_path(event):
    if not isinstance(event, dict):
        return "/"

    raw_path = event.get("rawPath") or event.get("path") or "/"
    if not isinstance(raw_path, str):
        return "/"

    path = raw_path.strip()
    if path == "":
        return "/"

    if not path.startswith("/"):
        path = f"/{path}"

    return path


def _normalize_path(path):
    if path in {"", "/"}:
        return "/"

    return path.rstrip("/")
