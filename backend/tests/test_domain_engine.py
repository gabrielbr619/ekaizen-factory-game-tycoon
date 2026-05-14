import random

from app.domain.engine import (
    allocate_dev,
    apply_kaizen,
    calculate_heijunka_bonus,
    calculate_oee,
    create_game,
    move_card,
    process_sprint,
)
from app.domain.models import (
    Card,
    CardSize,
    CardType,
    Column,
    Developer,
    KaizenType,
    Level,
    Specialty,
    SprintMetrics,
)
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.events import apply_event
from app.domain.rules.work import (
    REPUTATION_GAIN_ON_DELIVERY,
    handle_god_tier_retention,
    handle_headhunters,
    handle_raise_requests,
    handle_temporary_contracts,
    level_profile,
    penalize_client,
    specialty_matches,
    sprint_progress,
    stage_required_points,
    update_worker_moral,
)
from app.domain.sprint_processor import RECURRING_REVENUE_PER_ACTIVE_CLIENT


def _developer(dev_id: str, level: Level, specialty: Specialty = Specialty.BACKEND) -> Developer:
    speed, salary, bug_rate = level_profile(level)
    return Developer(dev_id, dev_id, specialty, level, speed, salary, bug_rate, 80, "backend")


def _large_backend_card(card_id: str = "large-card") -> Card:
    return Card(
        id=card_id,
        title="ERP fabril complexo",
        card_type=CardType.FEATURE,
        size=CardSize.G,
        required_specialties=[Specialty.BACKEND],
        points_total=60,
        progress=0,
        value=15_000,
        deadline_sprint=10,
        client_id="c1",
        column=Column.DEVELOPMENT,
        created_sprint=1,
        entered_column_sprint=1,
    )


def test_process_sprint_applies_progress_and_moral_drain() -> None:
    game = create_game(123)
    dev = game.developers[0]
    card = next(item for item in game.cards if specialty_matches(dev, item))
    game = move_card(game, card.id, Column.ANALYSIS)
    card.progress = card.points_total
    game = move_card(game, card.id, Column.DEVELOPMENT)
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
    qa_dev = game.developers[2]
    game = move_card(game, card.id, Column.ANALYSIS)

    try:
        allocate_dev(game, qa_dev.id, card.id)
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


def test_card_cannot_advance_before_current_column_work_is_done() -> None:
    game = create_game(123)
    card = game.cards[0]
    game = move_card(game, card.id, Column.ANALYSIS)

    try:
        move_card(game, card.id, Column.DEVELOPMENT)
    except ValueError as exc:
        assert "coluna atual" in str(exc)
    else:
        raise AssertionError("Expected unfinished analysis to block movement")


def test_analysis_and_qa_use_smaller_stage_effort_than_development() -> None:
    game = create_game(123)
    card = game.cards[0]

    card.column = Column.ANALYSIS
    assert stage_required_points(card) < card.points_total
    card.column = Column.DEVELOPMENT
    assert stage_required_points(card) == card.points_total
    card.column = Column.QA
    assert stage_required_points(card) < card.points_total


def test_qa_worker_matches_qa_column() -> None:
    game = create_game(123)
    card = game.cards[0]
    qa_dev = next(dev for dev in game.developers if dev.specialty == Specialty.QA)
    card.column = Column.QA
    card.assigned_dev_ids = [qa_dev.id]
    initial_moral = qa_dev.moral

    update_worker_moral(game, card, [qa_dev])

    assert qa_dev.moral == initial_moral - 2


