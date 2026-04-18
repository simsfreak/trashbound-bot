CREATE TABLE IF NOT EXISTS players (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    coins INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    current_zone_id TEXT NOT NULL DEFAULT 'back_alley',
    current_title TEXT NOT NULL DEFAULT 'Trash Rookie',
    total_dives INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_dive_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    acquired_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, item_id)
);

CREATE TABLE IF NOT EXISTS unlocked_zones (
    user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    zone_id TEXT NOT NULL,
    unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, zone_id)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS event_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    event_key TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, event_key)
);
