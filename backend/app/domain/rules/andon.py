from __future__ import annotations

from app.domain.models import AndonAlert, GameState, Level
from app.domain.rules.flow import active_cards
from app.domain.rules.work import payroll


def refresh_alerts(game: GameState) -> GameState:
    alerts: list[AndonAlert] = []
    for card in active_cards(game):
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
    game.andon_alerts = alerts[:8]
    return game
