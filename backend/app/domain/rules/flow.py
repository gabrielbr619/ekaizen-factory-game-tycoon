from __future__ import annotations

from app.domain.models import Card, Column, GameState, KaizenType, TimelineEvent
from app.domain.rules.work import find_dev, stage_required_points, worker_matches_stage


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


def move_card(game: GameState, card_id: str, target: Column) -> GameState:
    from app.domain.rules.andon import refresh_alerts

    card = find_card(game, card_id)
    if target == card.column:
        return game
    order = [Column.BACKLOG, Column.ANALYSIS, Column.DEVELOPMENT, Column.QA, Column.DONE]
    if order.index(target) != order.index(card.column) + 1:
        raise ValueError("Cards devem andar uma coluna por vez.")
    if target != Column.DONE and count_column(game, target) >= game.wip_limits[target.value]:
        raise ValueError("WIP limit da coluna foi atingido.")
    is_work_column = card.column in {Column.ANALYSIS, Column.DEVELOPMENT, Column.QA}
    if is_work_column and card.progress < stage_required_points(card):
        raise ValueError("Card so pode avancar apos concluir o trabalho da coluna atual.")
    if target == Column.DONE and card.progress < stage_required_points(card):
        raise ValueError("Card so pode ir para Done apos concluir o trabalho de QA.")
    if card.blocked_by_jidoka and target == Column.DONE:
        raise ValueError("Jidoka ativo: trate o bug critico antes de concluir.")
    if target == Column.DONE:
        raise ValueError("QA conclui cards no fim da sprint apos checagem de qualidade.")
    card.cycle_times[card.column.value] = game.sprint - card.entered_column_sprint
    card.column = target
    card.entered_column_sprint = game.sprint
    card.progress = (
        0 if target in {Column.ANALYSIS, Column.DEVELOPMENT, Column.QA} else card.progress
    )
    game.timeline.append(
        TimelineEvent(game.sprint, "move", f"{card.title} foi movido para {target.value}.")
    )
    return refresh_alerts(game)


def allocate_dev(game: GameState, dev_id: str, card_id: str | None) -> GameState:
    from app.domain.rules.andon import refresh_alerts

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
        if KaizenType.POKA_YOKE in game.active_kaizens and not worker_matches_stage(dev, card):
            raise ValueError("Poka-Yoke bloqueou alocacao fora da especialidade.")
        card.assigned_dev_ids.append(dev_id)
        game.timeline.append(
            TimelineEvent(game.sprint, "allocate", f"{dev.name} alocado em {card.title}.")
        )
    return refresh_alerts(game)
