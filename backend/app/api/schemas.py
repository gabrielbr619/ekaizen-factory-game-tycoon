from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.domain.models import Column, KaizenType


class CreateGameRequest(BaseModel):
    seed: int | None = None


class MoveCardPayload(BaseModel):
    type: Literal["move-card"]
    card_id: str
    target: Column


class AllocateDevPayload(BaseModel):
    type: Literal["allocate-dev"]
    dev_id: str
    card_id: str | None = None


class HireCandidatePayload(BaseModel):
    type: Literal["hire-candidate"]
    candidate_id: str


class ApplyKaizenPayload(BaseModel):
    type: Literal["apply-kaizen"]
    kaizen: KaizenType
    target_id: str | None = None


class ProcessSprintPayload(BaseModel):
    type: Literal["process-sprint"]


CommandPayload = Annotated[
    MoveCardPayload
    | AllocateDevPayload
    | HireCandidatePayload
    | ApplyKaizenPayload
    | ProcessSprintPayload,
    Field(discriminator="type"),
]


class CommandRequest(BaseModel):
    command_id: str
    payload: CommandPayload
