# Zoey Lambda

This Lambda requires a passphrase, then reads or writes a single S3 object (default.Txt) in BUCKET_NAME (default: jerimiahbaldwin-zoey).

- `GET`: returns the file content.
- `POST` with `content`: overwrites the file.
