from __future__ import annotations

from app.domain.models import (
    Client,
    Developer,
    GameState,
    KaizenImpact,
    KaizenType,
    Level,
    Specialty,
    SprintMetrics,
    TimelineEvent,
)
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.metrics import average_lead_time, current_oee
from app.domain.rules.work import find_dev, train_dev


def apply_kaizen(game: GameState, kaizen: KaizenType, target_id: str | None = None) -> GameState:
    cost = kaizen_cost(kaizen)
    if game.kaizen_points < cost:
        raise ValueError("Pontos de Kaizen insuficientes.")
    game.kaizen_points -= cost
    before = current_oee(game)
    if kaizen == KaizenType.TRAIN_DEV:
        if target_id is None:
            raise ValueError("Treinar Dev exige um alvo.")
        train_dev(find_dev(game, target_id))
    elif kaizen == KaizenType.WIP_INCREASE:
        column = target_id if target_id is not None else "development"
        if column not in game.wip_limits:
            raise ValueError("Coluna invalida para aumento de WIP.")
        game.wip_limits[column] += 2
    elif kaizen == KaizenType.MARKETING:
        game.clients.append(Client(f"c{len(game.clients) + 1}", "Novo Cliente", 60))
    elif kaizen == KaizenType.INTERNS:
        game.developers.extend(
            [
                Developer(
                    f"intern-{game.sprint}-{index}",
                    f"Estagiario {index}",
                    Specialty.FRONTEND,
                    Level.JUNIOR,
                    5,
                    0,
                    0.08,
                    75,
                    "intern",
                )
                for index in range(1, 4)
            ]
        )
    elif kaizen == KaizenType.REST_SPACE:
        for dev in game.developers:
            if dev.active:
                dev.moral = min(100, dev.moral + 5)
    if kaizen not in game.active_kaizens:
        game.active_kaizens.append(kaizen)
    after = min(1.0, before + 0.04 * cost)
    game.timeline.append(TimelineEvent(game.sprint, "kaizen", f"Kaizen aplicado: {kaizen.value}."))
    game.metrics_history.append(
        SprintMetrics(game.sprint, 0, 0, after, average_lead_time(game), 0, 0)
    )
    return refresh_alerts(game)


def top_kaizens(game: GameState) -> list[KaizenImpact]:
    impacts: list[KaizenImpact] = []
    for index, kaizen in enumerate(game.active_kaizens[:3]):
        before = 0.55 + index * 0.04
        after = min(0.98, before + 0.08 + index * 0.02)
        impacts.append(KaizenImpact(kaizen, kaizen.value, before, after, after - before))
    return impacts


def kaizen_cost(kaizen: KaizenType) -> int:
    if kaizen in {
        KaizenType.QA_AUTOMATION,
        KaizenType.MENTORING,
        KaizenType.MARKETING,
        KaizenType.DEVOPS_CULTURE,
        KaizenType.HEIJUNKA,
    }:
        return 2
    return 1
