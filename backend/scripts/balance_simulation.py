from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from statistics import mean

from app.domain.commands import hire_candidate
from app.domain.engine import allocate_dev, apply_kaizen, create_game, move_card, process_sprint
from app.domain.models import (
    Card,
    Column,
    Developer,
    GameState,
    KaizenType,
    Level,
    Specialty,
    Verdict,
)
from app.domain.rules.flow import count_column
from app.domain.rules.metrics import reputation
from app.domain.rules.work import stage_required_points, worker_matches_stage

DEV_SPECIALTIES = {
    Specialty.FRONTEND,
    Specialty.BACKEND,
    Specialty.DEVOPS,
    Specialty.FULLSTACK,
}
LEVEL_RANK = {
    Level.JUNIOR: 1,
    Level.PLENO: 2,
    Level.SENIOR: 3,
    Level.GOD_TIER: 4,
}


def active_devs(game: GameState) -> list[Developer]:
    return [dev for dev in game.developers if dev.active]


def card_sort_key(game: GameState, card: Card) -> tuple[float, int, int, int]:
    remaining_deadline = card.deadline_sprint - game.sprint
    remaining_points = max(1, stage_required_points(card) - card.progress)
    value = 18_000 if "Cliente urgente" in card.title else card.value
    bug_priority = 8_000 if card.value == 0 else 0
    lateness_penalty = 6_000 if remaining_deadline < 0 else 0
    urgency = 4_000 / max(1, remaining_deadline + 2)
    score = (value + bug_priority + lateness_penalty + urgency) / remaining_points
    return (-score, remaining_deadline, -value, remaining_points)


def has_viable_dev(game: GameState, card: Card) -> bool:
    workers = active_devs(game)
    if card.column == Column.ANALYSIS:
        return any(dev.specialty in {Specialty.PO, Specialty.FULLSTACK} for dev in workers)
    if card.column == Column.QA:
        return any(dev.specialty == Specialty.QA for dev in workers)
    if card.size == "G":
        return any(
            worker_matches_stage(dev, card) and dev.level in {Level.SENIOR, Level.GOD_TIER}
            for dev in workers
        )
    return any(worker_matches_stage(dev, card) for dev in workers)


def maybe_move_ready_cards(game: GameState) -> None:
    for target in [Column.QA, Column.DEVELOPMENT]:
        source = Column.DEVELOPMENT if target == Column.QA else Column.ANALYSIS
        ready = sorted(
            [
                card
                for card in game.cards
                if card.column == source and card.progress >= stage_required_points(card)
            ],
            key=lambda card: card_sort_key(game, card),
        )
        for card in ready:
            if count_column(game, target) >= game.wip_limits[target.value]:
                break
            try:
                move_card(game, card.id, target)
            except ValueError:
                continue


def pull_backlog(game: GameState) -> None:
    analysis_room = game.wip_limits[Column.ANALYSIS.value] - count_column(game, Column.ANALYSIS)
    if analysis_room <= 0:
        return
    in_work = sum(1 for card in game.cards if card.column in {Column.ANALYSIS, Column.DEVELOPMENT})
    active_capacity = max(3, len(active_devs(game)))
    target_pull = max(0, min(analysis_room, active_capacity - in_work))
    candidates = sorted(
        [
            card
            for card in game.cards
            if card.column == Column.BACKLOG
            and has_viable_dev(game, card)
            and card.deadline_sprint - game.sprint >= 0
        ],
        key=lambda card: card_sort_key(game, card),
    )
    for card in candidates[:target_pull]:
        try:
            move_card(game, card.id, Column.ANALYSIS)
        except ValueError:
            continue


def choose_workers(game: GameState, card: Card, available: set[str]) -> list[Developer]:
    candidates = [
        dev
        for dev in active_devs(game)
        if dev.id in available and worker_matches_stage(dev, card)
    ]
    candidates.sort(
        key=lambda dev: (
            dev.level != Level.GOD_TIER,
            -LEVEL_RANK[dev.level],
            -dev.speed,
            -dev.moral,
            dev.salary,
        )
    )
    if card.column in {Column.ANALYSIS, Column.QA}:
        return candidates[:1]
    if card.size == "G":
        seniorish = [dev for dev in candidates if dev.level in {Level.SENIOR, Level.GOD_TIER}]
        if not seniorish:
            return []
        selected = seniorish[:1]
        for dev in candidates:
            if dev.id not in {item.id for item in selected}:
                selected.append(dev)
            if len(selected) >= 3:
                break
        return selected
    return candidates[: min(2, len(candidates))]


