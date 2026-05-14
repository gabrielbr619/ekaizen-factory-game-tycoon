from __future__ import annotations

import pickle
import sqlite3
from contextlib import closing
from pathlib import Path

from app.domain.models import GameState


class GameRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _decode_game_state(self, state_blob: object) -> GameState | None:
        if not isinstance(state_blob, bytes):
            return None
        loaded = pickle.loads(state_blob)
        if isinstance(loaded, GameState):
            return loaded
        return None

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS games (id TEXT PRIMARY KEY, state BLOB NOT NULL)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    game_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    command_hash TEXT,
                    state BLOB NOT NULL,
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
                    state BLOB NOT NULL
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
        payload = pickle.dumps(game)
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
        payload = pickle.dumps(game)
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
        payload = pickle.dumps(game)
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
