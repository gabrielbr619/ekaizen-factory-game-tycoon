from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.command_dispatcher import apply_command_payload
from app.api.hall import build_hall_of_kaizen_response
from app.api.schemas import CommandRequest, CreateGameRequest
from app.api.security import hash_command, is_valid_session, sign_session
from app.api.serialization import encode_game
from app.domain.engine import create_game
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
    repo.ping()
    return {"status": "ok"}


@app.post("/games")
def start_game(body: CreateGameRequest, response: Response) -> object:
    game = create_game(body.seed)
    repo.save(game)
    response.set_cookie(
        "ekaizen_session",
        sign_session(game.id, SECRET),
        httponly=True,
        samesite="lax",
    )
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
    command_hash = hash_command(body.payload.model_dump(mode="json"))
    try:
        previous = repo.get_idempotent(game_id, command_id, command_hash)
        if previous is not None:
            return encode_game(previous)
        game = repo.get(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        game = apply_command_payload(game, body.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    repo.save_idempotent(game, command_id, command_hash)
    return encode_game(game)


@app.get("/games/{game_id}/events")
async def game_events(
    game_id: str, ekaizen_session: Annotated[str | None, Cookie()] = None
) -> StreamingResponse:
    require_session(game_id, ekaizen_session)

    async def stream() -> AsyncIterator[str]:
        for _ in range(5):
            game = repo.get(game_id)
            if game is not None:
                payload = json.dumps(encode_game(game), ensure_ascii=False)
                yield f"event: state\ndata: {payload}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/games/{game_id}/hall-of-kaizen")
def hall_of_kaizen(game_id: str, ekaizen_session: Annotated[str | None, Cookie()] = None) -> object:
    require_session(game_id, ekaizen_session)
    game = repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return build_hall_of_kaizen_response(game)


def require_session(game_id: str, cookie: str | None) -> None:
    if cookie is None:
        raise HTTPException(status_code=401, detail="Missing session cookie")
    if not is_valid_session(game_id, cookie, SECRET):
        raise HTTPException(status_code=401, detail="Invalid session cookie")