def allocate_work(game: GameState) -> None:
    available = {dev.id for dev in active_devs(game)}
    ordered_cards = sorted(
        [
            card
            for card in game.cards
            if card.column in {Column.QA, Column.DEVELOPMENT, Column.ANALYSIS}
        ],
        key=lambda card: (
            0 if card.column == Column.QA else 1 if card.column == Column.DEVELOPMENT else 2,
            card_sort_key(game, card),
        ),
    )
    for card in ordered_cards:
        workers = choose_workers(game, card, available)
        if not workers:
            continue
        for worker in workers:
            try:
                allocate_dev(game, worker.id, card.id)
            except ValueError:
                continue
            available.discard(worker.id)


def needed_specialties(game: GameState) -> set[Specialty]:
    active_specialties = {dev.specialty for dev in active_devs(game)}
    missing = (
        {Specialty.FRONTEND, Specialty.DEVOPS, Specialty.QA, Specialty.PO}
        - active_specialties
    )
    backlog_needs = {
        specialty
        for card in game.cards
        if card.column != Column.DONE
        for specialty in card.required_specialties
        if specialty in DEV_SPECIALTIES
    }
    return missing | (backlog_needs - active_specialties)


def maybe_hire(game: GameState) -> None:
    desired = needed_specialties(game)
    current = active_devs(game)
    max_team = 9 if game.sprint >= 20 or game.budget > 18_000 else 7
    if len(current) >= max_team:
        return
    affordable_floor = -4_000
    candidates = sorted(
        game.candidates,
        key=lambda candidate: (
            candidate.specialty not in desired,
            candidate.level in {Level.SENIOR, Level.GOD_TIER},
            candidate.level == Level.JUNIOR,
            -LEVEL_RANK[candidate.level],
            candidate.salary,
        ),
    )
    for candidate in candidates:
        if len(active_devs(game)) >= max_team:
            return
        if candidate.level == Level.GOD_TIER and game.budget < 45_000:
            continue
        if candidate.level == Level.SENIOR and game.budget < 28_000:
            continue
        if candidate.specialty not in desired and len(active_devs(game)) >= 5:
            continue
        if game.budget - candidate.salary < affordable_floor:
            continue
        try:
            hire_candidate(game, candidate.id)
        except ValueError:
            continue
        desired = needed_specialties(game)


def maybe_apply_kaizens(game: GameState) -> None:
    while game.kaizen_points > 0:
        low_moral = [dev for dev in active_devs(game) if dev.moral < 38]
        reputation_risk = reputation(game) < 60 or sum(1 for client in game.clients if client.active) < 3
        if (
            reputation_risk
            and KaizenType.MARKETING not in game.active_kaizens
            and game.kaizen_points < 2
            and not any(dev.moral < 20 for dev in active_devs(game))
        ):
            break
        god = next((dev for dev in active_devs(game) if dev.level == Level.GOD_TIER), None)
        raise_due = sorted(
            [
                dev
                for dev in active_devs(game)
                if dev.raise_request_deadline_sprint is not None
                and dev.raise_request_deadline_sprint - game.sprint <= 1
                and dev.level in {Level.JUNIOR, Level.PLENO}
            ],
            key=lambda dev: dev.raise_request_deadline_sprint or 99,
        )
        trainable = sorted(
            [
                dev
                for dev in active_devs(game)
                if dev.level in {Level.JUNIOR, Level.PLENO}
                and dev.specialty in needed_specialties(game) | {Specialty.PO, Specialty.QA}
            ],
            key=lambda dev: (LEVEL_RANK[dev.level], dev.moral),
        )
        choices: list[tuple[KaizenType, str | None]] = []
        if (
            game.kaizen_points >= 2
            and KaizenType.MARKETING not in game.active_kaizens
            and reputation_risk
        ):
            choices.append((KaizenType.MARKETING, None))
        if low_moral and KaizenType.REST_SPACE not in game.active_kaizens:
            choices.append((KaizenType.REST_SPACE, None))
        if raise_due:
            choices.append((KaizenType.TRAIN_DEV, raise_due[0].id))
        if god and game.sprint + 1 - god.god_last_kaizen_sprint >= 7:
            choices.append((KaizenType.TRAIN_DEV, god.id))
        if trainable and game.sprint <= 25:
            choices.append((KaizenType.TRAIN_DEV, trainable[0].id))
        if game.kaizen_points >= 2 and KaizenType.QA_AUTOMATION not in game.active_kaizens:
            choices.append((KaizenType.QA_AUTOMATION, None))
        if game.kaizen_points >= 2 and KaizenType.DEVOPS_CULTURE not in game.active_kaizens:
            choices.append((KaizenType.DEVOPS_CULTURE, None))
        if KaizenType.WIP_INCREASE not in game.active_kaizens and game.sprint >= 11:
            choices.append((KaizenType.WIP_INCREASE, Column.QA.value))
        if not choices:
            break
        applied = False
        for kaizen, target in choices:
            try:
                apply_kaizen(game, kaizen, target)
            except ValueError:
                continue
            applied = True
            break
        if not applied:
            break


