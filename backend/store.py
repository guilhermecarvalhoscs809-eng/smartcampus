"""SQLite persistence helpers for the SmartCampus V1 local draft."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "smartcampus-demo.sqlite3"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
SEED_PATH = ROOT / "frontend" / "static" / "js" / "dados-demo.js"
COLLECTIONS = (
    "salas",
    "armarios",
    "equipamentos",
    "utilizadores",
    "destinatarios",
    "atribuicoes",
    "avarias",
    "transferencias",
    "eventos",
    "logs",
)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def database_connection():
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), hashed.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return secrets.compare_digest(candidate, hash_hex)


def read_demo_seed() -> dict[str, list[dict[str, Any]]]:
    source = SEED_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"window\.SMARTCAMPUS_SEED\s*=\s*(\{.*\})\s*;",
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise RuntimeError(f"Não foi possível ler os dados demo em {SEED_PATH}")
    seed = json.loads(match.group(1))
    for collection in COLLECTIONS:
        if not isinstance(seed.get(collection), list):
            raise RuntimeError(f"A coleção demo {collection!r} não é uma lista")
    return seed


def initialize() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with database_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if count:
            return

        seed = read_demo_seed()
        for collection in COLLECTIONS:
            connection.executemany(
                "INSERT INTO records (collection, id, data_json) VALUES (?, ?, ?)",
                [
                    (
                        collection,
                        str(item["id"]),
                        json.dumps(item, ensure_ascii=False, separators=(",", ":")),
                    )
                    for item in seed[collection]
                ],
            )

        for user in seed["utilizadores"]:
            salt, hashed = hash_password("demo1234")
            connection.execute(
                "INSERT INTO credentials (user_id, password_salt, password_hash) "
                "VALUES (?, ?, ?)",
                (user["id"], salt, hashed),
            )


def load_state(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    state = {collection: [] for collection in COLLECTIONS}
    for row in connection.execute(
        "SELECT collection, data_json FROM records ORDER BY rowid"
    ):
        state[row["collection"]].append(json.loads(row["data_json"]))
    return state


def replace_state(
    connection: sqlite3.Connection, state: dict[str, list[dict[str, Any]]]
) -> None:
    connection.execute("DELETE FROM records")
    for collection in COLLECTIONS:
        connection.executemany(
            "INSERT INTO records (collection, id, data_json) VALUES (?, ?, ?)",
            [
                (
                    collection,
                    str(item["id"]),
                    json.dumps(item, ensure_ascii=False, separators=(",", ":")),
                )
                for item in state[collection]
            ],
        )


def get_record(
    connection: sqlite3.Connection, collection: str, record_id: str
) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT data_json FROM records WHERE collection = ? AND id = ?",
        (collection, record_id),
    ).fetchone()
    return json.loads(row["data_json"]) if row else None
