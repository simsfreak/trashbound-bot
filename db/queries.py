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
                SELECT user_id, username, coins, xp, level, current_zone_id, current_title, total_dives, hunger, last_dive_at
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
                "hunger": row[8] if row[8] is not None else 100,
                "last_dive_at": row[9],
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


def add_active_effect(
    user_id: int,
    effect_id: str,
    label: str,
    multiplier: float,
    duration_hours: int,
    source_item_id: str = None,
) -> None:
    """Add an active effect to the player. Replaces existing effect of same type if present."""
    from datetime import datetime, timedelta
    
    expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Remove any existing effect of the same type
            cur.execute(
                """
                DELETE FROM active_effects
                WHERE user_id = %s AND effect_id = %s
                """,
                (user_id, effect_id),
            )
            
            # Add the new effect
            cur.execute(
                """
                INSERT INTO active_effects (user_id, effect_id, label, multiplier, expires_at, source_item_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, effect_id, label, multiplier, expires_at, source_item_id),
            )


def get_active_effect(user_id: int, effect_id: str) -> dict | None:
    """Get a specific active effect if it exists and hasn't expired."""
    from datetime import datetime
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, effect_id, label, multiplier, expires_at
                FROM active_effects
                WHERE user_id = %s AND effect_id = %s AND expires_at > NOW()
                """,
                (user_id, effect_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": row[0],
                "effect_id": row[1],
                "label": row[2],
                "multiplier": row[3],
                "expires_at": row[4],
            }


def get_xp_multiplier(user_id: int) -> float:
    """Get the current XP multiplier from active effects."""
    effect = get_active_effect(user_id, "xp_buffer")
    if effect:
        return float(effect["multiplier"])
    return 1.0


def get_luck_bonus(user_id: int) -> float:
    """Get the current luck bonus from active effects (as percentage)."""
    effect = get_active_effect(user_id, "luck_amulet")
    if effect:
        return float(effect["multiplier"])
    return 0.0


# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE COLLECTIBLES QUERIES
# ═══════════════════════════════════════════════════════════════════

def get_exclusive_inventory(user_id: int) -> list[dict]:
    """Get all exclusive items owned by a player."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT exclusive_id, acquired_at, equipped
                FROM exclusive_inventory
                WHERE user_id = %s
                ORDER BY acquired_at DESC
                """,
                (user_id,),
            )
            return [
                {
                    "exclusive_id": row[0],
                    "acquired_at": row[1].isoformat() if row[1] else None,
                    "equipped": row[2],
                }
                for row in cur.fetchall()
            ]


def add_exclusive_to_inventory(user_id: int, exclusive_id: str) -> None:
    """Add an exclusive item to a player's inventory."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO exclusive_inventory (user_id, exclusive_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, exclusive_id) DO NOTHING
                """,
                (user_id, exclusive_id),
            )


def get_exclusive_counts(user_id: int) -> dict:
    """Get counts of exclusive items by category."""
    from game.data import EXCLUSIVE_ITEMS
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT exclusive_id
                FROM exclusive_inventory
                WHERE user_id = %s
                """,
                (user_id,),
            )
            owned_ids = [row[0] for row in cur.fetchall()]
    
    # Count by category
    counts = {"Toys": 0, "Dogs": 0, "Cats": 0, "Wings": 0}
    for exclusive_id in owned_ids:
        if exclusive_id in EXCLUSIVE_ITEMS:
            category = EXCLUSIVE_ITEMS[exclusive_id].get("category")
            if category in counts:
                counts[category] += 1
    
    return counts