def test_moving_completed_qa_card_to_done_pays_value_once() -> None:
    game = create_game(123)
    card = game.cards[0]
    dev = game.developers[0]
    card.column = Column.QA
    card.progress = stage_required_points(card)
    card.assigned_dev_ids = [dev.id]
    client = next(item for item in game.clients if item.id == card.client_id)
    initial_reputation = client.reputation
    initial_budget = game.budget

    try:
        move_card(game, card.id, Column.DONE)
    except ValueError as exc:
        assert "fim da sprint" in str(exc)
    else:
        raise AssertionError("Expected manual QA to Done movement to be rejected")

    game = process_sprint(game)

    assert card.column == Column.DONE
    assert card.assigned_dev_ids == []
    assert dev.cards_delivered == 1
    assert game.budget == initial_budget + card.value + (
        3 * RECURRING_REVENUE_PER_ACTIVE_CLIENT
    ) - game.fixed_cost - sum(
        item.salary for item in game.developers if item.active
    )
    assert client.reputation == min(100, initial_reputation + REPUTATION_GAIN_ON_DELIVERY)


def test_undetected_qa_bug_emerges_later_as_production_bug() -> None:
    game = create_game(6)
    card = game.cards[0]
    qa_dev = next(dev for dev in game.developers if dev.specialty == Specialty.QA)
    qa_dev.bug_rate = 1.0
    card.column = Column.QA
    card.progress = stage_required_points(card)
    card.assigned_dev_ids = [qa_dev.id]
    card.latent_bug = True
    initial_reputation = next(
        client for client in game.clients if client.id == card.client_id
    ).reputation

    game = process_sprint(game)

    assert card.column == Column.DONE
    assert game.scheduled_production_bugs
    due_sprint = game.scheduled_production_bugs[0].due_sprint
    while game.sprint <= due_sprint:
        game = process_sprint(game)

    client = next(item for item in game.clients if item.id == card.client_id)
    assert client.reputation <= initial_reputation
    assert any(
        item.card_type == CardType.BUG
        and card.title in item.title
        and item.column == Column.BACKLOG
        for item in game.cards
    )


def test_card_is_cancelled_after_three_late_sprints() -> None:
    game = create_game(123)
    card = game.cards[0]
    client = next(item for item in game.clients if item.id == card.client_id)
    card.column = Column.ANALYSIS
    card.deadline_sprint = game.sprint - 3
    initial_reputation = client.reputation

    game = process_sprint(game)

    assert card not in game.cards
    assert client.reputation == initial_reputation - 40
    assert any(event.kind == "cancel" and card.title in event.message for event in game.timeline)


def test_active_clients_generate_recurring_revenue() -> None:
    game = create_game(123)
    initial_budget = game.budget

    game = process_sprint(game)

    assert game.budget == initial_budget + (
        3 * RECURRING_REVENUE_PER_ACTIVE_CLIENT
    ) - game.fixed_cost - sum(
        item.salary for item in game.developers if item.active
    )


def test_client_cancels_on_next_sprint_after_reputation_drops_below_threshold() -> None:
    game = create_game(123)
    client = game.clients[0]
    client.reputation = 31

    penalize_client(game, client.id, 5)

    assert client.active
    assert client.cancellation_sprint == game.sprint + 1
    game.sprint += 1
    game = process_sprint(game)
    assert not client.active


def test_god_tier_profile_matches_pdf() -> None:
    assert level_profile(Level.GOD_TIER) == (40, 3_500, 0.005)


def test_oee_calculation() -> None:
    game = create_game(123)
    game.cards[0].column = Column.QA

    assert calculate_oee(game, delivered=1, delivered_on_time=1, production_bugs=0) == 1.0
    assert calculate_oee(game, delivered=1, delivered_on_time=0, production_bugs=0) == 0.0
    assert calculate_oee(game, delivered=1, delivered_on_time=1, production_bugs=1) == 0.0


def test_oee_availability_drops_when_dev_moral_is_below_burnout_threshold() -> None:
    game = create_game(123)
    game.developers[0].moral = 29

    assert calculate_oee(game, delivered=0, delivered_on_time=0, production_bugs=0) == 0.667


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

    assert calculate_heijunka_bonus(game, delivered=2, value=10_000) == 0
    game.metrics_history = [
        SprintMetrics(
            sprint=index,
            delivered_cards=3,
            throughput_value=6_000,
            oee=0.8,
            lead_time_avg=1.0,
            bugs_in_production=0,
            heijunka_bonus=0,
        )
        for index in range(1, 5)
    ]
    assert calculate_heijunka_bonus(game, delivered=3, value=10_000) == 1_000
    assert game.heijunka_streak == 1


