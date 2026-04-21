from datetime import datetime, timedelta
from decimal import Decimal

from db.database import get_conn
from game.data import ZONES


def ensure_player(user_id: int, username: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO players (user_id, username)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username
                """,
                (user_id, username),
            )
            cur.execute(
                """
                INSERT INTO unlocked_zones (user_id, zone_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, "back_alley"),
            )


def get_player(user_id: int) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username, coins, xp, level, current_zone_id, current_title, total_dives, last_dive_at
                FROM players
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row[0],
                "username": row[1],
                "coins": row[2],
                "xp": row[3],
                "level": row[4],
                "current_zone_id": row[5],
                "current_title": row[6],
                "total_dives": row[7],
                "last_dive_at": row[8],
            }


def add_item_to_inventory(user_id: int, item_id: str, quantity: int = 1) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inventory (user_id, item_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, item_id)
                DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity,
                              acquired_at = NOW()
                """,
                (user_id, item_id, quantity),
            )

    mark_item_discovered(user_id, item_id)


def mark_item_discovered(user_id: int, item_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO museum_discoveries (user_id, item_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, item_id),
            )


def get_discovered_item_ids(user_id: int) -> set[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_id
                FROM museum_discoveries
                WHERE user_id = %s
                ORDER BY discovered_at ASC
                """,
                (user_id,),
            )
            return {row[0] for row in cur.fetchall()}


def remove_item_from_inventory(user_id: int, item_id: str, quantity: int = 1) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT quantity
                FROM inventory
                WHERE user_id = %s AND item_id = %s
                """,
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row or row[0] < quantity:
                return False

            new_qty = row[0] - quantity
            if new_qty <= 0:
                cur.execute(
                    "DELETE FROM inventory WHERE user_id = %s AND item_id = %s",
                    (user_id, item_id),
                )
            else:
                cur.execute(
                    "UPDATE inventory SET quantity = %s WHERE user_id = %s AND item_id = %s",
                    (new_qty, user_id, item_id),
                )
    return True


def get_inventory(user_id: int) -> list[tuple[str, int]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_id, quantity
                FROM inventory
                WHERE user_id = %s
                ORDER BY acquired_at DESC, item_id ASC
                """,
                (user_id,),
            )
            return cur.fetchall()


def get_inventory_map(user_id: int) -> dict[str, int]:
    return {item_id: qty for item_id, qty in get_inventory(user_id)}


def update_player_progress(
    user_id: int,
    coins: int,
    xp: int,
    level: int,
    current_title: str,
    total_dives: int,
) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET coins = %s,
                    xp = %s,
                    level = %s,
                    current_title = %s,
                    total_dives = %s,
                    last_dive_at = NOW()
                WHERE user_id = %s
                """,
                (coins, xp, level, current_title, total_dives, user_id),
            )


def get_unlocked_zone_ids(user_id: int) -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT zone_id
                FROM unlocked_zones
                WHERE user_id = %s
                ORDER BY unlocked_at ASC
                """,
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]


def unlock_zones_for_level(user_id: int, level: int) -> list[str]:
    unlocked: list[str] = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            for zone_id, zone_data in ZONES.items():
                if level >= zone_data["unlock_level"]:
                    cur.execute(
                        """
                        INSERT INTO unlocked_zones (user_id, zone_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (user_id, zone_id),
                    )
                    unlocked.append(zone_id)
    return unlocked


def set_current_zone(user_id: int, zone_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET current_zone_id = %s
                WHERE user_id = %s
                """,
                (zone_id, user_id),
            )


def save_contact_message(user_id: int, username: str, subject: str, message: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO contact_messages (user_id, username, subject, message)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, username, subject, message),
            )


def get_active_effects(user_id: int) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, effect_id, label, expires_at
                FROM active_effects
                WHERE user_id = %s AND expires_at > NOW()
                ORDER BY expires_at ASC
                """,
                (user_id,),
            )
            return [
                {
                    "id": row[0],
                    "effect_id": row[1],
                    "label": row[2],
                    "expires_at": row[3].isoformat() if row[3] else None,
                }
                for row in cur.fetchall()
            ]


def get_equipped_items(user_id: int) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT slot, item_id
                FROM player_equipment
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return [{"slot": row[0], "item_id": row[1]} for row in cur.fetchall()]
