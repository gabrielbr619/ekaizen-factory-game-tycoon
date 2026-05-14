from __future__ import annotations

import random
from dataclasses import replace
from uuid import uuid4

from app.domain.models import (
    AndonAlert,
    Candidate,
    Card,
    CardSize,
    CardType,
    Client,
    Column,
    Developer,
    GameState,
    KaizenImpact,
    KaizenType,
    Level,
    Specialty,
    SprintMetrics,
    TimelineEvent,
    Verdict,
)


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
        Developer("d1", "Lia Backend", Specialty.BACKEND, Level.PLENO, 12, 700, 0.04, 78, "👩‍💻"),
        Developer("d2", "Theo Produto", Specialty.PO, Level.JUNIOR, 5, 300, 0.08, 42, "🧑‍💻"),
        Developer("d3", "Nina QA", Specialty.QA, Level.JUNIOR, 5, 300, 0.08, 72, "👩‍💻"),
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


def move_card(game: GameState, card_id: str, target: Column) -> GameState:
    card = find_card(game, card_id)
    if target == card.column:
        return game
    order = [Column.BACKLOG, Column.ANALYSIS, Column.DEVELOPMENT, Column.QA, Column.DONE]
    if order.index(target) != order.index(card.column) + 1:
        raise ValueError("Cards devem andar uma coluna por vez.")
    if target != Column.DONE and count_column(game, target) >= game.wip_limits[target.value]:
        raise ValueError("WIP limit da coluna foi atingido.")
    if card.blocked_by_jidoka and target == Column.DONE:
        raise ValueError("Jidoka ativo: trate o bug critico antes de concluir.")
    card.cycle_times[card.column.value] = game.sprint - card.entered_column_sprint
    card.column = target
    card.entered_column_sprint = game.sprint
    card.progress = 0 if target in {Column.ANALYSIS, Column.DEVELOPMENT, Column.QA} else card.progress
    game.timeline.append(TimelineEvent(game.sprint, "move", f"{card.title} foi movido para {target.value}."))
    return refresh_alerts(game)


def allocate_dev(game: GameState, dev_id: str, card_id: str | None) -> GameState:
    dev = find_dev(game, dev_id)
    if not dev.active:
        raise ValueError("Dev inativo nao pode ser alocado.")
    for card in game.cards:
        if dev_id in card.assigned_dev_ids:
            card.assigned_dev_ids.remove(dev_id)
    if card_id is not None:
        card = find_card(game, card_id)
        if card.column not in {Column.ANALYSIS, Column.DEVELOPMENT, Column.QA}:
            raise ValueError("So e possivel alocar em Analise, Dev ou QA.")
        if KaizenType.POKA_YOKE in game.active_kaizens and not specialty_matches(dev, card):
            raise ValueError("Poka-Yoke bloqueou alocacao fora da especialidade.")
        card.assigned_dev_ids.append(dev_id)
        game.timeline.append(TimelineEvent(game.sprint, "allocate", f"{dev.name} alocado em {card.title}."))
    return refresh_alerts(game)


def hire_candidate(game: GameState, candidate_id: str) -> GameState:
    candidate = next((item for item in game.candidates if item.id == candidate_id), None)
    if candidate is None:
        raise ValueError("Candidato nao encontrado.")
    game.budget -= candidate.salary
    game.developers.append(
        Developer(
            candidate.id.replace("cand", "dev"),
            candidate.name,
            candidate.specialty,
            candidate.level,
            candidate.speed,
            candidate.salary,
            candidate.bug_rate,
            candidate.moral,
            candidate.avatar,
            onboarding_sprints=2,
        )
    )
    game.candidates = [item for item in game.candidates if item.id != candidate_id]
    game.timeline.append(TimelineEvent(game.sprint, "hire", f"{candidate.name} entrou no time."))
    return refresh_alerts(game)


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
        column = target_id if target_id is not None else Column.DEVELOPMENT.value
        if column not in game.wip_limits:
            raise ValueError("Coluna invalida para aumento de WIP.")
        game.wip_limits[column] += 2
    elif kaizen == KaizenType.MARKETING:
        game.clients.append(Client(f"c{len(game.clients) + 1}", "Novo Cliente", 60))
    elif kaizen == KaizenType.INTERNS:
        game.developers.extend(
            [
                Developer(f"intern-{game.sprint}-{i}", f"Estagiario {i}", Specialty.FRONTEND, Level.JUNIOR, 5, 0, 0.08, 75, "🧑‍💻")
                for i in range(1, 4)
            ]
        )
    if kaizen not in game.active_kaizens:
        game.active_kaizens.append(kaizen)
    after = min(1.0, before + 0.04 * cost)
    game.timeline.append(TimelineEvent(game.sprint, "kaizen", f"Kaizen aplicado: {kaizen.value}."))
    game.metrics_history.append(
        SprintMetrics(game.sprint, 0, 0, after, average_lead_time(game), 0, 0)
    )
    return refresh_alerts(game)


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
                    game.timeline.append(TimelineEvent(game.sprint, "qa-bug", f"QA encontrou bug em {card.title}."))
                else:
                    production_bugs += 1
                    card.blocked_by_jidoka = True
                    penalize_client(game, card.client_id, 20)
            else:
                delivered += 1
                throughput_value += card.value
                finish_card(game, card, workers)
    for card in active_cards(game):
        if game.sprint > card.deadline_sprint and card.column != Column.DONE:
            penalize_client(game, card.client_id, 15)
    heijunka_bonus = calculate_heijunka_bonus(game, delivered, throughput_value)
    game.budget += throughput_value + heijunka_bonus
    game.budget -= game.fixed_cost + payroll(game)
    game.accumulated_profit += throughput_value + heijunka_bonus - game.fixed_cost - payroll(game)
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


