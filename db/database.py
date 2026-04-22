from contextlib import contextmanager

import psycopg

from config import DATABASE_URL


SCHEMA_STATEMENTS = [
    # Migration: Add hunger and last_fed_at columns if they don't exist
    """
    ALTER TABLE IF EXISTS players
    ADD COLUMN IF NOT EXISTS hunger INTEGER NOT NULL DEFAULT 100
    """,
    """
    ALTER TABLE IF EXISTS players
    ADD COLUMN IF NOT EXISTS last_fed_at TIMESTAMP
    """,
    """
    ALTER TABLE IF EXISTS players
    ADD COLUMN IF NOT EXISTS dirty_tickets INTEGER NOT NULL DEFAULT 0
    """,
    """
    CREATE TABLE IF NOT EXISTS players (
        user_id BIGINT PRIMARY KEY,
        username TEXT NOT NULL,
        coins INTEGER NOT NULL DEFAULT 0,
        xp INTEGER NOT NULL DEFAULT 0,
        level INTEGER NOT NULL DEFAULT 1,
        current_zone_id TEXT NOT NULL DEFAULT 'fishing',
        current_title TEXT NOT NULL DEFAULT 'Trash Rookie',
        total_dives INTEGER NOT NULL DEFAULT 0,
        hunger INTEGER NOT NULL DEFAULT 100,
        last_fed_at TIMESTAMP,
        dirty_tickets INTEGER NOT NULL DEFAULT 0,
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
    """
    CREATE TABLE IF NOT EXISTS exclusive_inventory (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        exclusive_id TEXT NOT NULL,
        acquired_at TIMESTAMP NOT NULL DEFAULT NOW(),
        equipped BOOLEAN DEFAULT FALSE,
        UNIQUE (user_id, exclusive_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS food_purchases (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        food_id TEXT NOT NULL,
        hunger_restored INTEGER NOT NULL,
        purchased_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS zone_events (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        zone_id TEXT NOT NULL,
        difficulty TEXT NOT NULL DEFAULT 'Medium',
        is_active BOOLEAN DEFAULT FALSE,
        activated_at TIMESTAMP,
        timer_end_at TIMESTAMP,
        mission_id TEXT,
        mission_target_item_id TEXT,
        mission_target_qty INTEGER DEFAULT 0,
        mission_progress INTEGER DEFAULT 0,
        last_action_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, zone_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS zone_harvests (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        zone_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        rarity TEXT NOT NULL,
        metadata_type TEXT,
        metadata_value TEXT,
        harvested_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS zone_actions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        zone_id TEXT NOT NULL,
        last_action_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, zone_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS player_relics (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        relic_id TEXT NOT NULL,
        set_id TEXT NOT NULL,
        rarity TEXT NOT NULL,
        collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, relic_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS museum_progress (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        set_id TEXT NOT NULL,
        relics_collected INTEGER DEFAULT 0,
        completed BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        PRIMARY KEY (user_id, set_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS museum_story (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
        chapter INTEGER NOT NULL,
        unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (user_id, chapter)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS museum_dust (
        user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE PRIMARY KEY,
        dust_amount INTEGER NOT NULL DEFAULT 0
    )
    """,
]


@contextmanager
def get_conn():
    print(f"[CONN] Creating connection to {DATABASE_URL[:20]}...")
    try:
        conn = psycopg.connect(DATABASE_URL, autocommit=False)
        print(f"[CONN] Connection created successfully")
        print(f"[CONN] Psycopg version: {psycopg.__version__}")
        try:
            yield conn
            print(f"[CONN] Committing transaction...")
            conn.commit()
            print(f"[CONN] Commit successful")
        finally:
            print(f"[CONN] Closing connection...")
            conn.close()
            print(f"[CONN] Connection closed")
    except Exception as e:
        print(f"\n[CONN ERROR] Connection failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise



def run_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
