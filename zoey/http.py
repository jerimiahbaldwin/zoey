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