def play_seed(seed: int) -> GameState:
    game = create_game(seed)
    while game.verdict == Verdict.PLAYING:
        maybe_apply_kaizens(game)
        maybe_hire(game)
        maybe_move_ready_cards(game)
        pull_backlog(game)
        maybe_move_ready_cards(game)
        allocate_work(game)
        process_sprint(game)
        if game.sprint > 36:
            break
    return game


def summarize_game(seed: int, game: GameState) -> dict[str, object]:
    active = active_devs(game)
    delivered = [card for card in game.cards if card.column == Column.DONE]
    kaizens = Counter(impact.kaizen.value for impact in game.kaizen_impacts)
    return {
        "seed": seed,
        "verdict": game.verdict.value,
        "sprint": game.sprint,
        "budget": game.budget,
        "accumulated_profit": game.accumulated_profit,
        "reputation": reputation(game),
        "active_clients": sum(1 for client in game.clients if client.active),
        "active_devs": len(active),
        "min_moral": min((dev.moral for dev in active), default=0),
        "delivered_cards": len(delivered),
        "throughput": sum(card.value for card in delivered),
        "kaizen_points_left": game.kaizen_points,
        "kaizens": dict(kaizens),
        "avg_oee": round(mean([metric.oee for metric in game.metrics_history]), 3)
        if game.metrics_history
        else 0,
        "last_metrics": asdict(game.metrics_history[-1]) if game.metrics_history else None,
        "events": dict(Counter(event.kind for event in game.timeline)),
    }


def score(summary: dict[str, object]) -> tuple[int, int, int, int]:
    verdict_score = {"master-kaizen": 3, "survived": 2, "bankrupt": 1, "playing": 0}
    return (
        verdict_score[str(summary["verdict"])],
        int(summary["budget"]),
        int(summary["reputation"]),
        int(summary["delivered_cards"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summaries = []
    for seed in range(args.start, args.start + args.seeds):
        summaries.append(summarize_game(seed, play_seed(seed)))
    verdicts = Counter(str(item["verdict"]) for item in summaries)
    best = max(summaries, key=score)
    aggregate = {
        "seeds": args.seeds,
        "start": args.start,
        "verdicts": dict(verdicts),
        "best": best,
        "averages": {
            key: round(mean(int(item[key]) for item in summaries), 2)
            for key in [
                "budget",
                "accumulated_profit",
                "reputation",
                "active_clients",
                "active_devs",
                "min_moral",
                "delivered_cards",
                "throughput",
            ]
        },
        "kaizen_usage": dict(
            sum((Counter(item["kaizens"]) for item in summaries), Counter())
        ),
    }
    if args.json:
        print(json.dumps(aggregate, indent=2, sort_keys=True))
        return
    print(f"seeds {args.seeds} start {args.start}")
    print(f"verdicts {dict(verdicts)}")
    print(f"best {json.dumps(best, indent=2, sort_keys=True)}")
    print(f"averages {json.dumps(aggregate['averages'], sort_keys=True)}")
    print(f"kaizen_usage {dict(aggregate['kaizen_usage'])}")


if __name__ == "__main__":
    main()