def test_seed_reproduces_initial_state() -> None:
    first = create_game(456)
    second = create_game(456)

    assert [card.title for card in first.cards] == [card.title for card in second.cards]
    assert [candidate.level for candidate in first.candidates] == [
        candidate.level for candidate in second.candidates
    ]


def test_urgent_client_event_adds_playable_short_deadline_card() -> None:
    game = create_game(123)
    initial_cards = len(game.cards)

    message = apply_event(game, "urgent-client", random.Random(1))

    urgent_card = game.cards[-1]
    assert "Cliente urgente" in message
    assert len(game.cards) == initial_cards + 1
    assert urgent_card.card_type == CardType.HOTFIX
    assert urgent_card.value > 15_000
    assert urgent_card.deadline_sprint == game.sprint + 2
    assert urgent_card.column == Column.BACKLOG


def test_referral_event_adds_discount_candidate_to_pool() -> None:
    game = create_game(123)
    initial_candidates = len(game.candidates)

    message = apply_event(game, "referral", random.Random(2))

    candidate = game.candidates[-1]
    profile_salary = level_profile(candidate.level)[1]
    assert "Indicacao" in message
    assert len(game.candidates) == initial_candidates + 1
    assert candidate.salary == int(profile_salary * 0.8)
    assert candidate.expires_after_sprint == game.sprint + 1


def test_retro_bug_event_turns_done_card_into_backlog_bug() -> None:
    game = create_game(123)
    done_card = game.cards[0]
    done_card.column = Column.DONE

    message = apply_event(game, "retro-bug", random.Random(3))

    bug_card = game.cards[-1]
    assert "Bug retroativo" in message
    assert bug_card.card_type == CardType.BUG
    assert done_card.title in bug_card.title
    assert bug_card.column == Column.BACKLOG
    assert bug_card.deadline_sprint == game.sprint + 3


def test_urgent_client_event_penalizes_reputation_when_backlog_wip_is_full() -> None:
    game = create_game(123)
    game.wip_limits[Column.BACKLOG.value] = 0
    client_reputations = {client.id: client.reputation for client in game.clients}
    initial_cards = len(game.cards)

    message = apply_event(game, "urgent-client", random.Random(1))

    assert message == "Cliente urgente: Backlog cheio recusou demanda e reputacao caiu."
    assert len(game.cards) == initial_cards
    assert any(client.reputation < client_reputations[client.id] for client in game.clients)


def test_junior_alone_on_large_card_makes_no_progress() -> None:
    game = create_game(123)
    junior = _developer("junior", Level.JUNIOR)
    card = _large_backend_card()
    game.developers = [junior]
    game.cards = [card]
    card.assigned_dev_ids = [junior.id]

    game = process_sprint(game)

    assert card.progress == 0
    assert junior.moral < 80


def test_andon_warns_before_sprint_when_junior_is_alone_on_large_card() -> None:
    game = create_game(123)
    junior = _developer("junior", Level.JUNIOR)
    card = _large_backend_card()
    game.developers = [junior]
    game.cards = [card]
    card.assigned_dev_ids = [junior.id]

    game = refresh_alerts(game)

    assert any(
        alert.code == "large-card-junior-alone"
        and "junior sozinho em card G" in alert.message
        and card.title in alert.message
        for alert in game.andon_alerts
    )


def test_pleno_needs_senior_mentor_on_large_card() -> None:
    game = create_game(123)
    pleno = _developer("pleno", Level.PLENO)
    senior = _developer("senior", Level.SENIOR)
    card = _large_backend_card()
    game.developers = [pleno, senior]
    game.cards = [card]
    card.assigned_dev_ids = [pleno.id]

    game = process_sprint(game)

    assert card.progress == 0

    card.progress = 0
    card.assigned_dev_ids = [pleno.id, senior.id]
    game = process_sprint(game)

    assert card.progress > 0


