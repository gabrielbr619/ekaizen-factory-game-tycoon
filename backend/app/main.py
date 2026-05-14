from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, FastAPI, Header, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    AllocateDevPayload,
    ApplyKaizenPayload,
    CommandRequest,
    CreateGameRequest,
    HireCandidatePayload,
    MoveCardPayload,
    ProcessSprintPayload,
)
from app.domain.engine import (
    allocate_dev,
    apply_kaizen,
    create_game,
    hire_candidate,
    move_card,
    process_sprint,
    top_kaizens,
)
from app.persistence import GameRepository

SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/factory-game.sqlite3"))

app = FastAPI(title="eKaizen Factory Game Tycoon API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
repo = GameRepository(DB_PATH)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/games")
def start_game(body: CreateGameRequest, response: Response) -> object:
    game = create_game(body.seed)
    repo.save(game)
    response.set_cookie("ekaizen_session", sign_session(game.id), httponly=True, samesite="lax")
    return encode_game(game)


@app.get("/games/{game_id}")
def get_game(game_id: str, ekaizen_session: Annotated[str | None, Cookie()] = None) -> object:
    require_session(game_id, ekaizen_session)
    game = repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return encode_game(game)


@app.post("/games/{game_id}/commands")
def execute_command(
    game_id: str,
    body: CommandRequest,
    ekaizen_session: Annotated[str | None, Cookie()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    require_session(game_id, ekaizen_session)
    command_id = idempotency_key or body.command_id
    previous = repo.get_idempotent(game_id, command_id)
    if previous is not None:
        return encode_game(previous)
    game = repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        payload = body.payload
        if isinstance(payload, MoveCardPayload):
            game = move_card(game, payload.card_id, payload.target)
        elif isinstance(payload, AllocateDevPayload):
            game = allocate_dev(game, payload.dev_id, payload.card_id)
        elif isinstance(payload, HireCandidatePayload):
            game = hire_candidate(game, payload.candidate_id)
        elif isinstance(payload, ApplyKaizenPayload):
            game = apply_kaizen(game, payload.kaizen, payload.target_id)
        elif isinstance(payload, ProcessSprintPayload):
            game = process_sprint(game)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    repo.save_idempotent(game, command_id)
    return encode_game(game)


@app.get("/games/{game_id}/events")
async def game_events(
    game_id: str, ekaizen_session: Annotated[str | None, Cookie()] = None
) -> StreamingResponse:
    require_session(game_id, ekaizen_session)

    async def stream() -> object:
        for _ in range(5):
            game = repo.get(game_id)
            if game is not None:
                payload = json.dumps(encode_game(game), ensure_ascii=False)
                yield f"event: state\ndata: {payload}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/games/{game_id}/hall-of-kaizen")
def hall_of_kaizen(
    game_id: str, ekaizen_session: Annotated[str | None, Cookie()] = None
) -> object:
    require_session(game_id, ekaizen_session)
    game = repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    metrics = game.metrics_history[-1] if game.metrics_history else None
    dev_mvp = max(game.developers, key=lambda dev: dev.clean_cards_delivered)
    return {
        "verdict": game.verdict.value,
        "accumulated_profit": game.accumulated_profit,
        "budget": game.budget,
        "oee_avg": round(
            sum(item.oee for item in game.metrics_history) / max(1, len(game.metrics_history)), 3
        ),
        "lead_time_avg": metrics.lead_time_avg if metrics is not None else 0,
        "throughput_avg": round(
            sum(item.delivered_cards for item in game.metrics_history)
            / max(1, len(game.metrics_history)),
            2,
        ),
        "top_kaizens": jsonable_encoder(top_kaizens(game)),
        "sprint_mvp": best_sprint(game),
        "dev_mvp": dev_mvp.name,
        "badges": game.badges,
        "timeline": jsonable_encoder(game.timeline[-12:]),
    }


def best_sprint(game: object) -> dict[str, int | float]:
    if not hasattr(game, "metrics_history"):
        return {"sprint": 0, "throughput_value": 0, "oee": 0.0}
    typed_game = game
    metrics = max(typed_game.metrics_history, key=lambda item: (item.throughput_value, item.oee), default=None)
    if metrics is None:
        return {"sprint": 0, "throughput_value": 0, "oee": 0.0}
    return {
        "sprint": metrics.sprint,
        "throughput_value": metrics.throughput_value,
        "oee": metrics.oee,
    }


def sign_session(game_id: str) -> str:
    digest = hmac.new(SECRET.encode(), game_id.encode(), hashlib.sha256).hexdigest()
    return f"{game_id}.{digest}"


def require_session(game_id: str, cookie: str | None) -> None:
    if cookie is None:
        raise HTTPException(status_code=401, detail="Missing session cookie")
    if not hmac.compare_digest(cookie, sign_session(game_id)):
        raise HTTPException(status_code=401, detail="Invalid session cookie")


def encode_game(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: encode_game(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [encode_game(item) for item in value]
    if isinstance(value, dict):
        return {str(key): encode_game(item) for key, item in value.items()}
    return value

