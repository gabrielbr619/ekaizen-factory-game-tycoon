from __future__ import annotations

from app.api.schemas import (
    AllocateDevPayload,
    ApplyKaizenPayload,
    CommandPayload,
    HireCandidatePayload,
    MoveCardPayload,
    ProcessSprintPayload,
)
from app.domain.engine import (
    allocate_dev,
    apply_kaizen,
    hire_candidate,
    move_card,
    process_sprint,
)
from app.domain.models import GameState


def apply_command_payload(game: GameState, payload: CommandPayload) -> GameState:
    if isinstance(payload, MoveCardPayload):
        return move_card(game, payload.card_id, payload.target)
    if isinstance(payload, AllocateDevPayload):
        return allocate_dev(game, payload.dev_id, payload.card_id)
    if isinstance(payload, HireCandidatePayload):
        return hire_candidate(game, payload.candidate_id)
    if isinstance(payload, ApplyKaizenPayload):
        return apply_kaizen(game, payload.kaizen, payload.target_id)
    if isinstance(payload, ProcessSprintPayload):
        return process_sprint(game)
    raise ValueError("Payload de comando invalido.")