def test_andon_warns_before_sprint_when_pleno_lacks_large_card_mentor() -> None:
    game = create_game(123)
    pleno = _developer("pleno", Level.PLENO)
    junior = _developer("junior", Level.JUNIOR)
    card = _large_backend_card()
    game.developers = [pleno, junior]
    game.cards = [card]
    card.assigned_dev_ids = [pleno.id, junior.id]

    game = refresh_alerts(game)

    assert any(
        alert.code == "large-card-pleno-no-mentor"
        and "precisa de mentor Senior/God-tier" in alert.message
        and card.title in alert.message
        for alert in game.andon_alerts
    )


def test_brooks_law_overstaffing_increases_moral_drain_and_bug_risk() -> None:
    game = create_game(123)
    workers = [_developer(f"senior-{index}", Level.SENIOR) for index in range(5)]
    card = _large_backend_card()

    progress = sprint_progress(game, card, workers, random.Random(1))
    update_worker_moral(game, card, workers)

    assert progress > 0
    assert card.latent_bug
    assert all(worker.moral == 75 for worker in workers)


def test_rest_space_kaizen_reduces_active_work_moral_drain() -> None:
    game = create_game(123)
    worker = _developer("senior", Level.SENIOR)
    card = _large_backend_card()
    game.active_kaizens.append(KaizenType.REST_SPACE)

    update_worker_moral(game, card, [worker])

    assert worker.moral == 79


def test_god_tier_leaves_after_three_trivial_sprints() -> None:
    game = create_game(123)
    god = _developer("god", Level.GOD_TIER)
    card = game.cards[0]
    card.size = CardSize.P
    card.column = Column.DEVELOPMENT
    card.progress = 0
    card.points_total = 10
    card.assigned_dev_ids = [god.id]
    game.developers = [god]
    initial_reputations = {client.id: client.reputation for client in game.clients}

    for _ in range(3):
        card.column = Column.DEVELOPMENT
        card.progress = 0
        card.assigned_dev_ids = [god.id]
        game = process_sprint(game)

    assert not god.active
    assert all(
        client.reputation == initial_reputations[client.id] - 15 for client in game.clients
    )


def test_god_tier_leaves_without_targeted_kaizen_every_eight_sprints() -> None:
    game = create_game(123)
    god = _developer("god", Level.GOD_TIER)
    god.god_last_kaizen_sprint = game.sprint
    game.developers = [god]
    game.cards = []
    game.sprint = 8

    handle_god_tier_retention(game)

    assert not god.active
    assert any(
        event.kind == "god-tier-exit" and "Kaizen" in event.message
        for event in game.timeline
    )


def test_targeted_kaizen_recognition_resets_god_tier_eight_sprint_timer() -> None:
    game = create_game(123)
    god = _developer("god", Level.GOD_TIER)
    god.god_last_kaizen_sprint = game.sprint
    game.developers = [god]
    game.cards = []
    game.sprint = 8

    game.kaizen_points = 1
    game = apply_kaizen(game, KaizenType.TRAIN_DEV, god.id)
    handle_god_tier_retention(game)

    assert god.active
    assert god.god_last_kaizen_sprint == 8
    assert god.onboarding_sprints == 0


def test_raise_request_event_sets_salary_deadline_and_dev_leaves_if_unanswered() -> None:
    game = create_game(123)
    dev = game.developers[0]
    initial_reputations = {client.id: client.reputation for client in game.clients}

    message = apply_event(game, "raise-request", random.Random(4))

    assert "Pedido de aumento" in message
    assert dev.raise_request_deadline_sprint == game.sprint + 2
    assert dev.raise_requested_salary == int(dev.salary * 1.2)
    deadline = dev.raise_request_deadline_sprint
    assert deadline is not None

    game.sprint = deadline
    game.budget = -3_000
    handle_raise_requests(game)

    assert not dev.active
    assert all(
        client.reputation == initial_reputations[client.id] - 5 for client in game.clients
    )


