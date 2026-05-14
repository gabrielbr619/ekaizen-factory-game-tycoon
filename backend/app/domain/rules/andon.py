from __future__ import annotations

from app.domain.models import AndonAlert, Card, CardSize, Developer, GameState, Level
from app.domain.rules.flow import active_cards
from app.domain.rules.work import find_dev, has_complexity_mentor, payroll

SEVERITY_PRIORITY = {"danger": 0, "warning": 1, "info": 2, "success": 3}


def _assigned_workers(game: GameState, card: Card) -> list[Developer]:
    return [find_dev(game, dev_id) for dev_id in card.assigned_dev_ids]


def _large_card_composition_alerts(game: GameState, card: Card) -> list[AndonAlert]:
    if card.size != CardSize.G or not card.assigned_dev_ids:
        return []

    workers = _assigned_workers(game, card)
    if len(workers) == 1 and workers[0].level == Level.JUNIOR:
        return [
            AndonAlert(
                "warning",
                "large-card-junior-alone",
                f"{workers[0].name} sozinho em card G ({card.title}) nao vai progredir.",
            )
        ]

    if any(worker.level == Level.PLENO for worker in workers) and not has_complexity_mentor(
        workers
    ):
        return [
            AndonAlert(
                "warning",
                "large-card-pleno-no-mentor",
                f"Pleno em card G ({card.title}) precisa de mentor Senior/God-tier.",
            )
        ]

    return []


def refresh_alerts(game: GameState) -> GameState:
    alerts: list[AndonAlert] = []
    for card in active_cards(game):
        alerts.extend(_large_card_composition_alerts(game, card))
        if game.sprint - card.created_sprint > 3 and card.progress == 0:
            alerts.append(AndonAlert("danger", "stuck-card", f"{card.title} esta travado."))
        if card.deadline_sprint - game.sprint <= 1:
            alerts.append(AndonAlert("warning", "deadline", f"{card.title} esta perto do prazo."))
        if card.blocked_by_jidoka:
            alerts.append(AndonAlert("danger", "jidoka", f"Jidoka parou {card.title}."))
    for dev in game.developers:
        if dev.active and dev.moral < 30:
            alerts.append(AndonAlert("warning", "burnout", f"{dev.name} esta em burnout."))
        if dev.active and dev.level == Level.GOD_TIER and dev.moral < 55:
            alerts.append(AndonAlert("danger", "god-tier", f"{dev.name} ameaca sair."))
    for client in game.clients:
        if client.active and client.reputation < 40:
            alerts.append(AndonAlert("warning", "client", f"{client.name} esta critico."))
    for event in game.pending_events:
        alerts.append(AndonAlert("info", "event", event))
    if game.kaizen_points > 0:
        alerts.append(AndonAlert("success", "kaizen", "Ha ponto de Kaizen disponivel."))
    if game.budget - game.fixed_cost - payroll(game) < 0:
        alerts.append(AndonAlert("danger", "budget", "Caixa projetado negativo."))
    game.andon_alerts = sorted(
        alerts,
        key=lambda alert: (
            SEVERITY_PRIORITY.get(alert.severity, 9),
            alert.code,
            alert.message,
        ),
    )
    return game