def top_kaizens(game: GameState) -> list[KaizenImpact]:
    impacts: list[KaizenImpact] = []
    for index, kaizen in enumerate(game.active_kaizens[:3]):
        before = 0.55 + index * 0.04
        after = min(0.98, before + 0.08 + index * 0.02)
        impacts.append(KaizenImpact(kaizen, kaizen.value, before, after, after - before))
    return impacts


def find_dev(game: GameState, dev_id: str) -> Developer:
    for dev in game.developers:
        if dev.id == dev_id:
            return dev
    raise ValueError("Dev nao encontrado.")


def find_card(game: GameState, card_id: str) -> Card:
    for card in game.cards:
        if card.id == card_id:
            return card
    raise ValueError("Card nao encontrado.")


def count_column(game: GameState, column: Column) -> int:
    return sum(1 for card in game.cards if card.column == column)


def cards_in_work(game: GameState) -> list[Card]:
    return [
        card
        for card in game.cards
        if card.column in {Column.ANALYSIS, Column.DEVELOPMENT, Column.QA}
    ]


def active_cards(game: GameState) -> list[Card]:
    return [card for card in game.cards if card.column != Column.DONE]


def sprint_progress(
    game: GameState, card: Card, workers: list[Developer], rng: random.Random
) -> int:
    multiplier_by_count = {1: 1.0, 2: 1.7, 3: 2.2, 4: 2.4}
    multiplier = multiplier_by_count.get(len(workers), 2.4)
    total = 0.0
    for worker in workers:
        speed = worker.speed * moral_multiplier(worker)
        if worker.onboarding_sprints > 0:
            speed *= 0.5
            worker.onboarding_sprints -= 1
        if not specialty_matches(worker, card):
            if worker.specialty == Specialty.FULLSTACK and card.required_specialties[0] in {
                Specialty.FRONTEND,
                Specialty.BACKEND,
            }:
                speed *= 0.75
            else:
                effect = rng.choice(["slow", "bug", "refuse"])
                if effect == "slow":
                    speed *= 0.35
                elif effect == "bug":
                    card.latent_bug = True
                    speed *= 0.5
                else:
                    speed = 0
                    worker.moral = max(0, worker.moral - 12)
        total += speed
    if len(workers) >= 5 and rng.random() < 0.5:
        card.latent_bug = True
    if KaizenType.QA_AUTOMATION in game.active_kaizens and card.column == Column.QA:
        total *= 1.3
    return max(0, int(total * multiplier / max(1, len(workers))))


def update_worker_moral(game: GameState, card: Card, workers: list[Developer]) -> None:
    for worker in workers:
        drain = 2
        if not specialty_matches(worker, card):
            drain += 4
        if card.size == CardSize.G and worker.level == Level.JUNIOR and KaizenType.MENTORING not in game.active_kaizens:
            drain += 8
        if game.sprint - card.created_sprint > 3:
            drain += 4
        if len(workers) == 3:
            drain += 1
        elif len(workers) == 4:
            drain += 2
        elif len(workers) >= 5:
            drain += 3
        if KaizenType.REST_SPACE in game.active_kaizens:
            drain -= 1
        worker.moral = min(100, max(0, worker.moral - drain))
        worker.tenure_sprints += 1


def specialty_matches(dev: Developer, card: Card) -> bool:
    if dev.specialty == Specialty.FULLSTACK:
        return any(item in {Specialty.FRONTEND, Specialty.BACKEND} for item in card.required_specialties)
    return dev.specialty in card.required_specialties


def moral_multiplier(dev: Developer) -> float:
    if dev.moral >= 70:
        return 1.0
    if dev.moral >= 50:
        return 0.9
    if dev.moral >= 30:
        return 0.7
    if dev.moral >= 10:
        return 0.4
    return 0.2


def bug_happens(game: GameState, card: Card, workers: list[Developer], rng: random.Random) -> bool:
    if card.latent_bug:
        return True
    rate = sum(worker.bug_rate for worker in workers) / len(workers)
    if KaizenType.DEVOPS_CULTURE in game.active_kaizens:
        rate *= 0.5
    return rng.random() < rate


def qa_detection_chance(game: GameState, workers: list[Developer]) -> float:
    base = 0.65
    if any(worker.specialty == Specialty.QA for worker in workers):
        base += 0.2
    if KaizenType.QA_AUTOMATION in game.active_kaizens:
        base += 0.1
    return min(0.95, base)


