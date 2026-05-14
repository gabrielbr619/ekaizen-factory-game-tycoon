from __future__ import annotations

from app.api.command_dispatcher import apply_command_payload
from app.api.hall import build_hall_of_kaizen_response
from app.api.schemas import ProcessSprintPayload
from app.api.security import hash_command, sign_session
from app.api.serialization import encode_game
from app.domain.engine import create_game
from app.domain.models import Column


def test_encode_game_serializes_dataclasses_and_enums() -> None:
    game = create_game(123)

    encoded = encode_game({"game": game, "column": Column.BACKLOG})

    assert isinstance(encoded, dict)
    assert encoded["column"] == "backlog"
    assert isinstance(encoded["game"], dict)
    assert encoded["game"]["cards"][0]["column"] == "backlog"


def test_hash_command_is_stable_for_key_order() -> None:
    first = hash_command({"type": "hire-candidate", "candidate_id": "cand-1-0"})
    second = hash_command({"candidate_id": "cand-1-0", "type": "hire-candidate"})

    assert first == second


def test_sign_session_uses_supplied_secret() -> None:
    signed = sign_session("game-1", "test-secret")

    assert signed.startswith("game-1.")
    assert signed == sign_session("game-1", "test-secret")
    assert signed != sign_session("game-1", "other-secret")


def test_build_hall_of_kaizen_response_handles_empty_metrics() -> None:
    game = create_game(123)

    response = build_hall_of_kaizen_response(game)

    assert response["verdict"] == "playing"
    assert response["lead_time_avg"] == 0
    assert response["sprint_mvp"] == {"sprint": 0, "throughput_value": 0, "oee": 0.0}
    assert response["timeline"] == [
        {"sprint": 1, "kind": "start", "message": "Voce assumiu a eKaizen Software."}
    ]


def test_apply_command_payload_dispatches_process_sprint() -> None:
    game = create_game(123)

    updated = apply_command_payload(game, ProcessSprintPayload(type="process-sprint"))

    assert updated.sprint == 2
    assert updated.metrics_history[0].sprint == 1