def test_raise_request_is_accepted_when_budget_can_absorb_salary_increase() -> None:
    game = create_game(123)
    dev = game.developers[0]

    apply_event(game, "raise-request", random.Random(4))
    requested_salary = dev.raise_requested_salary
    deadline = dev.raise_request_deadline_sprint
    assert requested_salary is not None
    assert deadline is not None

    game.sprint = deadline
    handle_raise_requests(game)

    assert dev.active
    assert dev.salary == requested_salary
    assert dev.raise_request_deadline_sprint is None
    assert dev.raise_requested_salary is None


def test_headhunter_event_targets_senior_and_retention_cost_is_processed() -> None:
    game = create_game(123)
    senior = _developer("senior", Level.SENIOR)
    game.developers = [senior]

    message = apply_event(game, "headhunter", random.Random(7))
    requested_salary = senior.headhunter_salary
    deadline = senior.headhunter_deadline_sprint
    assert "Headhunter" in message
    assert requested_salary == int(1_500 * 1.5)
    assert deadline == game.sprint + 2

    game.sprint = deadline
    handle_headhunters(game)

    assert senior.active
    assert senior.salary == requested_salary
    assert senior.headhunter_deadline_sprint is None


def test_conference_event_gives_moral_and_blocks_one_productive_sprint() -> None:
    game = create_game(123)
    dev = game.developers[0]
    card = _large_backend_card()
    game.cards = [card]
    game.developers = [dev]
    card.assigned_dev_ids = [dev.id]
    dev.moral = 60

    message = apply_event(game, "conference", random.Random(8))
    progress = sprint_progress(game, card, [dev], random.Random(9))

    assert "Conferencia" in message
    assert dev.moral == 80
    assert dev.conference_return_sprint == game.sprint
    assert progress == 0


def test_non_stacking_kaizen_cannot_charge_points_twice() -> None:
    game = create_game(123)
    game.kaizen_points = 3

    game = apply_kaizen(game, KaizenType.QA_AUTOMATION)

    try:
        apply_kaizen(game, KaizenType.QA_AUTOMATION)
    except ValueError as exc:
        assert "ja esta ativo" in str(exc)
    else:
        raise AssertionError("Expected repeated permanent Kaizen to be rejected")
    assert game.kaizen_points == 1


def test_interns_leave_after_five_sprints() -> None:
    game = create_game(123)
    game.kaizen_points = 1
    game = apply_kaizen(game, KaizenType.INTERNS)
    interns = [dev for dev in game.developers if dev.id.startswith("intern-")]

    assert len(interns) == 3
    assert all(dev.contract_ends_sprint == game.sprint + 5 for dev in interns)

    game.sprint += 5
    handle_temporary_contracts(game)

    assert all(not dev.active for dev in interns)


def test_oee_audit_event_cancels_lowest_reputation_client_when_average_oee_is_bad() -> None:
    game = create_game(123)
    game.metrics_history = [
        SprintMetrics(
            sprint=index,
            delivered_cards=1,
            throughput_value=1_000,
            oee=0.2,
            lead_time_avg=3.0,
            bugs_in_production=0,
            heijunka_bonus=0,
        )
        for index in range(1, 5)
    ]
    game.clients[0].reputation = 55
    game.clients[1].reputation = 45
    game.clients[2].reputation = 65

    message = apply_event(game, "oee-audit", random.Random(5))
    game = process_sprint(game)

    assert "Auditoria de OEE" in message
    assert game.clients[1].active is False
    assert any(event.kind == "oee-audit" for event in game.timeline)


def test_market_trend_event_adds_extra_specialty_demand_for_five_sprints() -> None:
    game = create_game(123)
    game.sprint = 31
    game.cards = []

    message = apply_event(game, "market-trend", random.Random(6))
    trended_specialty = game.market_trends[0].specialty
    initial_cards = len(game.cards)

    game = process_sprint(game)

    new_cards = game.cards[initial_cards:]
    assert "Tendencia de mercado" in message
    assert len(new_cards) >= 2
    assert any(card.required_specialties == [trended_specialty] for card in new_cards)
    assert game.market_trends[0].expires_after_sprint == 36