def finish_card(game: GameState, card: Card, workers: list[Developer]) -> None:
    card.column = Column.DONE
    card.cycle_times[Column.QA.value] = game.sprint - card.entered_column_sprint
    card.assigned_dev_ids = []
    for worker in workers:
        worker.cards_delivered += 1
        worker.clean_cards_delivered += 1
    client = find_client(game, card.client_id)
    client.reputation = min(100, client.reputation + 4)
    game.timeline.append(TimelineEvent(game.sprint, "done", f"{card.title} entregue para {client.name}."))


def find_client(game: GameState, client_id: str) -> Client:
    for client in game.clients:
        if client.id == client_id:
            return client
    raise ValueError("Cliente nao encontrado.")


def penalize_client(game: GameState, client_id: str, points: int) -> None:
    client = find_client(game, client_id)
    client.reputation = max(0, client.reputation - points)
    if client.reputation < 30:
        client.active = False


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
                avatar=rng.choice(["🧑‍💻", "👨‍💻", "👩‍💻"]),
                expires_after_sprint=game.sprint + 1 if level == Level.GOD_TIER else None,
            )
        )
    return candidates


def level_profile(level: Level) -> tuple[int, int, float]:
    if level == Level.JUNIOR:
        return 5, 300, 0.08
    if level == Level.PLENO:
        return 12, 700, 0.04
    if level == Level.SENIOR:
        return 22, 1_500, 0.02
    return 40, 3_500, 0.005


def generate_events(game: GameState, rng: random.Random) -> list[str]:
    options = [
        "Cliente urgente: card de alto valor com deadline curto apareceu.",
        "Pedido de aumento: um dev quer reconhecimento financeiro.",
        "Auditoria de OEE: cliente avaliara sua eficiencia na proxima sprint.",
        "Tendencia de mercado: uma especialidade tera mais demanda.",
        "Indicacao: um candidato com salario reduzido apareceu no pool.",
    ]
    return rng.sample(options, k=rng.randint(1, 3))


def payroll(game: GameState) -> int:
    return sum(dev.salary for dev in game.developers if dev.active)


def calculate_heijunka_bonus(game: GameState, delivered: int, value: int) -> int:
    recent = [metric.delivered_cards for metric in game.metrics_history[-4:]] + [delivered]
    if KaizenType.HEIJUNKA not in game.active_kaizens or len(recent) < 5:
        return 0
    if all(item == 3 for item in recent):
        game.heijunka_streak += 1
        return int(value * 0.10)
    game.heijunka_streak = 0
    return 0


def calculate_oee(game: GameState, delivered: int, production_bugs: int) -> float:
    active_devs = [dev for dev in game.developers if dev.active]
    if not active_devs:
        return 0.0
    availability = sum(1 for dev in active_devs if dev.moral >= 30) / len(active_devs)
    performance = 1.0 if delivered == 0 else min(1.0, delivered / max(1, count_due_done(game)))
    quality = 1.0 if delivered == 0 else max(0.0, (delivered - production_bugs) / delivered)
    return round(availability * performance * quality, 3)


def current_oee(game: GameState) -> float:
    if not game.metrics_history:
        return 0.6
    return game.metrics_history[-1].oee


def count_due_done(game: GameState) -> int:
    return sum(1 for card in game.cards if card.column == Column.DONE)


def average_lead_time(game: GameState) -> float:
    done_cards = [card for card in game.cards if card.column == Column.DONE]
    if not done_cards:
        return 0.0
    total = sum(sum(card.cycle_times.values()) for card in done_cards)
    return round(total / len(done_cards), 2)


def handle_resignations(game: GameState, rng: random.Random) -> None:
    for dev in game.developers:
        if not dev.active or dev.moral > 9:
            continue
        if rng.random() < 0.3:
            dev.active = False
            game.timeline.append(TimelineEvent(game.sprint, "resignation", f"{dev.name} pediu demissao."))


def train_dev(dev: Developer) -> None:
    if dev.level == Level.JUNIOR:
        dev.level = Level.PLENO
        dev.speed, dev.salary, dev.bug_rate = level_profile(Level.PLENO)
    elif dev.level == Level.PLENO:
        dev.level = Level.SENIOR
        dev.speed, dev.salary, dev.bug_rate = level_profile(Level.SENIOR)
    dev.onboarding_sprints = 2


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


def reputation(game: GameState) -> int:
    active_clients = [client for client in game.clients if client.active]
    if not active_clients:
        return 0
    return round(sum(client.reputation for client in active_clients) / len(active_clients))


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
    for client in game.clients:
        if client.active and client.reputation < 40:
            alerts.append(AndonAlert("warning", "client", f"{client.name} esta critico."))
    if game.kaizen_points > 0:
        alerts.append(AndonAlert("success", "kaizen", "Ha ponto de Kaizen disponivel."))
    if game.budget - game.fixed_cost - payroll(game) < 0:
        alerts.append(AndonAlert("danger", "budget", "Caixa projetado negativo."))
    game.andon_alerts = alerts[:8]
    return game

