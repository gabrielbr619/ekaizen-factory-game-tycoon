from app.domain.engine import (
    allocate_dev,
    apply_kaizen,
    calculate_heijunka_bonus,
    calculate_oee,
    create_game,
    move_card,
    process_sprint,
)
from app.domain.models import Column, KaizenType, SprintMetrics


def test_process_sprint_applies_progress_and_moral_drain() -> None:
    game = create_game(123)
    dev = game.developers[0]
    card = next(item for item in game.cards if dev.specialty in item.required_specialties)
    game = move_card(game, card.id, Column.ANALYSIS)
    game = allocate_dev(game, dev.id, card.id)
    initial_moral = dev.moral

    game = process_sprint(game)

    updated = next(item for item in game.cards if item.id == card.id)
    updated_dev = next(item for item in game.developers if item.id == dev.id)
    assert updated.progress > 0
    assert updated_dev.moral < initial_moral


def test_kaizen_wip_increase_changes_limit() -> None:
    game = create_game(123)
    game.kaizen_points = 1

    game = apply_kaizen(game, KaizenType.WIP_INCREASE, Column.DEVELOPMENT.value)

    assert game.wip_limits[Column.DEVELOPMENT.value] == 7
    assert KaizenType.WIP_INCREASE in game.active_kaizens


def test_poka_yoke_blocks_wrong_specialty() -> None:
    game = create_game(123)
    game.kaizen_points = 1
    game = apply_kaizen(game, KaizenType.POKA_YOKE)
    card = game.cards[0]
    po_dev = game.developers[1]
    game = move_card(game, card.id, Column.ANALYSIS)

    try:
        allocate_dev(game, po_dev.id, card.id)
    except ValueError as exc:
        assert "Poka-Yoke" in str(exc)
    else:
        raise AssertionError("Expected Poka-Yoke to reject wrong specialty")


def test_sprint_end_generates_metrics_and_andon() -> None:
    game = create_game(123)

    game = process_sprint(game)

    assert game.metrics_history
    assert game.andon_alerts


def test_kanban_blocks_invalid_jump() -> None:
    game = create_game(123)
    card = game.cards[0]

    try:
        move_card(game, card.id, Column.DEVELOPMENT)
    except ValueError as exc:
        assert "uma coluna por vez" in str(exc)
    else:
        raise AssertionError("Expected invalid jump to be rejected")


def test_wip_limit_blocks_overflow() -> None:
    game = create_game(123)
    game.wip_limits[Column.ANALYSIS.value] = 0
    card = game.cards[0]

    try:
        move_card(game, card.id, Column.ANALYSIS)
    except ValueError as exc:
        assert "WIP limit" in str(exc)
    else:
        raise AssertionError("Expected WIP overflow to be rejected")


def test_oee_calculation() -> None:
    game = create_game(123)
    game.cards[0].column = Column.QA

    assert calculate_oee(game, delivered=1, production_bugs=0) == 1.0
    assert calculate_oee(game, delivered=1, production_bugs=1) == 0.0


def test_heijunka_bonus_requires_consistency() -> None:
    game = create_game(123)
    game.active_kaizens.append(KaizenType.HEIJUNKA)
    game.metrics_history = [
        SprintMetrics(
            sprint=index,
            delivered_cards=2,
            throughput_value=2_000,
            oee=0.8,
            lead_time_avg=1.0,
            bugs_in_production=0,
            heijunka_bonus=0,
        )
        for index in range(1, 5)
    ]

    assert calculate_heijunka_bonus(game, delivered=2, value=10_000) == 1_000
    assert game.heijunka_streak == 1


def test_seed_reproduces_initial_state() -> None:
    first = create_game(456)
    second = create_game(456)

    assert [card.title for card in first.cards] == [card.title for card in second.cards]
    assert [candidate.level for candidate in first.candidates] == [
        candidate.level for candidate in second.candidates
    ]
