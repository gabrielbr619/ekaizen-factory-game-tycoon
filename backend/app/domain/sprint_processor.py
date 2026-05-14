from __future__ import annotations

import random

from app.domain.game_factory import generate_candidates, generate_cards
from app.domain.models import (
    Card,
    CardType,
    Column,
    GameState,
    ScheduledProductionBug,
    SprintMetrics,
    TimelineEvent,
    Verdict,
)
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.events import generate_events
from app.domain.rules.flow import active_cards, cards_in_work
from app.domain.rules.metrics import (
    average_cycle_time_by_column,
    average_lead_time,
    calculate_heijunka_bonus,
    calculate_oee,
)
from app.domain.rules.verdict import update_badges, update_verdict
from app.domain.rules.work import (
    bug_happens,
    find_dev,
    finish_card,
    handle_god_tier_retention,
    handle_raise_requests,
    handle_resignations,
    payroll,
    penalize_client,
    qa_detection_chance,
    recover_idle_morale,
    sprint_progress,
    stage_required_points,
    update_worker_moral,
)

RECURRING_REVENUE_PER_ACTIVE_CLIENT = 1_700


def _resolve_scheduled_production_bugs(game: GameState) -> int:
    due_bugs = [
        bug for bug in game.scheduled_production_bugs if bug.due_sprint <= game.sprint
    ]
    game.scheduled_production_bugs = [
        bug for bug in game.scheduled_production_bugs if bug.due_sprint > game.sprint
    ]
    for bug in due_bugs:
        penalize_client(game, bug.client_id, 20)
        game.cards.append(
            Card(
                id=f"prod-bug-{game.sprint}-{bug.source_card_id}",
                title=f"Bug em producao: {bug.source_title}",
                card_type=CardType.BUG,
                size=bug.size,
                required_specialties=list(bug.required_specialties),
                points_total=8 if bug.size.value == "P" else 25 if bug.size.value == "M" else 60,
                progress=0,
                value=0,
                deadline_sprint=game.sprint + 4,
                client_id=bug.client_id,
                column=Column.BACKLOG,
                created_sprint=game.sprint,
                entered_column_sprint=game.sprint,
            )
        )
        game.timeline.append(
            TimelineEvent(
                game.sprint,
                "production-bug",
                f"Bug em producao surgiu em {bug.source_title}.",
            )
        )
    return len(due_bugs)


def _resolve_oee_audit(
    game: GameState, audited_sprint: int, pending_audit_sprint: int | None
) -> None:
    if pending_audit_sprint != audited_sprint:
        return
    if game.pending_oee_audit_sprint == pending_audit_sprint:
        game.pending_oee_audit_sprint = None
    if not game.metrics_history:
        return
    average_oee = sum(metric.oee for metric in game.metrics_history) / len(game.metrics_history)
    if average_oee >= 0.5:
        game.timeline.append(
            TimelineEvent(audited_sprint, "oee-audit", "Auditoria de OEE aprovada.")
        )
        return
    active_clients = [client for client in game.clients if client.active]
    if not active_clients:
        return
    lost_client = min(active_clients, key=lambda client: client.reputation)
    lost_client.active = False
    game.timeline.append(
        TimelineEvent(
            audited_sprint,
            "oee-audit",
            f"Auditoria de OEE reprovada: {lost_client.name} cancelou o contrato.",
        )
    )


