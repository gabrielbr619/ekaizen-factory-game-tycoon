from __future__ import annotations

import random
from uuid import uuid4

from app.domain.models import (
    Candidate,
    Card,
    CardSize,
    CardType,
    Client,
    Column,
    Developer,
    GameState,
    Level,
    Specialty,
    TimelineEvent,
)
from app.domain.rules.andon import refresh_alerts
from app.domain.rules.flow import count_column
from app.domain.rules.work import level_profile, penalize_client

NAMES = [
    "Ana Martins",
    "Bruno Lima",
    "Camila Rocha",
    "Diego Santos",
    "Elisa Nunes",
    "Felipe Costa",
    "Giovana Melo",
    "Heitor Alves",
    "Isabela Prado",
    "Jonas Freire",
    "Karina Lopes",
    "Lucas Moreira",
]

CARD_TITLES = {
    CardType.FEATURE: ["Dashboard OEE", "Tela de Auditoria", "Plano de Acao", "Indicadores 5S"],
    CardType.BUG: ["Bug critico em apontamento", "Falha de validacao", "Regressao no kanban"],
    CardType.REFACTOR: ["Refactor do fluxo de QA", "Refactor de indicadores"],
    CardType.INFRA: ["Pipeline de deploy", "Migracao de banco"],
    CardType.HOTFIX: ["Hotfix de producao", "Patch de deadline urgente"],
}


def create_game(seed: int | None = None) -> GameState:
    game_seed = seed if seed is not None else random.randint(1000, 999_999)
    rng = random.Random(game_seed)
    clients = [
        Client(id="c1", name="MetalSul", reputation=rng.randint(60, 80)),
        Client(id="c2", name="AutoVale", reputation=rng.randint(60, 80)),
        Client(id="c3", name="Fabrica Orion", reputation=rng.randint(60, 80)),
    ]
    developers = [
        Developer(
            "d1", "Lia Backend", Specialty.BACKEND, Level.PLENO, 12, 700, 0.04, 78, "backend"
        ),
        Developer("d2", "Theo Produto", Specialty.PO, Level.JUNIOR, 5, 300, 0.08, 42, "po"),
        Developer("d3", "Nina QA", Specialty.QA, Level.JUNIOR, 5, 300, 0.08, 72, "qa"),
    ]
    game = GameState(
        id=str(uuid4()),
        seed=game_seed,
        sprint=1,
        phase="recovery",
        budget=8_000,
        fixed_cost=2_000,
        accumulated_profit=0,
        clients=clients,
        developers=developers,
        candidates=[],
        cards=[],
        wip_limits={
            Column.BACKLOG.value: 10,
            Column.ANALYSIS.value: 3,
            Column.DEVELOPMENT.value: 5,
            Column.QA.value: 3,
            Column.DONE.value: 999,
        },
        kaizen_points=0,
        active_kaizens=[],
        metrics_history=[],
        timeline=[TimelineEvent(1, "start", "Voce assumiu a eKaizen Software.")],
        andon_alerts=[],
        pending_events=[],
        consecutive_negative_budget_sprints=0,
        heijunka_streak=0,
        badges=[],
    )
    game.cards.extend(generate_cards(game, 5))
    game.candidates = generate_candidates(game)
    return refresh_alerts(game)


def generate_cards(game: GameState, amount: int) -> list[Card]:
    rng = random.Random(game.seed + game.sprint * 31 + len(game.cards))
    cards: list[Card] = []
    active_clients = [client for client in game.clients if client.active]
    if not active_clients:
        return cards
    for index in range(amount):
        if count_column(game, Column.BACKLOG) + len(cards) >= game.wip_limits[Column.BACKLOG.value]:
            penalize_client(game, rng.choice(active_clients).id, 10)
            continue
        size = rng.choices([CardSize.P, CardSize.M, CardSize.G], weights=[50, 35, 15], k=1)[0]
        card_type = rng.choices(
            [CardType.FEATURE, CardType.BUG, CardType.REFACTOR, CardType.INFRA, CardType.HOTFIX],
            weights=[55, 12, 12, 11, 10],
            k=1,
        )[0]
        points, value, deadline = size_profile(size)
        required = required_specialty(card_type, rng)
        client = rng.choice(active_clients)
        title = rng.choice(CARD_TITLES[card_type])
        cards.append(
            Card(
                id=f"card-{game.sprint}-{len(game.cards) + index + 1}",
                title=title,
                card_type=card_type,
                size=size,
                required_specialties=required,
                points_total=points,
                progress=0,
                value=value,
                deadline_sprint=game.sprint + deadline,
                client_id=client.id,
                column=Column.BACKLOG,
                created_sprint=game.sprint,
                entered_column_sprint=game.sprint,
            )
        )
    return cards


def size_profile(size: CardSize) -> tuple[int, int, int]:
    if size == CardSize.P:
        return 8, 2_000, 4
    if size == CardSize.M:
        return 25, 6_000, 6
    return 60, 15_000, 10


def required_specialty(card_type: CardType, rng: random.Random) -> list[Specialty]:
    if card_type == CardType.INFRA:
        return [Specialty.DEVOPS]
    if card_type == CardType.HOTFIX:
        return [rng.choice([Specialty.BACKEND, Specialty.DEVOPS])]
    if card_type == CardType.REFACTOR:
        return [rng.choice([Specialty.BACKEND, Specialty.FRONTEND])]
    if card_type == CardType.BUG:
        return [rng.choice([Specialty.BACKEND, Specialty.FRONTEND, Specialty.DEVOPS])]
    return [rng.choice([Specialty.BACKEND, Specialty.FRONTEND])]


def generate_candidates(game: GameState) -> list[Candidate]:
    rng = random.Random(game.seed + game.sprint * 11)
    total = rng.randint(4, 6)
    candidates: list[Candidate] = []
    for index in range(total):
        level = rng.choices(
            [Level.JUNIOR, Level.PLENO, Level.SENIOR, Level.GOD_TIER],
            weights=[60, 25, 13, 2],
            k=1,
        )[0]
        speed, salary, bug_rate = level_profile(level)
        candidates.append(
            Candidate(
                id=f"cand-{game.sprint}-{index}",
                name=rng.choice(NAMES),
                specialty=rng.choice(list(Specialty)),
                level=level,
                speed=speed,
                salary=salary,
                bug_rate=bug_rate,
                moral=rng.randint(68, 90),
                avatar=rng.choice(["frontend", "backend", "qa"]),
                expires_after_sprint=game.sprint + 1 if level == Level.GOD_TIER else None,
            )
        )
    return candidates
