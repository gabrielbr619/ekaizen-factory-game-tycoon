from __future__ import annotations

from app.domain.models import GameState, SprintMetrics, Verdict
from app.domain.rules.metrics import reputation


def update_badges(game: GameState, metrics: SprintMetrics) -> None:
    add_badge(game, "Zero Bug Sprint", metrics.bugs_in_production == 0)
    add_badge(game, "Heijunka Pro", game.heijunka_streak >= 10)
    add_badge(game, "OEE de Ouro", metrics.oee >= 0.85)
    add_badge(game, "Cliente Fiel", all(client.active for client in game.clients))
    add_badge(game, "Sem Burnout", all(dev.moral >= 50 for dev in game.developers if dev.active))


def add_badge(game: GameState, badge: str, condition: bool) -> None:
    if condition and badge not in game.badges:
        game.badges.append(badge)


def update_verdict(game: GameState) -> None:
    if game.budget < -5_000:
        game.consecutive_negative_budget_sprints += 1
    else:
        game.consecutive_negative_budget_sprints = 0
    general_reputation = reputation(game)
    if (
        game.consecutive_negative_budget_sprints >= 3
        or len([client for client in game.clients if client.active]) == 0
        or general_reputation < 20
        or len([dev for dev in game.developers if dev.active]) == 0
    ):
        game.verdict = Verdict.BANKRUPT
        return
    if game.sprint <= 35:
        return
    active_devs = [dev for dev in game.developers if dev.active]
    if (
        game.accumulated_profit >= 20_000
        and general_reputation >= 70
        and len(active_devs) >= 5
        and all(dev.moral >= 30 for dev in active_devs)
    ):
        game.verdict = Verdict.MASTER_KAIZEN
    else:
        game.verdict = Verdict.SURVIVED
