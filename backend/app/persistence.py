from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from app.api.serialization import encode_game
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
    MarketTrend,
    ScheduledProductionBug,
    Specialty,
    SprintMetrics,
    TimelineEvent,
    Verdict,
)


def _expect_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Estado persistido invalido.")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Estado persistido invalido.")
        result[key] = item
    return result


def _expect_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Estado persistido invalido.")
    return list(value)


def _get_required(data: dict[str, object], key: str) -> object:
    try:
        return data[key]
    except KeyError as exc:
        raise ValueError("Estado persistido invalido.") from exc


def _get_optional(data: dict[str, object], key: str) -> object:
    return data.get(key)


def _get_str(data: dict[str, object], key: str) -> str:
    value = _get_required(data, key)
    if not isinstance(value, str):
        raise ValueError("Estado persistido invalido.")
    return value


def _get_optional_str(data: dict[str, object], key: str) -> str | None:
    value = _get_optional(data, key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Estado persistido invalido.")
    return value


def _get_int(data: dict[str, object], key: str) -> int:
    value = _get_required(data, key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("Estado persistido invalido.")
    return value


def _get_optional_int(data: dict[str, object], key: str) -> int | None:
    value = _get_optional(data, key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("Estado persistido invalido.")
    return value


def _get_float(data: dict[str, object], key: str) -> float:
    value = _get_required(data, key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("Estado persistido invalido.")
    return float(value)


def _get_bool(data: dict[str, object], key: str, default: bool) -> bool:
    value = _get_optional(data, key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError("Estado persistido invalido.")
    return value


def _get_str_int_dict(data: dict[str, object], key: str) -> dict[str, int]:
    value = _get_required(data, key)
    raw = _expect_dict(value)
    result: dict[str, int] = {}
    for item_key, item_value in raw.items():
        if not isinstance(item_value, int) or isinstance(item_value, bool):
            raise ValueError("Estado persistido invalido.")
        result[item_key] = item_value
    return result


def _get_str_float_dict(data: dict[str, object], key: str) -> dict[str, float]:
    value = _get_optional(data, key)
    if value is None:
        return {}
    raw = _expect_dict(value)
    result: dict[str, float] = {}
    for item_key, item_value in raw.items():
        if isinstance(item_value, bool) or not isinstance(item_value, int | float):
            raise ValueError("Estado persistido invalido.")
        result[item_key] = float(item_value)
    return result


def _get_list(data: dict[str, object], key: str) -> list[object]:
    return _expect_list(_get_required(data, key))


def _get_optional_list(data: dict[str, object], key: str) -> list[object]:
    value = _get_optional(data, key)
    if value is None:
        return []
    return _expect_list(value)


def _decode_client(value: object) -> Client:
    data = _expect_dict(value)
    return Client(
        id=_get_str(data, "id"),
        name=_get_str(data, "name"),
        reputation=_get_int(data, "reputation"),
        active=_get_bool(data, "active", True),
        cancellation_sprint=_get_optional_int(data, "cancellation_sprint"),
    )


def _decode_developer(value: object) -> Developer:
    data = _expect_dict(value)
    return Developer(
        id=_get_str(data, "id"),
        name=_get_str(data, "name"),
        specialty=Specialty(_get_str(data, "specialty")),
        level=Level(_get_str(data, "level")),
        speed=_get_int(data, "speed"),
        salary=_get_int(data, "salary"),
        bug_rate=_get_float(data, "bug_rate"),
        moral=_get_int(data, "moral"),
        avatar=_get_str(data, "avatar"),
        active=_get_bool(data, "active", True),
        cards_delivered=_get_int(data, "cards_delivered"),
        bugs_generated=_get_int(data, "bugs_generated"),
        tenure_sprints=_get_int(data, "tenure_sprints"),
        onboarding_sprints=_get_int(data, "onboarding_sprints"),
        clean_cards_delivered=_get_int(data, "clean_cards_delivered"),
        god_low_work_streak=_get_int(data, "god_low_work_streak"),
        god_last_kaizen_sprint=_get_int(data, "god_last_kaizen_sprint"),
        raise_request_deadline_sprint=_get_optional_int(data, "raise_request_deadline_sprint"),
        raise_requested_salary=_get_optional_int(data, "raise_requested_salary"),
        headhunter_deadline_sprint=_get_optional_int(data, "headhunter_deadline_sprint"),
        headhunter_salary=_get_optional_int(data, "headhunter_salary"),
        conference_return_sprint=_get_optional_int(data, "conference_return_sprint"),
        contract_ends_sprint=_get_optional_int(data, "contract_ends_sprint"),
    )


def _decode_card(value: object) -> Card:
    data = _expect_dict(value)
    return Card(
        id=_get_str(data, "id"),
        title=_get_str(data, "title"),
        card_type=CardType(_get_str(data, "card_type")),
        size=CardSize(_get_str(data, "size")),
        required_specialties=_decode_specialty_list(_get_required(data, "required_specialties")),
        points_total=_get_int(data, "points_total"),
        progress=_get_int(data, "progress"),
        value=_get_int(data, "value"),
        deadline_sprint=_get_int(data, "deadline_sprint"),
        client_id=_get_str(data, "client_id"),
        column=Column(_get_str(data, "column")),
        created_sprint=_get_int(data, "created_sprint"),
        entered_column_sprint=_get_int(data, "entered_column_sprint"),
        assigned_dev_ids=_decode_str_list(_get_optional(data, "assigned_dev_ids") or []),
        latent_bug=_get_bool(data, "latent_bug", False),
        blocked_by_jidoka=_get_bool(data, "blocked_by_jidoka", False),
        cycle_times=_get_str_int_dict(data, "cycle_times"),
    )


def _decode_scheduled_production_bug(value: object) -> ScheduledProductionBug:
    data = _expect_dict(value)
    return ScheduledProductionBug(
        source_card_id=_get_str(data, "source_card_id"),
        source_title=_get_str(data, "source_title"),
        client_id=_get_str(data, "client_id"),
        size=CardSize(_get_str(data, "size")),
        required_specialties=_decode_specialty_list(_get_required(data, "required_specialties")),
        due_sprint=_get_int(data, "due_sprint"),
    )


def _decode_candidate(value: object) -> Candidate:
    data = _expect_dict(value)
    return Candidate(
        id=_get_str(data, "id"),
        name=_get_str(data, "name"),
        specialty=Specialty(_get_str(data, "specialty")),
        level=Level(_get_str(data, "level")),
        speed=_get_int(data, "speed"),
        salary=_get_int(data, "salary"),
        bug_rate=_get_float(data, "bug_rate"),
        moral=_get_int(data, "moral"),
        avatar=_get_str(data, "avatar"),
        expires_after_sprint=_get_optional_int(data, "expires_after_sprint"),
    )


def _decode_sprint_metrics(value: object) -> SprintMetrics:
    data = _expect_dict(value)
    return SprintMetrics(
        sprint=_get_int(data, "sprint"),
        delivered_cards=_get_int(data, "delivered_cards"),
        throughput_value=_get_int(data, "throughput_value"),
        oee=_get_float(data, "oee"),
        lead_time_avg=_get_float(data, "lead_time_avg"),
        bugs_in_production=_get_int(data, "bugs_in_production"),
        heijunka_bonus=_get_int(data, "heijunka_bonus"),
        cycle_time_by_column=_get_str_float_dict(data, "cycle_time_by_column"),
    )


def _decode_timeline_event(value: object) -> TimelineEvent:
    data = _expect_dict(value)
    return TimelineEvent(
        sprint=_get_int(data, "sprint"),
        kind=_get_str(data, "kind"),
        message=_get_str(data, "message"),
    )


def _decode_market_trend(value: object) -> MarketTrend:
    data = _expect_dict(value)
    return MarketTrend(
        specialty=Specialty(_get_str(data, "specialty")),
        expires_after_sprint=_get_int(data, "expires_after_sprint"),
    )


def _decode_andon_alert(value: object) -> AndonAlert:
    data = _expect_dict(value)
    return AndonAlert(
        severity=_get_str(data, "severity"),
        code=_get_str(data, "code"),
        message=_get_str(data, "message"),
    )


def _decode_kaizen_impact(value: object) -> KaizenImpact:
    data = _expect_dict(value)
    return KaizenImpact(
        kaizen=KaizenType(_get_str(data, "kaizen")),
        label=_get_str(data, "label"),
        before=_get_float(data, "before"),
        after=_get_float(data, "after"),
        delta=_get_float(data, "delta"),
    )


def _decode_str_list(value: object) -> list[str]:
    result: list[str] = []
    for item in _expect_list(value):
        if not isinstance(item, str):
            raise ValueError("Estado persistido invalido.")
        result.append(item)
    return result


def _decode_specialty_list(value: object) -> list[Specialty]:
    return [Specialty(item) for item in _decode_str_list(value)]


def _decode_kaizen_list(value: object) -> list[KaizenType]:
    return [KaizenType(item) for item in _decode_str_list(value)]


def _decode_game_state_json(payload: str) -> GameState | None:
    try:
        raw: object = json.loads(payload)
        data = _expect_dict(raw)
        return GameState(
            id=_get_str(data, "id"),
            seed=_get_int(data, "seed"),
            sprint=_get_int(data, "sprint"),
            phase=_get_str(data, "phase"),
            budget=_get_int(data, "budget"),
            fixed_cost=_get_int(data, "fixed_cost"),
            accumulated_profit=_get_int(data, "accumulated_profit"),
            clients=[_decode_client(item) for item in _get_list(data, "clients")],
            developers=[_decode_developer(item) for item in _get_list(data, "developers")],
            candidates=[_decode_candidate(item) for item in _get_list(data, "candidates")],
            cards=[_decode_card(item) for item in _get_list(data, "cards")],
            wip_limits=_get_str_int_dict(data, "wip_limits"),
            kaizen_points=_get_int(data, "kaizen_points"),
            active_kaizens=_decode_kaizen_list(_get_required(data, "active_kaizens")),
            metrics_history=[
                _decode_sprint_metrics(item) for item in _get_list(data, "metrics_history")
            ],
            timeline=[_decode_timeline_event(item) for item in _get_list(data, "timeline")],
            andon_alerts=[_decode_andon_alert(item) for item in _get_list(data, "andon_alerts")],
            pending_events=_decode_str_list(_get_required(data, "pending_events")),
            consecutive_negative_budget_sprints=_get_int(
                data, "consecutive_negative_budget_sprints"
            ),
            heijunka_streak=_get_int(data, "heijunka_streak"),
            badges=_decode_str_list(_get_required(data, "badges")),
            scheduled_production_bugs=[
                _decode_scheduled_production_bug(item)
                for item in _get_optional_list(data, "scheduled_production_bugs")
            ],
            kaizen_impacts=[
                _decode_kaizen_impact(item) for item in _get_optional_list(data, "kaizen_impacts")
            ],
            market_trends=[
                _decode_market_trend(item) for item in _get_optional_list(data, "market_trends")
            ],
            pending_oee_audit_sprint=_get_optional_int(data, "pending_oee_audit_sprint"),
            knowledge_loss_until_sprint=_get_optional_int(data, "knowledge_loss_until_sprint"),
            verdict=Verdict(_get_str(data, "verdict")),
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _encode_game_state(game: GameState) -> str:
    return json.dumps(encode_game(game), ensure_ascii=True, separators=(",", ":"), sort_keys=True)


class GameRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _decode_game_state(self, state_payload: object) -> GameState | None:
        if isinstance(state_payload, str):
            return _decode_game_state_json(state_payload)
        return None

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS games (id TEXT PRIMARY KEY, state TEXT NOT NULL)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    game_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    command_hash TEXT,
                    state TEXT NOT NULL,
                    PRIMARY KEY (game_id, command_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS game_creations (
                    idempotency_key TEXT PRIMARY KEY,
                    request_hash TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    state TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row[1])
                for row in conn.execute("PRAGMA table_info(commands)").fetchall()
            }
            if "command_hash" not in columns:
                conn.execute("ALTER TABLE commands ADD COLUMN command_hash TEXT")

    def ping(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("SELECT 1").fetchone()

    def save(self, game: GameState) -> None:
        payload = _encode_game_state(game)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT OR REPLACE INTO games (id, state) VALUES (?, ?)",
                (game.id, payload),
            )

    def get(self, game_id: str) -> GameState | None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT state FROM games WHERE id = ?", (game_id,)).fetchone()
        if row is None:
            return None
        return self._decode_game_state(row[0])

    def get_created_game(self, idempotency_key: str, request_hash: str) -> GameState | None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                """
                SELECT state, request_hash
                FROM game_creations
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()
        if row is None:
            return None
        existing_hash = row[1]
        if isinstance(existing_hash, str) and existing_hash != request_hash:
            raise ValueError("Idempotency-Key reutilizado com payload diferente.")
        return self._decode_game_state(row[0])

    def save_created_game(
        self, idempotency_key: str, request_hash: str, game: GameState
    ) -> GameState:
        payload = _encode_game_state(game)
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    INSERT INTO game_creations (idempotency_key, request_hash, game_id, state)
                    VALUES (?, ?, ?, ?)
                    """,
                    (idempotency_key, request_hash, game.id, payload),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO games (id, state) VALUES (?, ?)",
                    (game.id, payload),
                )
            except sqlite3.IntegrityError:
                row = conn.execute(
                    """
                    SELECT state, request_hash
                    FROM game_creations
                    WHERE idempotency_key = ?
                    """,
                    (idempotency_key,),
                ).fetchone()
                conn.rollback()
                if row is None:
                    raise
                existing_hash = row[1]
                if isinstance(existing_hash, str) and existing_hash != request_hash:
                    raise ValueError(
                        "Idempotency-Key reutilizado com payload diferente."
                    ) from None
                existing = self._decode_game_state(row[0])
                if existing is None:
                    raise ValueError("Estado idempotente invalido.") from None
                return existing
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
                return game

    def get_idempotent(
        self,
        game_id: str,
        command_id: str,
        command_hash: str,
    ) -> GameState | None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT state, command_hash FROM commands WHERE game_id = ? AND command_id = ?",
                (game_id, command_id),
            ).fetchone()
        if row is None:
            return None
        existing_hash = row[1]
        if isinstance(existing_hash, str) and existing_hash != command_hash:
            raise ValueError("Idempotency-Key reutilizado com payload diferente.")
        return self._decode_game_state(row[0])

    def save_idempotent(self, game: GameState, command_id: str, command_hash: str) -> GameState:
        payload = _encode_game_state(game)
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    INSERT INTO commands (game_id, command_id, command_hash, state)
                    VALUES (?, ?, ?, ?)
                    """,
                    (game.id, command_id, command_hash, payload),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO games (id, state) VALUES (?, ?)",
                    (game.id, payload),
                )
            except sqlite3.IntegrityError:
                row = conn.execute(
                    """
                    SELECT state, command_hash
                    FROM commands
                    WHERE game_id = ? AND command_id = ?
                    """,
                    (game.id, command_id),
                ).fetchone()
                conn.rollback()
                if row is None:
                    raise
                existing_hash = row[1]
                if isinstance(existing_hash, str) and existing_hash != command_hash:
                    raise ValueError(
                        "Idempotency-Key reutilizado com payload diferente."
                    ) from None
                existing = self._decode_game_state(row[0])
                if existing is None:
                    raise ValueError("Estado idempotente invalido.") from None
                return existing
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
                return game
