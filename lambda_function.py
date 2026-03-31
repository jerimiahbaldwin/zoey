import json
import os

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

PASSPHRASE = "At the end of the game, the king and the pawn go back in the same box."
BUCKET = os.environ.get("BUCKET_NAME", "jerimiahbaldwin-zoey")
OBJECT_KEY = "default.Txt"


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


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
            import base64

            body_text = base64.b64decode(body).decode("utf-8")

        if body_text.strip() == "":
            return {}

        return json.loads(body_text)

    return {}


def _extract_query_params(event):
    if not isinstance(event, dict):
        return {}
    params = event.get("queryStringParameters")
    if isinstance(params, dict):
        return params
    return {}


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


def _extract_object_key(payload, query):
    file_name = payload.get("fileName") or query.get("fileName") or OBJECT_KEY

    if not isinstance(file_name, str):
        return None, _response(400, {"error": "fileName must be a string"})

    key = file_name.strip()
    if key == "":
        return None, _response(400, {"error": "fileName cannot be empty"})

    # Keep keys simple and avoid hidden control chars in object names.
    if any(ch in key for ch in ["\r", "\n", "\t"]):
        return None, _response(400, {"error": "fileName contains invalid characters"})

    return key, None


def _build_docs_payload():
    return {
        "service": "zoey",
        "bucket": BUCKET,
        "defaultFileName": OBJECT_KEY,
        "auth": {
            "passphraseRequiredForDataRoutes": True,
            "passphraseField": "passphrase",
        },
        "routes": [
            {
                "method": "GET",
                "path": "/docs",
                "description": "List available routes and capabilities.",
                "requiresPassphrase": False,
            },
            {
                "method": "GET",
                "path": "/files",
                "description": "List objects in the configured S3 bucket.",
                "requiresPassphrase": True,
                "query": ["passphrase", "prefix (optional)", "limit (optional, 1-1000)"],
            },
            {
                "method": "GET",
                "path": "/",
                "description": "Read file content from S3.",
                "requiresPassphrase": True,
                "query": ["passphrase", "fileName (optional)"],
            },
            {
                "method": "POST",
                "path": "/",
                "description": "Write file content to S3.",
                "requiresPassphrase": True,
                "body": ["passphrase", "content", "fileName (optional)"],
            },
        ],
    }


def _parse_limit(query):
    raw = query.get("limit")
    if raw is None or raw == "":
        return 200, None

    try:
        limit = int(raw)
    except (TypeError, ValueError):
        return None, _response(400, {"error": "limit must be an integer"})

    if limit < 1 or limit > 1000:
        return None, _response(400, {"error": "limit must be between 1 and 1000"})

    return limit, None


def _list_files(prefix, limit):
    keys = []
    continuation_token = None

    while len(keys) < limit:
        max_keys = min(1000, limit - len(keys))
        kwargs = {
            "Bucket": BUCKET,
            "Prefix": prefix,
            "MaxKeys": max_keys,
        }
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        result = s3.list_objects_v2(**kwargs)
        for item in result.get("Contents", []):
            keys.append(item["Key"])

        if not result.get("IsTruncated"):
            break
        continuation_token = result.get("NextContinuationToken")

    return keys


def lambda_handler(event, context):
    method = _extract_method(event)
    payload = _extract_json_body(event)
    query = _extract_query_params(event)
    path = _normalize_path(_extract_path(event))

    if method == "GET" and path == "/docs":
        return _response(200, _build_docs_payload())

    provided_passphrase = payload.get("passphrase") or query.get("passphrase")

    if provided_passphrase != PASSPHRASE:
        return _response(403, {"error": "Invalid passphrase"})

    if method == "GET" and path == "/files":
        prefix = query.get("prefix", "")
        if not isinstance(prefix, str):
            return _response(400, {"error": "prefix must be a string"})

        limit, limit_error = _parse_limit(query)
        if limit_error:
            return limit_error

        keys = _list_files(prefix=prefix, limit=limit)
        return _response(
            200,
            {
                "bucket": BUCKET,
                "prefix": prefix,
                "count": len(keys),
                "files": keys,
            },
        )

    object_key, key_error = _extract_object_key(payload, query)

    if key_error:
        return key_error

    if method == "POST":
        content = payload.get("content", query.get("content", ""))
        if not isinstance(content, str):
            return _response(400, {"error": "content must be a string"})

        s3.put_object(Bucket=BUCKET, Key=object_key, Body=content.encode("utf-8"))
        return _response(200, {"message": "Write successful", "bucket": BUCKET, "key": object_key})

    if method == "GET":
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=object_key)
            text = obj["Body"].read().decode("utf-8")
            return _response(200, {"content": text, "bucket": BUCKET, "key": object_key})
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "Unknown")
            if code in {"NoSuchKey", "404"}:
                return _response(404, {"error": f"{object_key} not found"})
            raise

    return _response(405, {"error": "Use HTTP GET or POST"})
