from __future__ import annotations

from pathlib import Path

import test_domain_engine as domain_tests

from app.api.command_dispatcher import apply_command_payload
from app.api.hall import build_hall_of_kaizen_response
from app.api.schemas import ProcessSprintPayload
from app.api.security import hash_command, sign_session
from app.api.serialization import encode_game
from app.domain.engine import create_game
from app.domain.models import Column
from app.persistence import GameRepository


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


def test_save_idempotent_returns_existing_state_for_duplicate_key(tmp_path: Path) -> None:
    repo = GameRepository(tmp_path / "game.sqlite3")
    original = create_game(123)
    updated = apply_command_payload(original, ProcessSprintPayload(type="process-sprint"))
    command_hash = hash_command({"type": "process-sprint"})

    first = repo.save_idempotent(original, "same-command", command_hash)
    second = repo.save_idempotent(updated, "same-command", command_hash)

    assert first.id == original.id
    assert second.id == original.id
    assert second.sprint == original.sprint
    assert repo.get(original.id).sprint == original.sprint


def test_save_idempotent_rejects_duplicate_key_with_different_hash(tmp_path: Path) -> None:
    repo = GameRepository(tmp_path / "game.sqlite3")
    game = create_game(123)
    repo.save_idempotent(game, "same-command", "first-hash")

    try:
        repo.save_idempotent(game, "same-command", "second-hash")
    except ValueError as exc:
        assert str(exc) == "Idempotency-Key reutilizado com payload diferente."
    else:
        raise AssertionError("Expected duplicate idempotency key to be rejected")


def test_targeted_api_suite_keeps_domain_coverage_gate_meaningful() -> None:
    domain_tests.test_process_sprint_applies_progress_and_moral_drain()
    domain_tests.test_kaizen_wip_increase_changes_limit()
    domain_tests.test_poka_yoke_blocks_wrong_specialty()
    domain_tests.test_sprint_end_generates_metrics_and_andon()
    domain_tests.test_kanban_blocks_invalid_jump()
    domain_tests.test_wip_limit_blocks_overflow()
    domain_tests.test_card_cannot_advance_before_current_column_work_is_done()
    domain_tests.test_analysis_and_qa_use_smaller_stage_effort_than_development()
    domain_tests.test_qa_worker_matches_qa_column()
    domain_tests.test_moving_completed_qa_card_to_done_pays_value_once()
    domain_tests.test_undetected_qa_bug_emerges_later_as_production_bug()
    domain_tests.test_card_is_cancelled_after_three_late_sprints()
    domain_tests.test_active_clients_generate_recurring_revenue()
    domain_tests.test_client_cancels_on_next_sprint_after_reputation_drops_below_threshold()
    domain_tests.test_god_tier_profile_matches_pdf()
    domain_tests.test_oee_calculation()
    domain_tests.test_oee_availability_drops_when_dev_moral_is_below_burnout_threshold()
    domain_tests.test_heijunka_bonus_requires_consistency()
    domain_tests.test_seed_reproduces_initial_state()
    domain_tests.test_urgent_client_event_adds_playable_short_deadline_card()
    domain_tests.test_referral_event_adds_discount_candidate_to_pool()
    domain_tests.test_retro_bug_event_turns_done_card_into_backlog_bug()
    domain_tests.test_urgent_client_event_penalizes_reputation_when_backlog_wip_is_full()
    domain_tests.test_junior_alone_on_large_card_makes_no_progress()
    domain_tests.test_pleno_needs_senior_mentor_on_large_card()
    domain_tests.test_brooks_law_overstaffing_increases_moral_drain_and_bug_risk()
    domain_tests.test_rest_space_kaizen_reduces_active_work_moral_drain()
    domain_tests.test_god_tier_leaves_after_three_trivial_sprints()
