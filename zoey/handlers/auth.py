import base64
import hashlib
import hmac
import json
import time

from zoey.config import AUTH_COOKIE_MAX_AGE_SECONDS, AUTH_COOKIE_NAME, AUTH_TOKEN_SECRET, PASSPHRASE
from zoey.http import html_response, json_response


def get_unlock_page(_request, _store):
    return html_response(200, _unlock_html())


def unlock(request, _store):
    provided_passphrase = request.body.get("passphrase") or request.query.get("passphrase")
    if provided_passphrase != PASSPHRASE:
        return json_response(403, {"error": "Invalid passphrase"})

    token = mint_auth_token()
    cookie = _build_auth_cookie(token)
    return json_response(200, {"message": "Unlocked", "expiresInSeconds": AUTH_COOKIE_MAX_AGE_SECONDS}, headers={"Set-Cookie": cookie})


def mint_auth_token():
    now = int(time.time())
    payload = {"iat": now, "exp": now + AUTH_COOKIE_MAX_AGE_SECONDS}
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _to_base64url(payload_bytes)

    signature = hmac.new(AUTH_TOKEN_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = _to_base64url(signature)
    return f"{payload_b64}.{signature_b64}"


def has_valid_auth_cookie(request):
    token = _extract_cookie_value(request.headers.get("cookie", ""), AUTH_COOKIE_NAME)
    if not token:
        return False

    return _is_valid_auth_token(token)


def _is_valid_auth_token(token):
    if not isinstance(token, str) or "." not in token:
        return False

    payload_b64, signature_b64 = token.split(".", 1)
    expected_signature = hmac.new(AUTH_TOKEN_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    if not hmac.compare_digest(signature_b64, _to_base64url(expected_signature)):
        return False

    try:
        payload_raw = _from_base64url(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return False

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return False

    return int(time.time()) <= exp


def _extract_cookie_value(cookie_header, key):
    if not isinstance(cookie_header, str) or cookie_header.strip() == "":
        return None

    parts = cookie_header.split(";")
    for part in parts:
        name, sep, value = part.strip().partition("=")
        if sep and name == key:
            return value

    return None


def _build_auth_cookie(token):
    return "; ".join(
        [
            f"{AUTH_COOKIE_NAME}={token}",
            f"Max-Age={AUTH_COOKIE_MAX_AGE_SECONDS}",
            "Path=/",
            "HttpOnly",
            "Secure",
            "SameSite=Lax",
        ]
    )


def _to_base64url(value):
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _from_base64url(value):
    padding_length = (4 - len(value) % 4) % 4
    return base64.urlsafe_b64decode((value + ("=" * padding_length)).encode("utf-8"))


def _unlock_html():
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Unlock Zoey</title>
  <style>
    body { font-family: sans-serif; margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f4f6f8; }
    .card { width: min(420px, 92vw); background: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 12px 30px rgba(0,0,0,.08); }
    h1 { margin-top: 0; font-size: 1.25rem; }
    label { display: block; margin-bottom: 8px; font-weight: 600; }
    input { width: 100%; box-sizing: border-box; padding: 10px 12px; border: 1px solid #cdd5df; border-radius: 8px; }
    button { margin-top: 12px; width: 100%; padding: 10px 12px; border: 0; border-radius: 8px; background: #0f62fe; color: #fff; font-weight: 600; cursor: pointer; }
    .status { min-height: 20px; margin-top: 10px; color: #374151; }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Enter Passphrase</h1>
    <label for=\"passphrase\">Passphrase</label>
    <input id=\"passphrase\" type=\"password\" autocomplete=\"current-password\" />
    <button id=\"unlock\" type=\"button\">Unlock</button>
    <p class=\"status\" id=\"status\"></p>
  </div>
  <script>
    const passphraseInput = document.getElementById('passphrase');
    const unlockButton = document.getElementById('unlock');
    const status = document.getElementById('status');

    async function submitUnlock() {
      status.textContent = 'Checking...';
      const response = await fetch('/unlock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ passphrase: passphraseInput.value })
      });

      if (response.ok) {
        status.textContent = 'Unlocked. Redirecting...';
        window.location.href = '/docs';
        return;
      }

      status.textContent = 'Invalid passphrase';
    }

    unlockButton.addEventListener('click', submitUnlock);
    passphraseInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        submitUnlock();
      }
    });
  </script>
</body>
</html>
"""
