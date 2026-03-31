from zoey.config import BUCKET, DEFAULT_OBJECT_KEY, SERVICE_NAME
from zoey.http import json_response


def get_docs(_request, _store):
    return json_response(
        200,
        {
            "service": SERVICE_NAME,
            "bucket": BUCKET,
            "defaultFileName": DEFAULT_OBJECT_KEY,
            "auth": {
                "passphraseRequiredForDataRoutes": True,
                "passphraseField": "passphrase",
                "cookieAuthRoute": "/unlock",
                "cookieLifetimeSeconds": 200 * 24 * 60 * 60,
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
                    "path": "/health",
                    "description": "Return a simple service health payload.",
                    "requiresPassphrase": False,
                },
                {
                    "method": "GET",
                    "path": "/unlock",
                    "description": "Serve a simple HTML passphrase form.",
                    "requiresPassphrase": False,
                },
                {
                    "method": "POST",
                    "path": "/unlock",
                    "description": "Validate passphrase and set a long-lived auth cookie.",
                    "requiresPassphrase": False,
                    "body": ["passphrase"],
                },
                {
                    "method": "POST",
                    "path": "/lock",
                    "description": "Clear the auth cookie and lock the browser session.",
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
                    "description": "Default entrypoint: serves unlock page unless authenticated, then reads file content from S3.",
                    "requiresPassphrase": False,
                    "query": ["passphrase (optional)", "fileName (optional)"],
                },
                {
                    "method": "POST",
                    "path": "/",
                    "description": "Write file content to S3.",
                    "requiresPassphrase": True,
                    "body": ["passphrase", "content", "fileName (optional)"],
                },
                {
                    "method": "DELETE",
                    "path": "/",
                    "description": "Delete a file from S3.",
                    "requiresPassphrase": True,
                    "query": ["passphrase", "fileName (optional)"],
                },
                {
                    "method": "POST",
                    "path": "/files/copy",
                    "description": "Copy one file to another location in S3.",
                    "requiresPassphrase": True,
                    "status": "stub",
                },
                {
                    "method": "POST",
                    "path": "/files/move",
                    "description": "Move a file between S3 keys.",
                    "requiresPassphrase": True,
                    "status": "stub",
                },
                {
                    "method": "GET",
                    "path": "/search",
                    "description": "Search file names or metadata.",
                    "requiresPassphrase": True,
                    "status": "stub",
                },
            ],
        },
    )


def get_health(_request, _store):
    return json_response(
        200,
        {
            "service": SERVICE_NAME,
            "status": "ok",
            "bucket": BUCKET,
        },
    )
