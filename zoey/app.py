from zoey.config import PASSPHRASE
from zoey.handlers.docs import get_docs, get_health
from zoey.handlers.files import list_files, read_file, write_file
from zoey.handlers.stubs import copy_file, delete_file, move_file, search_files
from zoey.http import json_response
from zoey.request import build_request
from zoey.services.s3_store import S3Store


ROUTES = {
    ("GET", "/docs"): {"handler": get_docs, "requires_passphrase": False},
    ("GET", "/health"): {"handler": get_health, "requires_passphrase": False},
    ("GET", "/files"): {"handler": list_files, "requires_passphrase": True},
    ("GET", "/"): {"handler": read_file, "requires_passphrase": True},
    ("POST", "/"): {"handler": write_file, "requires_passphrase": True},
    ("DELETE", "/"): {"handler": delete_file, "requires_passphrase": True},
    ("POST", "/files/copy"): {"handler": copy_file, "requires_passphrase": True},
    ("POST", "/files/move"): {"handler": move_file, "requires_passphrase": True},
    ("GET", "/search"): {"handler": search_files, "requires_passphrase": True},
}


def lambda_handler(event, context):
    request = build_request(event)
    route = ROUTES.get((request.method, request.path))

    if route is None:
        return json_response(404, {"error": f"Route not found for {request.method} {request.path}"})

    if route["requires_passphrase"]:
        provided_passphrase = request.body.get("passphrase") or request.query.get("passphrase")
        if provided_passphrase != PASSPHRASE:
            return json_response(403, {"error": "Invalid passphrase"})

    store = S3Store()
    return route["handler"](request, store)
