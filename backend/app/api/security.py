from __future__ import annotations

import hashlib
import hmac
import json


def sign_session(game_id: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), game_id.encode(), hashlib.sha256).hexdigest()
    return f"{game_id}.{digest}"


def session_game_id(cookie: str, secret: str) -> str | None:
    try:
        game_id, _digest = cookie.rsplit(".", 1)
    except ValueError:
        return None
    return game_id if is_valid_session(game_id, cookie, secret) else None


def is_valid_session(game_id: str, cookie: str, secret: str) -> bool:
    return hmac.compare_digest(cookie, sign_session(game_id, secret))


def hash_command(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()
