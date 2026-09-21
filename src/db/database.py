import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# Database path
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

DATABASE_PATH = DATA_DIR / "travel_ai.db"


# =========================================================
# Database connection
# =========================================================

def get_connection():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# Helpers
# =========================================================

def get_current_time():
    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# Database initialization
# =========================================================

def init_database():
    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                session_id TEXT NOT NULL,

                role TEXT NOT NULL,

                content TEXT NOT NULL,

                services TEXT,

                sources TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                    REFERENCES conversations(session_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()


# =========================================================
# Conversations
# =========================================================

def create_conversation(
    session_id: str,
    title: str = "New conversation"
):
    now = get_current_time()

    with get_connection() as connection:

        connection.execute(
            """
            INSERT OR IGNORE INTO conversations (
                session_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                title,
                now,
                now
            )
        )

        connection.commit()


def get_conversations():
    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                session_id,
                title,
                created_at,
                updated_at
            FROM conversations
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]

def get_conversation(
    session_id: str
):
    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                session_id,
                title,
                created_at,
                updated_at

            FROM conversations

            WHERE session_id = ?
            """,
            (
                session_id,
            )
        ).fetchone()

    if row is None:
        return None

    return dict(row)

def update_conversation_title(
    session_id: str,
    title: str
):
    now = get_current_time()

    with get_connection() as connection:

        connection.execute(
            """
            UPDATE conversations

            SET
                title = ?,
                updated_at = ?

            WHERE session_id = ?
            """,
            (
                title,
                now,
                session_id
            )
        )

        connection.commit()


def delete_conversation(
    session_id: str
):
    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM conversations
            WHERE session_id = ?
            """,
            (
                session_id,
            )
        )

        connection.commit()


# =========================================================
# Messages
# =========================================================

def save_message(
    session_id: str,
    role: str,
    content: str,
    services: list[str] | None = None,
    sources: list[str] | None = None
):
    now = get_current_time()

    services_json = json.dumps(
        services or [],
        ensure_ascii=False
    )

    sources_json = json.dumps(
        sources or [],
        ensure_ascii=False
    )

    with get_connection() as connection:

        # Make sure conversation exists
        connection.execute(
            """
            INSERT OR IGNORE INTO conversations (
                session_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                "New conversation",
                now,
                now
            )
        )

        connection.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                content,
                services,
                sources,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                services_json,
                sources_json,
                now
            )
        )

        connection.execute(
            """
            UPDATE conversations

            SET updated_at = ?

            WHERE session_id = ?
            """,
            (
                now,
                session_id
            )
        )

        connection.commit()


def get_messages(
    session_id: str
):
    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                session_id,
                role,
                content,
                services,
                sources,
                created_at

            FROM messages

            WHERE session_id = ?

            ORDER BY id ASC
            """,
            (
                session_id,
            )
        ).fetchall()

    messages = []

    for row in rows:
        message = dict(row)

        message["services"] = (
            json.loads(
                message["services"]
            )
            if message["services"]
            else []
        )

        message["sources"] = (
            json.loads(
                message["sources"]
            )
            if message["sources"]
            else []
        )

        messages.append(
            message
        )

    return messages

def get_recent_messages(
    session_id: str,
    limit: int = 6
):
    """
    Get the most recent messages
    and return them in chronological order.
    """

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                session_id,
                role,
                content,
                services,
                sources,
                created_at

            FROM messages

            WHERE session_id = ?

            ORDER BY id DESC

            LIMIT ?
            """,
            (
                session_id,
                limit
            )
        ).fetchall()

    rows = list(
        reversed(rows)
    )

    messages = []

    for row in rows:
        message = dict(row)

        message["services"] = (
            json.loads(
                message["services"]
            )
            if message["services"]
            else []
        )

        message["sources"] = (
            json.loads(
                message["sources"]
            )
            if message["sources"]
            else []
        )

        messages.append(
            message
        )

    return messages

def get_message_count(
    session_id: str
):
    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT COUNT(*) AS count

            FROM messages

            WHERE session_id = ?
            """,
            (
                session_id,
            )
        ).fetchone()

    return row["count"]