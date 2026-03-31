import mimetypes

from botocore.exceptions import ClientError

from zoey.config import DEFAULT_OBJECT_KEY
from zoey.http import binary_response, json_response, text_response


def list_files(request, store):
    prefix = request.query.get("prefix", "")
    if not isinstance(prefix, str):
        return json_response(400, {"error": "prefix must be a string"})

    limit, limit_error = _parse_limit(request.query)
    if limit_error:
        return limit_error

    keys = store.list_files(prefix=prefix, limit=limit)
    return json_response(
        200,
        {
            "bucket": store.bucket,
            "prefix": prefix,
            "count": len(keys),
            "files": keys,
        },
    )


def read_file(request, store):
    object_key, key_error = _extract_object_key(request.body, request.query)
    if key_error:
        return key_error

    try:
        content_bytes, content_type = store.read_object(object_key)
        resolved_content_type = _resolve_content_type(content_type, object_key)

        if _is_textual_content_type(resolved_content_type):
            try:
                text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return binary_response(200, content_bytes, "application/octet-stream")

            return text_response(200, text, resolved_content_type)

        return binary_response(200, content_bytes, resolved_content_type)
    except ClientError as error:
        if store.is_missing_key_error(error):
            return json_response(404, {"error": f"{object_key} not found"})
        raise


def write_file(request, store):
    object_key, key_error = _extract_object_key(request.body, request.query)
    if key_error:
        return key_error

    content = request.body.get("content", request.query.get("content", ""))
    if not isinstance(content, str):
        return json_response(400, {"error": "content must be a string"})

    store.write_text(object_key, content)
    return json_response(200, {"message": "Write successful", "bucket": store.bucket, "key": object_key})


def delete_file(request, store):
    object_key, key_error = _extract_object_key(request.body, request.query)
    if key_error:
        return key_error

    store.delete_file(object_key)
    return json_response(200, {"message": "Delete successful", "bucket": store.bucket, "key": object_key})


def _parse_limit(query):
    raw = query.get("limit")
    if raw is None or raw == "":
        return 200, None

    try:
        limit = int(raw)
    except (TypeError, ValueError):
        return None, json_response(400, {"error": "limit must be an integer"})

    if limit < 1 or limit > 1000:
        return None, json_response(400, {"error": "limit must be between 1 and 1000"})

    return limit, None


def _extract_object_key(payload, query):
    file_name = payload.get("fileName") or query.get("fileName") or DEFAULT_OBJECT_KEY

    if not isinstance(file_name, str):
        return None, json_response(400, {"error": "fileName must be a string"})

    key = file_name.strip()
    if key == "":
        return None, json_response(400, {"error": "fileName cannot be empty"})

    if any(character in key for character in ["\r", "\n", "\t"]):
        return None, json_response(400, {"error": "fileName contains invalid characters"})

    return key, None


def _resolve_content_type(s3_content_type, object_key):
    if isinstance(s3_content_type, str) and s3_content_type.strip() != "":
        return s3_content_type

    guessed_content_type, _ = mimetypes.guess_type(object_key)
    if guessed_content_type:
        return guessed_content_type

    return "application/octet-stream"


def _is_textual_content_type(content_type):
    lowered = content_type.lower()
    if lowered.startswith("text/"):
        return True

    return lowered.startswith("application/json")
