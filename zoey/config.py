import os


PASSPHRASE = "At the end of the game, the king and the pawn go back in the same box."
BUCKET = os.environ.get("BUCKET_NAME", "jerimiahbaldwin-zoey")
DEFAULT_OBJECT_KEY = "default.Txt"
SERVICE_NAME = "zoey"
AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME", "zoey_auth")
# 200 days keeps sessions valid for more than six months.
AUTH_COOKIE_MAX_AGE_SECONDS = int(os.environ.get("AUTH_COOKIE_MAX_AGE_SECONDS", str(200 * 24 * 60 * 60)))
AUTH_TOKEN_SECRET = os.environ.get("AUTH_TOKEN_SECRET", PASSPHRASE)
