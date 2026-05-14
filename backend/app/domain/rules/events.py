from __future__ import annotations

import random

from app.domain.game_factory import NAMES
from app.domain.models import (
    Candidate,
    Card,
    CardSize,
    CardType,
    Column,
    GameState,
    Level,
    MarketTrend,
    Specialty,
    TimelineEvent,
)
from app.domain.rules.flow import count_column
from app.domain.rules.work import level_profile, penalize_client

EVENT_KEYS = [
    "urgent-client",
    "raise-request",
    "retro-bug",
    "headhunter",
    "conference",
    "oee-audit",
    "market-trend",
    "referral",
]

TREND_SPECIALTIES = [
    Specialty.FRONTEND,
    Specialty.BACKEND,
    Specialty.DEVOPS,
    Specialty.FULLSTACK,
]


def _points_for_size(size: CardSize) -> int:
    if size == CardSize.P:
        return 8
    if size == CardSize.M:
        return 25
    return 60


def _append_or_refuse_backlog_card(game: GameState, card: Card, rng: random.Random) -> bool:
    active_clients = [client for client in game.clients if client.active]
    if count_column(game, Column.BACKLOG) >= game.wip_limits[Column.BACKLOG.value]:
        if active_clients:
            penalize_client(game, rng.choice(active_clients).id, 10)
        return False
    game.cards.append(card)
    return True


def _apply_urgent_client(game: GameState, rng: random.Random) -> str:
    active_clients = [client for client in game.clients if client.active]
    if not active_clients:
        return "Cliente urgente: nao ha clientes ativos para gerar demanda."
    specialty = rng.choice([Specialty.BACKEND, Specialty.DEVOPS])
    client = rng.choice(active_clients)
    card = Card(
        id=f"event-urgent-{game.sprint}-{len(game.cards) + 1}",
        title="Cliente urgente: hotfix de alto valor",
        card_type=CardType.HOTFIX,
        size=CardSize.M,
        required_specialties=[specialty],
        points_total=25,
        progress=0,
        value=18_000,
        deadline_sprint=game.sprint + 2,
        client_id=client.id,
        column=Column.BACKLOG,
        created_sprint=game.sprint,
        entered_column_sprint=game.sprint,
    )
    if _append_or_refuse_backlog_card(game, card, rng):
        game.timeline.append(TimelineEvent(game.sprint, "event", card.title))
        return "Cliente urgente: hotfix de alto valor entrou no Backlog."
    return "Cliente urgente: Backlog cheio recusou demanda e reputacao caiu."


def _apply_referral(game: GameState, rng: random.Random) -> str:
    level = rng.choices(
        [Level.JUNIOR, Level.PLENO, Level.SENIOR, Level.GOD_TIER],
        weights=[45, 30, 20, 5],
        k=1,
    )[0]
    speed, salary, bug_rate = level_profile(level)
    candidate = Candidate(
        id=f"event-referral-{game.sprint}-{len(game.candidates) + 1}",
        name=rng.choice(NAMES),
        specialty=rng.choice(list(Specialty)),
        level=level,
        speed=speed,
        salary=int(salary * 0.8),
        bug_rate=bug_rate,
        moral=rng.randint(72, 92),
        avatar=rng.choice(["frontend", "backend", "qa"]),
        expires_after_sprint=game.sprint + 1,
    )
    game.candidates.append(candidate)
    game.timeline.append(
        TimelineEvent(game.sprint, "event", f"Indicacao: {candidate.name} entrou no pool.")
    )
    return "Indicacao: candidato indicado apareceu no pool com salario 20% menor."


def _apply_retro_bug(game: GameState, rng: random.Random) -> str:
    done_cards = [card for card in game.cards if card.column == Column.DONE]
    if not done_cards:
        return "Bug retroativo: auditoria nao encontrou cards entregues para reabrir."
    source = rng.choice(done_cards)
    bug = Card(
        id=f"event-retro-bug-{game.sprint}-{source.id}",
        title=f"Bug retroativo: {source.title}",
        card_type=CardType.BUG,
        size=source.size,
        required_specialties=list(source.required_specialties),
        points_total=_points_for_size(source.size),
        progress=0,
        value=0,
        deadline_sprint=game.sprint + 3,
        client_id=source.client_id,
        column=Column.BACKLOG,
        created_sprint=game.sprint,
        entered_column_sprint=game.sprint,
    )
    if _append_or_refuse_backlog_card(game, bug, rng):
        game.timeline.append(TimelineEvent(game.sprint, "event", bug.title))
        return "Bug retroativo: card entregue voltou ao Backlog como bug critico."
    return "Bug retroativo: Backlog cheio recusou bug critico e reputacao caiu."


