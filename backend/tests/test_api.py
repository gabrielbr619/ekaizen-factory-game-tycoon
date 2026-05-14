from fastapi.testclient import TestClient

from app.main import app


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
