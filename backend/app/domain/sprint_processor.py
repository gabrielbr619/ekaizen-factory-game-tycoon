from __future__ import annotations

import random

from app.domain.game_factory import generate_candidates, generate_cards
from app.domain.models import Column, GameState, SprintMetrics, TimelineEvent, Verdict
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.events import generate_events
from app.domain.rules.flow import active_cards, cards_in_work
from app.domain.rules.metrics import average_lead_time, calculate_heijunka_bonus, calculate_oee
from app.domain.rules.verdict import update_badges, update_verdict
from app.domain.rules.work import (
    bug_happens,
    find_dev,
    finish_card,
    handle_resignations,
    payroll,
    penalize_client,
    qa_detection_chance,
    recover_idle_morale,
    sprint_progress,
    update_worker_moral,
)


def process_sprint(game: GameState) -> GameState:
    if game.verdict != Verdict.PLAYING:
        return game
    rng = random.Random(game.seed + game.sprint * 97)
    delivered = 0
    throughput_value = 0
    production_bugs = 0
    for card in cards_in_work(game):
        workers = [find_dev(game, dev_id) for dev_id in card.assigned_dev_ids]
        if not workers:
            continue
        card.progress += sprint_progress(game, card, workers, rng)
        update_worker_moral(game, card, workers)
        if card.progress >= card.points_total and card.column == Column.QA:
            if bug_happens(game, card, workers, rng):
                if rng.random() < qa_detection_chance(game, workers):
                    card.column = Column.DEVELOPMENT
                    card.progress = max(0, card.points_total // 2)
                    card.assigned_dev_ids = []
                    game.timeline.append(
                        TimelineEvent(game.sprint, "qa-bug", f"QA encontrou bug em {card.title}.")
                    )
                else:
                    production_bugs += 1
                    card.blocked_by_jidoka = True
                    penalize_client(game, card.client_id, 20)
            else:
                delivered += 1
                throughput_value += card.value
                finish_card(game, card, workers)
    recover_idle_morale(game)
    for card in active_cards(game):
        if game.sprint > card.deadline_sprint and card.column != Column.DONE:
            penalize_client(game, card.client_id, 15)
    heijunka_bonus = calculate_heijunka_bonus(game, delivered, throughput_value)
    sprint_cost = game.fixed_cost + payroll(game)
    game.budget += throughput_value + heijunka_bonus - sprint_cost
    game.accumulated_profit += throughput_value + heijunka_bonus - sprint_cost
    game.sprint += 1
    if game.sprint <= 30:
        game.phase = "recovery"
    elif game.sprint <= 35:
        game.phase = "stabilization"
    if game.sprint % 5 == 1:
        game.kaizen_points += 1
    if game.sprint % 3 == 1:
        game.candidates = generate_candidates(game)
    game.cards.extend(generate_cards(game, 2 + min(3, game.sprint // 8)))
    game.pending_events = generate_events(game, rng)
    handle_resignations(game, rng)
    metrics = SprintMetrics(
        sprint=game.sprint - 1,
        delivered_cards=delivered,
        throughput_value=throughput_value,
        oee=calculate_oee(game, delivered, production_bugs),
        lead_time_avg=average_lead_time(game),
        bugs_in_production=production_bugs,
        heijunka_bonus=heijunka_bonus,
    )
    game.metrics_history.append(metrics)
    update_badges(game, metrics)
    update_verdict(game)
    return refresh_alerts(game)
