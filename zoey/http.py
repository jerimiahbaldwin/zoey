import base64
import json


def json_response(status_code, payload, headers=None):
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json.dumps(payload),
    }


def html_response(status_code, html, headers=None):
    response_headers = {"Content-Type": "text/html; charset=utf-8"}
    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": html,
    }


def text_response(status_code, text, content_type, headers=None):
    response_headers = {"Content-Type": content_type}
    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": text,
    }


def binary_response(status_code, content_bytes, content_type, headers=None):
    response_headers = {"Content-Type": content_type}
    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "isBase64Encoded": True,
        "body": base64.b64encode(content_bytes).decode("ascii"),
    }
