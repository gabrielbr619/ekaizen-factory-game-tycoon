from __future__ import annotations

import hashlib
import hmac
import json


def sign_session(game_id: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), game_id.encode(), hashlib.sha256).hexdigest()
    return f"{game_id}.{digest}"


def is_valid_session(game_id: str, cookie: str, secret: str) -> bool:
    return hmac.compare_digest(cookie, sign_session(game_id, secret))


def hash_command(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()
