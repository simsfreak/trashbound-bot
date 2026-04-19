from contextlib import contextmanager

import psycopg

from config import DATABASE_URL


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS players (
        user_id BIGINT PRIMARY KEY,
        username TEXT NOT NULL,
        coins INTEGER NOT NULL DEFAULT 0,
        xp INTEGER NOT NULL DEFAULT 0,
        level INTEGER NOT NULL DEFAULT 1,
        current_zone_id TEXT NOT NULL DEFAULT 'back_alley',
        current_title TEXT NOT NULL DEFAULT 'Trash Rookie',
        total_dives INTEGER NOT NULL DEFAULT 0,
        game_currency INTEGER NOT NULL DEFAULT 0,
        dirty_tickets INTEGER NOT NULL DEFAULT 0,
        pawn_relationship INTEGER NOT NULL DEFAULT 0,
        last_pawn_chat_date DATE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        last_dive_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        item_id TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        acquired_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, item_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS unlocked_zones (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        zone_id TEXT NOT NULL,
        unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (user_id, zone_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contact_messages (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        username TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        status TEXT NOT NULL DEFAULT 'open'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_progress (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        event_key TEXT NOT NULL,
        progress INTEGER NOT NULL DEFAULT 0,
        UNIQUE (user_id, event_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS active_effects (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        effect_id TEXT NOT NULL,
        source_item_id TEXT,
        multiplier NUMERIC NOT NULL DEFAULT 1.0,
        label TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS player_equipment (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        slot TEXT NOT NULL,
        item_id TEXT NOT NULL,
        equipped_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (user_id, slot)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS museum_discoveries (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        item_id TEXT NOT NULL,
        discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (user_id, item_id)
    )
    """,
]


@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()



def run_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
