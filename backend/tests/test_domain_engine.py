from app.domain.engine import (
    allocate_dev,
    apply_kaizen,
    create_game,
    move_card,
    process_sprint,
)
from app.domain.models import Column, KaizenType


def test_process_sprint_applies_progress_and_moral_drain() -> None:
    game = create_game(123)
    card = game.cards[0]
    dev = game.developers[0]
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

