from zoey.http import json_response


def delete_file(_request, _store):
    return _stub_response("delete_file")


def copy_file(_request, _store):
    return _stub_response("copy_file")


def move_file(_request, _store):
    return _stub_response("move_file")


def search_files(_request, _store):
    return _stub_response("search_files")


def _stub_response(function_name):
    return json_response(
        501,
        {
            "error": "Not implemented",
            "function": function_name,
            "message": "This route is scaffolded and ready for implementation.",
        },
    )
