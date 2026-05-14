from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum


def encode_game(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: encode_game(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, list):
        return [encode_game(item) for item in value]
    if isinstance(value, dict):
        return {str(key): encode_game(item) for key, item in value.items()}
    return value