def _apply_raise_request(game: GameState, rng: random.Random) -> str:
    active_devs = [dev for dev in game.developers if dev.active]
    if not active_devs:
        return "Pedido de aumento: nao ha dev ativo para fazer pedido."
    dev = rng.choice(active_devs)
    dev.raise_requested_salary = int(dev.salary * 1.2)
    dev.raise_request_deadline_sprint = game.sprint + 2
    game.timeline.append(
        TimelineEvent(
            game.sprint,
            "event",
            f"Pedido de aumento: {dev.name} quer salario de R$ {dev.raise_requested_salary}.",
        )
    )
    return f"Pedido de aumento: {dev.name} exige +20% salario ou sai em 2 sprints."


def _apply_headhunter(game: GameState, rng: random.Random) -> str:
    targets = [
        dev
        for dev in game.developers
        if dev.active and dev.level in {Level.SENIOR, Level.GOD_TIER}
    ]
    if not targets:
        return "Headhunter: nenhum Senior/God-tier ativo foi abordado."
    dev = rng.choice(targets)
    dev.headhunter_salary = int(dev.salary * 1.5)
    dev.headhunter_deadline_sprint = game.sprint + 2
    game.timeline.append(
        TimelineEvent(
            game.sprint,
            "event",
            f"Headhunter: {dev.name} recebeu oferta externa.",
        )
    )
    return f"Headhunter: {dev.name} precisa receber R$ {dev.headhunter_salary} ou sai em 2 sprints."


def _apply_conference(game: GameState, rng: random.Random) -> str:
    active_devs = [dev for dev in game.developers if dev.active]
    if not active_devs:
        return "Conferencia: nao ha dev ativo para participar."
    dev = rng.choice(active_devs)
    dev.moral = min(100, dev.moral + 20)
    dev.conference_return_sprint = game.sprint
    game.timeline.append(
        TimelineEvent(
            game.sprint,
            "event",
            f"Conferencia: {dev.name} ganhou moral, mas ficara 1 sprint improdutivo.",
        )
    )
    return f"Conferencia: {dev.name} ganhou +20 moral e perde 1 sprint produtivo."


def _apply_oee_audit(game: GameState) -> str:
    game.pending_oee_audit_sprint = game.sprint
    game.timeline.append(
        TimelineEvent(game.sprint, "event", "Auditoria de OEE marcada para esta sprint.")
    )
    return "Auditoria de OEE: cliente avaliara sua eficiencia na proxima sprint."


def _apply_market_trend(game: GameState, rng: random.Random) -> str:
    if game.market_trends:
        return "Tendencia de mercado: sinal mantido, sem nova demanda extra."
    specialty = rng.choice(TREND_SPECIALTIES)
    game.market_trends.append(MarketTrend(specialty, game.sprint + 5))
    game.timeline.append(
        TimelineEvent(
            game.sprint,
            "event",
            f"Tendencia de mercado: demanda por {specialty.value} aumentou.",
        )
    )
    return f"Tendencia de mercado: demanda por {specialty.value} dobrou por 5 sprints."


def apply_event(game: GameState, event_key: str, rng: random.Random) -> str:
    if event_key == "urgent-client":
        return _apply_urgent_client(game, rng)
    if event_key == "referral":
        return _apply_referral(game, rng)
    if event_key == "retro-bug":
        return _apply_retro_bug(game, rng)
    if event_key == "raise-request":
        return _apply_raise_request(game, rng)
    if event_key == "headhunter":
        return _apply_headhunter(game, rng)
    if event_key == "conference":
        return _apply_conference(game, rng)
    if event_key == "oee-audit":
        return _apply_oee_audit(game)
    if event_key == "market-trend":
        return _apply_market_trend(game, rng)
    return "Evento desconhecido: nenhuma alteracao aplicada."


def generate_events(game: GameState, rng: random.Random) -> list[str]:
    weighted_events: list[tuple[str, int]] = [
        ("referral", 8),
        ("market-trend", 1),
    ]
    if game.sprint >= 5:
        weighted_events.append(("conference", 5))
    if game.sprint >= 12:
        weighted_events.extend([("urgent-client", 1), ("raise-request", 1)])
    if game.sprint >= 18 and any(
        dev.active and dev.level in {Level.SENIOR, Level.GOD_TIER}
        for dev in game.developers
    ):
        weighted_events.append(("headhunter", 1))
    if game.sprint >= 15 and game.pending_oee_audit_sprint is None:
        weighted_events.append(("oee-audit", 1))
    if game.sprint >= 15 and any(card.column == Column.DONE for card in game.cards):
        weighted_events.append(("retro-bug", 1))

    event_count = rng.randint(1, 3)

    selected_events: list[str] = []
    pool = weighted_events.copy()
    for _ in range(min(event_count, len(pool))):
        total_weight = sum(weight for _, weight in pool)
        pick = rng.randint(1, total_weight)
        cursor = 0
        for index, (event_key, weight) in enumerate(pool):
            cursor += weight
            if pick <= cursor:
                selected_events.append(event_key)
                pool.pop(index)
                break
    return [apply_event(game, event_key, rng) for event_key in selected_events]