def get_exclusives_by_category(user_id: int, category: str) -> list[dict]:
    """Get all exclusive items in a specific category owned by a player."""
    from game.data import EXCLUSIVE_ITEMS
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT exclusive_id, acquired_at
                FROM exclusive_inventory
                WHERE user_id = %s
                ORDER BY acquired_at DESC
                """,
                (user_id,),
            )
            owned = [row[0] for row in cur.fetchall()]
    
    # Filter by category
    result = []
    for exclusive_id in owned:
        if exclusive_id in EXCLUSIVE_ITEMS:
            item = EXCLUSIVE_ITEMS[exclusive_id]
            if item.get("category") == category:
                result.append({
                    "exclusive_id": exclusive_id,
                    "name": item.get("name"),
                    "flavor": item.get("flavor"),
                })
    
    return result


# ═══════════════════════════════════════════════════════════════════
# HUNGER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def reduce_hunger(user_id: int, amount: int = 1) -> int:
    """Reduce hunger by specified amount. Returns new hunger value."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT hunger FROM players WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            current_hunger = row[0] if row else 100
            
            new_hunger = max(0, current_hunger - amount)
            
            cur.execute(
                """
                UPDATE players SET hunger = %s WHERE user_id = %s
                """,
                (new_hunger, user_id),
            )
    
    return new_hunger


def feed_player(user_id: int, hunger_restored: int) -> int:
    """Feed player and restore hunger. Returns new hunger value."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT hunger FROM players WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            current_hunger = row[0] if row else 100
            
            new_hunger = min(100, current_hunger + hunger_restored)
            
            cur.execute(
                """
                UPDATE players SET hunger = %s, last_fed_at = NOW() WHERE user_id = %s
                """,
                (new_hunger, user_id),
            )
    
    return new_hunger


# ═══════════════════════════════════════════════════════════════════
# ZONE SYSTEM QUERIES
# ═══════════════════════════════════════════════════════════════════

def get_zone_event(user_id: int, zone_id: str) -> dict | None:
    """Get active zone event for a user."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, zone_id, difficulty, is_active, mission_target_item_id,
                       mission_target_qty, mission_progress, timer_end_at
                FROM zone_events
                WHERE user_id = %s AND zone_id = %s
                """,
                (user_id, zone_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": row[0],
                "zone_id": row[1],
                "difficulty": row[2],
                "is_active": row[3],
                "mission_target_item_id": row[4],
                "mission_target_qty": row[5],
                "mission_progress": row[6],
                "timer_end_at": row[7],
            }


def start_zone_event(user_id: int, zone_id: str, difficulty: str = "Medium") -> dict:
    """Start a new zone event with mission."""
    from game.zones import generate_mission
    
    mission = generate_mission(zone_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO zone_events
                (user_id, zone_id, difficulty, is_active, activated_at, timer_end_at,
                 mission_id, mission_target_item_id, mission_target_qty, mission_progress)
                VALUES (%s, %s, %s, true, NOW(), NOW() + INTERVAL '1 hour', %s, %s, %s, 0)
                ON CONFLICT (user_id, zone_id)
                DO UPDATE SET
                    is_active = true,
                    activated_at = NOW(),
                    timer_end_at = NOW() + INTERVAL '1 hour',
                    mission_target_item_id = EXCLUDED.mission_target_item_id,
                    mission_target_qty = EXCLUDED.mission_target_qty,
                    mission_progress = 0
                RETURNING id
                """,
                (user_id, zone_id, difficulty, f"mission_{zone_id}_{user_id}",
                 mission.get("target_item_id"), mission.get("target_qty")),
            )
            row = cur.fetchone()
    
    return {"event_id": row[0], "mission": mission}


def add_zone_harvest(user_id: int, zone_id: str, item_id: str, rarity: str,
                     metadata_type: str = None, metadata_value: str = None) -> None:
    """Record a harvested item from a zone."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO zone_harvests
                (user_id, zone_id, item_id, rarity, metadata_type, metadata_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, zone_id, item_id, rarity, metadata_type, metadata_value),
            )


def update_mission_progress(user_id: int, zone_id: str, progress_increment: int) -> int:
    """Update mission progress. Returns new progress."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE zone_events
                SET mission_progress = mission_progress + %s
                WHERE user_id = %s AND zone_id = %s
                RETURNING mission_progress
                """,
                (progress_increment, user_id, zone_id),
            )
            row = cur.fetchone()
            return row[0] if row else 0


def complete_zone_event(user_id: int, zone_id: str) -> None:
    """Mark zone event as complete."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE zone_events
                SET is_active = false
                WHERE user_id = %s AND zone_id = %s
                """,
                (user_id, zone_id),
            )



def get_hunger(user_id: int) -> int:
    """Get current hunger level (0-100)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT hunger FROM players WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 100
