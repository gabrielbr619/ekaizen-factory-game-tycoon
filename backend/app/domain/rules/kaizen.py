from __future__ import annotations

from app.domain.models import (
    Client,
    Developer,
    GameState,
    KaizenImpact,
    KaizenType,
    Level,
    Specialty,
    TimelineEvent,
)
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.metrics import current_oee
from app.domain.rules.work import find_dev, train_dev

NON_STACKING_KAIZENS = {
    KaizenType.POKA_YOKE,
    KaizenType.QA_AUTOMATION,
    KaizenType.MENTORING,
    KaizenType.DEVOPS_CULTURE,
    KaizenType.HEIJUNKA,
}


def apply_kaizen(game: GameState, kaizen: KaizenType, target_id: str | None = None) -> GameState:
    if kaizen in NON_STACKING_KAIZENS and kaizen in game.active_kaizens:
        raise ValueError("Kaizen permanente ja esta ativo.")
    cost = kaizen_cost(kaizen)
    if game.kaizen_points < cost:
        raise ValueError("Pontos de Kaizen insuficientes.")
    game.kaizen_points -= cost
    before = kaizen_signal(game, kaizen, target_id)
    if kaizen == KaizenType.TRAIN_DEV:
        if target_id is None:
            raise ValueError("Treinar Dev exige um alvo.")
        target_dev = find_dev(game, target_id)
        if target_dev.level == Level.GOD_TIER:
            target_dev.god_last_kaizen_sprint = game.sprint
            target_dev.moral = min(100, target_dev.moral + 8)
        else:
            train_dev(target_dev)
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
                    contract_ends_sprint=game.sprint + 5,
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
    after = kaizen_signal(game, kaizen, target_id)
    game.kaizen_impacts.append(
        KaizenImpact(kaizen, kaizen.value, before, after, round(after - before, 3))
    )
    game.timeline.append(TimelineEvent(game.sprint, "kaizen", f"Kaizen aplicado: {kaizen.value}."))
    return refresh_alerts(game)


def top_kaizens(game: GameState) -> list[KaizenImpact]:
    return sorted(game.kaizen_impacts, key=lambda item: item.delta, reverse=True)[:3]


def kaizen_signal(game: GameState, kaizen: KaizenType, target_id: str | None) -> float:
    if kaizen == KaizenType.TRAIN_DEV and target_id is not None:
        return float(find_dev(game, target_id).speed)
    if kaizen == KaizenType.WIP_INCREASE:
        column = target_id if target_id is not None else "development"
        return float(game.wip_limits.get(column, 0))
    if kaizen == KaizenType.MARKETING:
        return float(len([client for client in game.clients if client.active]))
    if kaizen == KaizenType.INTERNS:
        return float(len([dev for dev in game.developers if dev.active]))
    if kaizen == KaizenType.REST_SPACE:
        active_devs = [dev for dev in game.developers if dev.active]
        if not active_devs:
            return 0.0
        return round(sum(dev.moral for dev in active_devs) / len(active_devs), 2)
    if kaizen in game.active_kaizens:
        return 1.0
    return current_oee(game)


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
