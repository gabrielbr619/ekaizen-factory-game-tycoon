import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.security import sign_session
from app.main import SECRET, app, game_events, repo


def test_healthz() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_idempotent_process_sprint() -> None:
    client = TestClient(app)
    created = client.post("/games", json={"seed": 987})
    game_id = created.json()["id"]

    command = {"command_id": "same-command", "payload": {"type": "process-sprint"}}
    first = client.post(
        f"/games/{game_id}/commands",
        json=command,
        headers={"Idempotency-Key": "same-command"},
    )
    second = client.post(
        f"/games/{game_id}/commands",
        json=command,
        headers={"Idempotency-Key": "same-command"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["sprint"] == second.json()["sprint"]


def test_idempotency_key_rejects_different_payload() -> None:
    client = TestClient(app)
    created = client.post("/games", json={"seed": 654})
    game_id = created.json()["id"]

    first = client.post(
        f"/games/{game_id}/commands",
        json={"command_id": "same-command", "payload": {"type": "process-sprint"}},
        headers={"Idempotency-Key": "same-command"},
    )
    second = client.post(
        f"/games/{game_id}/commands",
        json={
            "command_id": "same-command",
            "payload": {"type": "hire-candidate", "candidate_id": "cand-1-0"},
        },
        headers={"Idempotency-Key": "same-command"},
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Idempotency-Key reutilizado com payload diferente."


def test_game_events_returns_sse_response() -> None:
    client = TestClient(app)
    created = client.post("/games", json={"seed": 321})
    game_id = created.json()["id"]

    response = asyncio.run(game_events(game_id, sign_session(game_id, SECRET)))

    assert response.media_type == "text/event-stream"
    assert repo.get(game_id) is not None


def test_create_game_rejects_unknown_fields() -> None:
    client = TestClient(app)

    response = client.post("/games", json={"seed": 321, "extra": "ignored?"})

    assert response.status_code == 422


def test_command_rejects_unknown_request_fields() -> None:
    client = TestClient(app)
    created = client.post("/games", json={"seed": 321})
    game_id = created.json()["id"]

    response = client.post(
        f"/games/{game_id}/commands",
        json={
            "command_id": "strict-command",
            "payload": {"type": "process-sprint"},
            "extra": "ignored?",
        },
        headers={"Idempotency-Key": "strict-command"},
    )

    assert response.status_code == 422


def test_command_rejects_unknown_payload_fields() -> None:
    client = TestClient(app)
    created = client.post("/games", json={"seed": 321})
    game_id = created.json()["id"]

    response = client.post(
        f"/games/{game_id}/commands",
        json={
            "command_id": "strict-payload",
            "payload": {"type": "process-sprint", "extra": "ignored?"},
        },
        headers={"Idempotency-Key": "strict-payload"},
    )

    assert response.status_code == 422


def test_create_game_is_idempotent_when_key_is_retried() -> None:
    client = TestClient(app)
    key = f"new-game-retry-{uuid4()}"

    first = client.post("/games", json={"seed": 777}, headers={"Idempotency-Key": key})
    second = client.post("/games", json={"seed": 777}, headers={"Idempotency-Key": key})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.headers["set-cookie"] == second.headers["set-cookie"]


def test_create_game_idempotency_key_rejects_different_payload() -> None:
    client = TestClient(app)
    key = f"new-game-conflict-{uuid4()}"

    first = client.post("/games", json={"seed": 111}, headers={"Idempotency-Key": key})
    second = client.post("/games", json={"seed": 222}, headers={"Idempotency-Key": key})

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Idempotency-Key reutilizado com payload diferente."