def process_sprint(game: GameState) -> GameState:
    if game.verdict != Verdict.PLAYING:
        return game
    for client in game.clients:
        cancellation_due = (
            client.cancellation_sprint is not None and game.sprint >= client.cancellation_sprint
        )
        if client.active and cancellation_due:
            client.active = False
            game.timeline.append(
                TimelineEvent(game.sprint, "client-cancel", f"{client.name} cancelou o contrato.")
            )
    rng = random.Random(game.seed + game.sprint * 97)
    pending_audit_sprint = game.pending_oee_audit_sprint
    delivered = 0
    delivered_on_time = 0
    throughput_value = 0
    production_bugs = _resolve_scheduled_production_bugs(game)
    for card in cards_in_work(game):
        workers = [find_dev(game, dev_id) for dev_id in card.assigned_dev_ids]
        if not workers:
            continue
        card.progress += sprint_progress(game, card, workers, rng)
        update_worker_moral(game, card, workers)
        if card.progress >= stage_required_points(card) and card.column == Column.QA:
            if bug_happens(game, card, workers, rng):
                if rng.random() < qa_detection_chance(game, workers):
                    card.column = Column.DEVELOPMENT
                    card.progress = max(0, card.points_total // 2)
                    card.assigned_dev_ids = []
                    game.timeline.append(
                        TimelineEvent(game.sprint, "qa-bug", f"QA encontrou bug em {card.title}.")
                    )
                else:
                    delivered += 1
                    if game.sprint <= card.deadline_sprint:
                        delivered_on_time += 1
                    throughput_value += card.value
                    game.scheduled_production_bugs.append(
                        ScheduledProductionBug(
                            source_card_id=card.id,
                            source_title=card.title,
                            client_id=card.client_id,
                            size=card.size,
                            required_specialties=list(card.required_specialties),
                            due_sprint=game.sprint + rng.randint(1, 3),
                        )
                    )
                    finish_card(game, card, workers, clean=False)
            else:
                delivered += 1
                if game.sprint <= card.deadline_sprint:
                    delivered_on_time += 1
                throughput_value += card.value
                finish_card(game, card, workers)
    recover_idle_morale(game)
    handle_god_tier_retention(game)
    handle_raise_requests(game)
    for card in list(active_cards(game)):
        if game.sprint > card.deadline_sprint and card.column != Column.DONE:
            penalize_client(game, card.client_id, 15)
            if game.sprint - card.deadline_sprint >= 3:
                penalize_client(game, card.client_id, 25)
                card.assigned_dev_ids = []
                game.cards.remove(card)
                game.timeline.append(
                    TimelineEvent(game.sprint, "cancel", f"{card.title} foi cancelado por atraso.")
                )
    heijunka_bonus = calculate_heijunka_bonus(game, delivered, throughput_value)
    recurring_revenue = sum(
        RECURRING_REVENUE_PER_ACTIVE_CLIENT for client in game.clients if client.active
    )
    sprint_cost = game.fixed_cost + payroll(game)
    sprint_result = throughput_value + heijunka_bonus + recurring_revenue - sprint_cost
    game.budget += sprint_result
    game.accumulated_profit += sprint_result
    game.sprint += 1
    if game.sprint <= 30:
        game.phase = "recovery"
    elif game.sprint <= 35:
        game.phase = "stabilization"
    if game.sprint % 5 == 1:
        game.kaizen_points += 1
    if game.sprint % 3 == 1:
        game.candidates = generate_candidates(game)
    if game.sprint <= 20:
        incoming_cards = 1 if game.sprint % 3 == 1 else 0
    elif game.sprint <= 30:
        incoming_cards = 1 if game.sprint % 2 == 1 else 0
    else:
        incoming_cards = 1
    game.cards.extend(generate_cards(game, incoming_cards))
    game.pending_events = generate_events(game, rng)
    handle_resignations(game, rng)
    metrics = SprintMetrics(
        sprint=game.sprint - 1,
        delivered_cards=delivered,
        throughput_value=throughput_value,
        oee=calculate_oee(game, delivered, delivered_on_time, production_bugs),
        lead_time_avg=average_lead_time(game),
        bugs_in_production=production_bugs,
        heijunka_bonus=heijunka_bonus,
        cycle_time_by_column=average_cycle_time_by_column(game),
    )
    game.metrics_history.append(metrics)
    _resolve_oee_audit(game, metrics.sprint, pending_audit_sprint)
    update_badges(game, metrics)
    update_verdict(game)
    return refresh_alerts(game)
