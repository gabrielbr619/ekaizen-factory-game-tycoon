from __future__ import annotations

import random

from app.domain.models import (
    Card,
    CardSize,
    Client,
    Developer,
    GameState,
    KaizenType,
    Level,
    Specialty,
    TimelineEvent,
)


def find_dev(game: GameState, dev_id: str) -> Developer:
    for dev in game.developers:
        if dev.id == dev_id:
            return dev
    raise ValueError("Dev nao encontrado.")


def find_client(game: GameState, client_id: str) -> Client:
    for client in game.clients:
        if client.id == client_id:
            return client
    raise ValueError("Cliente nao encontrado.")


def specialty_matches(dev: Developer, card: Card) -> bool:
    if dev.specialty == Specialty.FULLSTACK:
        return any(
            item in {Specialty.FRONTEND, Specialty.BACKEND} for item in card.required_specialties
        )
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
    if KaizenType.QA_AUTOMATION in game.active_kaizens and card.column.value == "qa":
        total *= 1.3
    return max(0, int(total * multiplier / max(1, len(workers))))


def update_worker_moral(game: GameState, card: Card, workers: list[Developer]) -> None:
    for worker in workers:
        drain = 2
        if not specialty_matches(worker, card):
            drain += 4
        if (
            card.size == CardSize.G
            and worker.level == Level.JUNIOR
            and KaizenType.MENTORING not in game.active_kaizens
        ):
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


def recover_idle_morale(game: GameState) -> None:
    assigned = {dev_id for card in game.cards for dev_id in card.assigned_dev_ids}
    for dev in game.developers:
        if dev.active and dev.id not in assigned:
            dev.moral = min(100, dev.moral + 3)


def bug_happens(game: GameState, card: Card, workers: list[Developer], rng: random.Random) -> bool:
    if card.latent_bug:
        return True
    rate = sum(worker.bug_rate for worker in workers) / len(workers)
    if any(worker.moral < 30 for worker in workers):
        rate *= 1.5
    if any(worker.moral < 10 for worker in workers):
        rate *= 2.0
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
    from app.domain.models import Column

    card.column = Column.DONE
    card.cycle_times[Column.QA.value] = game.sprint - card.entered_column_sprint
    card.assigned_dev_ids = []
    for worker in workers:
        worker.cards_delivered += 1
        worker.clean_cards_delivered += 1
    client = find_client(game, card.client_id)
    client.reputation = min(100, client.reputation + 4)
    game.timeline.append(
        TimelineEvent(game.sprint, "done", f"{card.title} entregue para {client.name}.")
    )


def penalize_client(game: GameState, client_id: str, points: int) -> None:
    client = find_client(game, client_id)
    client.reputation = max(0, client.reputation - points)
    if client.reputation < 30:
        client.active = False


def payroll(game: GameState) -> int:
    return sum(dev.salary for dev in game.developers if dev.active)


def handle_resignations(game: GameState, rng: random.Random) -> None:
    for dev in game.developers:
        if not dev.active or dev.moral > 9:
            continue
        if rng.random() < 0.3:
            dev.active = False
            for client in game.clients:
                if client.active:
                    client.reputation = max(0, client.reputation - 5)
            for card in game.cards:
                if dev.id in card.assigned_dev_ids:
                    card.assigned_dev_ids.remove(dev.id)
            game.timeline.append(
                TimelineEvent(game.sprint, "resignation", f"{dev.name} pediu demissao.")
            )


def train_dev(dev: Developer) -> None:
    if dev.level == Level.JUNIOR:
        dev.level = Level.PLENO
        dev.speed, dev.salary, dev.bug_rate = level_profile(Level.PLENO)
    elif dev.level == Level.PLENO:
        dev.level = Level.SENIOR
        dev.speed, dev.salary, dev.bug_rate = level_profile(Level.SENIOR)
    dev.onboarding_sprints = 2


def level_profile(level: Level) -> tuple[int, int, float]:
    if level == Level.JUNIOR:
        return 5, 300, 0.08
    if level == Level.PLENO:
        return 12, 700, 0.04
    if level == Level.SENIOR:
        return 22, 1_500, 0.02
    return 66, 7_500, 0.005
