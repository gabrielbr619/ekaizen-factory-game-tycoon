from __future__ import annotations

from app.domain.models import Column, GameState, KaizenType


def calculate_heijunka_bonus(game: GameState, delivered: int, value: int) -> int:
    recent = [metric.delivered_cards for metric in game.metrics_history[-4:]] + [delivered]
    if KaizenType.HEIJUNKA not in game.active_kaizens or len(recent) < 5:
        return 0
    average = sum(recent) / len(recent)
    variance = max(recent) - min(recent)
    if average > 0 and variance <= 1:
        game.heijunka_streak += 1
        return int(value * 0.10)
    game.heijunka_streak = 0
    return 0


def calculate_oee(game: GameState, delivered: int, production_bugs: int) -> float:
    active_devs = [dev for dev in game.developers if dev.active]
    if not active_devs:
        return 0.0
    availability = sum(1 for dev in active_devs if dev.moral >= 30) / len(active_devs)
    committed = sum(1 for card in game.cards if card.column in {Column.QA, Column.DONE})
    performance = 1.0 if committed == 0 else min(1.0, delivered / committed)
    quality = 1.0 if delivered == 0 else max(0.0, (delivered - production_bugs) / delivered)
    return round(availability * performance * quality, 3)


def current_oee(game: GameState) -> float:
    if not game.metrics_history:
        return 0.6
    return game.metrics_history[-1].oee


def average_lead_time(game: GameState) -> float:
    done_cards = [card for card in game.cards if card.column == Column.DONE]
    if not done_cards:
        return 0.0
    total = sum(sum(card.cycle_times.values()) for card in done_cards)
    return round(total / len(done_cards), 2)


def reputation(game: GameState) -> int:
    active_clients = [client for client in game.clients if client.active]
    if not active_clients:
        return 0
    return round(sum(client.reputation for client in active_clients) / len(active_clients))
