from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Column, KaizenType


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateGameRequest(StrictRequest):
    seed: int | None = None


class MoveCardPayload(StrictRequest):
    type: Literal["move-card"]
    card_id: str
    target: Column


class AllocateDevPayload(StrictRequest):
    type: Literal["allocate-dev"]
    dev_id: str
    card_id: str | None = None


class HireCandidatePayload(StrictRequest):
    type: Literal["hire-candidate"]
    candidate_id: str


class ApplyKaizenPayload(StrictRequest):
    type: Literal["apply-kaizen"]
    kaizen: KaizenType
    target_id: str | None = None


class ProcessSprintPayload(StrictRequest):
    type: Literal["process-sprint"]


CommandPayload = Annotated[
    MoveCardPayload
    | AllocateDevPayload
    | HireCandidatePayload
    | ApplyKaizenPayload
    | ProcessSprintPayload,
    Field(discriminator="type"),
]


class CommandRequest(StrictRequest):
    command_id: str
    payload: CommandPayload
