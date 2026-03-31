# Zoey Lambda

This Lambda requires a passphrase for data operations and reads or writes S3 objects in `BUCKET_NAME` (default: `jerimiahbaldwin-zoey`).

Lambda name: `zoey`
Base route: `https://otlya66bawi6x2caxv4223hvdq0aoglb.lambda-url.us-east-1.on.aws/`

The project is now organized so you can keep adding Lambda capabilities without pushing all routing and S3 logic back into one file.

## Structure

```text
lambda_function.py        # Thin AWS Lambda entrypoint
zoey/
	app.py                  # Route table and request dispatch
	config.py               # Environment-backed configuration
	http.py                 # JSON response helper
	request.py              # Event parsing and normalization
	handlers/
		docs.py               # Public docs and health handlers
		files.py              # Current S3-backed file handlers
		stubs.py              # Placeholder handlers for future routes
	services/
		s3_store.py           # S3 access layer
```

## Current routes

- `GET /docs`: returns JSON docs of the main capabilities.
- `GET /health`: returns a basic health payload.
- `GET /unlock`: serves a simple HTML page that prompts for the passphrase.
- `POST /unlock`: validates passphrase and sets a long-lived auth cookie (200 days).
- `GET /files`: lists files in the bucket. Requires `passphrase`; supports optional `prefix` and `limit`.
- `GET /`: reads a file. Requires `passphrase`; optional `fileName` (defaults to `default.Txt`).
- `POST /`: writes a file. Requires JSON body with `passphrase`, `content`, and optional `fileName`.
- `DELETE /`: deletes a file. Requires `passphrase`; optional `fileName` (defaults to `default.Txt`).

All protected routes also accept the auth cookie set by `POST /unlock`, so browser requests can remain authenticated without repeating `passphrase`.

## Stubbed routes

These are registered now and return `501 Not Implemented` until you fill them in.

- `POST /files/copy`
- `POST /files/move`
- `GET /search`

## Next expansion pattern

When you add another Lambda capability:

1. Create a handler in `zoey/handlers/`.
2. Put external API or storage logic in `zoey/services/`.
3. Register the route in `zoey/app.py`.
4. Add the route to `/docs` so the Lambda stays self-describing.

## Local verification

Install the local verification tooling:

```bash
python -m pip install -r requirements-dev.txt
```

Run the full local gate before pushing:

```bash
python scripts/preflight.py
```

That command runs:

- `black --check .`
- `ruff check .`
- `pytest`
- Python bytecode compilation for `lambda_function.py` and `zoey/`
- Lambda packaging to `dist/function.zip`

If you want to apply formatting locally before re-running the gate:

```bash
python scripts/preflight.py format
```
