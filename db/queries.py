import random
from datetime import datetime, timedelta, date
from decimal import Decimal

from db.database import get_conn
from game.data import DAILY_QUEST_TEMPLATES, ITEMS, ZONES, MUSEUM_COLLECTIONS


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
                SELECT user_id, username, coins, xp, level, current_zone_id, current_title, total_dives, last_dive_at, dirty_tickets, pawn_relationship, last_pawn_chat_date, museum_xp, museum_level
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
                "dirty_tickets": row[9],
                "pawn_relationship": row[10],
                "last_pawn_chat_date": row[11],
                "museum_xp": row[12],
                "museum_level": row[13],
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


def get_equipped_items(user_id: int) -> list[dict[str, str]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT slot, item_id
                FROM player_equipment
                WHERE user_id = %s
                ORDER BY slot
                """,
                (user_id,),
            )
            return [{"slot": row[0], "item_id": row[1]} for row in cur.fetchall()]


def equip_item(user_id: int, item_id: str) -> bool:
    item = ITEMS.get(item_id)
    if not item or not item.get("equip_slot"):
        return False

    slot = item["equip_slot"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT item_id FROM player_equipment WHERE user_id = %s AND slot = %s",
                (user_id, slot),
            )
            row = cur.fetchone()
            old_item_id = row[0] if row else None

            cur.execute(
                "SELECT quantity FROM inventory WHERE user_id = %s AND item_id = %s",
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row or row[0] < 1:
                return False

            if old_item_id:
                cur.execute(
                    """
                    INSERT INTO inventory (user_id, item_id, quantity)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (user_id, item_id)
                    DO UPDATE SET quantity = inventory.quantity + 1,
                                  acquired_at = NOW()
                    """,
                    (user_id, old_item_id),
                )

            cur.execute(
                "UPDATE inventory SET quantity = quantity - 1 WHERE user_id = %s AND item_id = %s",
                (user_id, item_id),
            )
            cur.execute(
                "DELETE FROM inventory WHERE user_id = %s AND item_id = %s AND quantity <= 0",
                (user_id, item_id),
            )

            cur.execute(
                """
                INSERT INTO player_equipment (user_id, slot, item_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, slot)
                DO UPDATE SET item_id = EXCLUDED.item_id, equipped_at = NOW()
                """,
                (user_id, slot, item_id),
            )
    return True


def unequip_item(user_id: int, slot: str) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT item_id FROM player_equipment WHERE user_id = %s AND slot = %s",
                (user_id, slot),
            )
            row = cur.fetchone()
            if not row:
                return False
            item_id = row[0]

            cur.execute(
                "DELETE FROM player_equipment WHERE user_id = %s AND slot = %s",
                (user_id, slot),
            )
            cur.execute(
                """
                INSERT INTO inventory (user_id, item_id, quantity)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, item_id)
                DO UPDATE SET quantity = inventory.quantity + 1,
                              acquired_at = NOW()
                """,
                (user_id, item_id),
            )
    return True


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


def _create_daily_quest_row(user_id: int, template: dict) -> None:
    expires_at = datetime.utcnow() + timedelta(hours=24)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_quests (
                    user_id,
                    quest_key,
                    quest_type,
                    name,
                    description,
                    progress,
                    target,
                    reward_coins,
                    reward_tickets,
                    started_at,
                    expires_at,
                    completed,
                    redeemed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    quest_key = EXCLUDED.quest_key,
                    quest_type = EXCLUDED.quest_type,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    progress = EXCLUDED.progress,
                    target = EXCLUDED.target,
                    reward_coins = EXCLUDED.reward_coins,
                    reward_tickets = EXCLUDED.reward_tickets,
                    started_at = EXCLUDED.started_at,
                    expires_at = EXCLUDED.expires_at,
                    completed = EXCLUDED.completed,
                    redeemed = EXCLUDED.redeemed
                """,
                (
                    user_id,
                    template["quest_key"],
                    template["quest_type"],
                    template["name"],
                    template["description"],
                    0,
                    template["target"],
                    template["reward_coins"],
                    template["reward_tickets"],
                    datetime.utcnow(),
                    expires_at,
                    False,
                    False,
                ),
            )


def ensure_daily_quest(user_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT expires_at FROM daily_quests WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            if row and row[0] and row[0] > datetime.utcnow():
                return
    template = random.choice(DAILY_QUEST_TEMPLATES)
    _create_daily_quest_row(user_id, template)


def get_daily_quest(user_id: int) -> dict | None:
    ensure_daily_quest(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT quest_key, quest_type, name, description, progress, target, reward_coins, reward_tickets, started_at, expires_at, completed, redeemed
                FROM daily_quests
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "quest_key": row[0],
                "quest_type": row[1],
                "name": row[2],
                "description": row[3],
                "progress": row[4],
                "target": row[5],
                "reward_coins": row[6],
                "reward_tickets": row[7],
                "started_at": row[8],
                "expires_at": row[9],
                "completed": row[10],
                "redeemed": row[11],
            }


def progress_daily_quest(user_id: int, event_type: str, amount: int = 1) -> bool:
    ensure_daily_quest(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT progress, target, completed, redeemed, expires_at, quest_type
                FROM daily_quests
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return False
            progress, target, completed, redeemed, expires_at, quest_type = row
            if redeemed or completed or expires_at <= datetime.utcnow() or quest_type != event_type:
                return False
            new_progress = min(progress + amount, target)
            completed_flag = new_progress >= target
            cur.execute(
                """
                UPDATE daily_quests
                SET progress = %s, completed = %s
                WHERE user_id = %s
                """,
                (new_progress, completed_flag, user_id),
            )
            return True


def redeem_daily_quest(user_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT progress, target, completed, redeemed, expires_at, reward_coins, reward_tickets
                FROM daily_quests
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return False
            progress, target, completed, redeemed, expires_at, reward_coins, reward_tickets = row
            if redeemed or not completed or expires_at <= datetime.utcnow():
                return False
            cur.execute(
                """
                UPDATE players
                SET coins = coins + %s,
                    dirty_tickets = dirty_tickets + %s
                WHERE user_id = %s
                """,
                (reward_coins, reward_tickets, user_id),
            )
            cur.execute(
                """
                UPDATE daily_quests
                SET redeemed = TRUE
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return True


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


def add_player_coins(user_id: int, coins_delta: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET coins = coins + %s
                WHERE user_id = %s
                """,
                (coins_delta, user_id),
            )


def buy_dirty_tickets(user_id: int, coins_cost: int, ticket_count: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET coins = coins - %s,
                    dirty_tickets = dirty_tickets + %s
                WHERE user_id = %s AND coins >= %s
                RETURNING user_id
                """,
                (coins_cost, ticket_count, user_id, coins_cost),
            )
            return cur.fetchone() is not None


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
                        RETURNING zone_id
                        """,
                        (user_id, zone_id),
                    )
                    inserted = cur.fetchone()
                    if inserted:
                        unlocked.append(inserted[0])
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


def get_all_contact_messages() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, username, subject, message, created_at, status
                FROM contact_messages
                ORDER BY created_at DESC
                """
            )
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "subject": row[3],
                    "message": row[4],
                    "created_at": row[5],
                    "status": row[6],
                }
                for row in cur.fetchall()
            ]


def get_contact_message_by_id(message_id: int) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, username, subject, message, created_at, status
                FROM contact_messages
                WHERE id = %s
                """,
                (message_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "user_id": row[1],
                "username": row[2],
                "subject": row[3],
                "message": row[4],
                "created_at": row[5],
                "status": row[6],
            }


def mark_contact_message_read(message_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE contact_messages
                SET status = 'read'
                WHERE id = %s
                """,
                (message_id,),
            )


def grant_player_xp(user_id: int, xp_amount: int) -> bool:
    player = get_player(user_id)
    if not player:
        return False
    
    from game.leveling import apply_xp
    from game.helpers import determine_title
    
    new_xp, new_level, leveled_up = apply_xp(player["xp"], player["level"], xp_amount)
    new_title = determine_title(new_level)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET xp = %s, level = %s, current_title = %s
                WHERE user_id = %s
                """,
                (new_xp, new_level, new_title, user_id),
            )
    return True


def grant_player_coins(user_id: int, coins_amount: int) -> bool:
    player = get_player(user_id)
    if not player:
        return False
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET coins = coins + %s
                WHERE user_id = %s
                """,
                (coins_amount, user_id),
            )
    return True


def grant_player_tickets(user_id: int, tickets_amount: int) -> bool:
    player = get_player(user_id)
    if not player:
        return False
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET dirty_tickets = dirty_tickets + %s
                WHERE user_id = %s
                """,
                (tickets_amount, user_id),
            )
    return True


def add_active_effect(
    user_id: int,
    effect_id: str,
    source_item_id: str,
    label: str,
    multiplier: float | Decimal,
    duration_minutes: int,
) -> None:
    expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM active_effects WHERE user_id = %s AND effect_id = %s",
                (user_id, effect_id),
            )
            cur.execute(
                """
                INSERT INTO active_effects (user_id, effect_id, source_item_id, multiplier, label, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, effect_id, source_item_id, multiplier, label, expires_at),
            )


def cleanup_expired_effects(user_id: int | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if user_id is None:
                cur.execute("DELETE FROM active_effects WHERE expires_at <= NOW()")
            else:
                cur.execute(
                    "DELETE FROM active_effects WHERE user_id = %s AND expires_at <= NOW()",
                    (user_id,),
                )


def get_active_effects(user_id: int) -> list[dict]:
    cleanup_expired_effects(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT effect_id, source_item_id, multiplier, label, expires_at
                FROM active_effects
                WHERE user_id = %s
                ORDER BY expires_at ASC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "effect_id": row[0],
                    "source_item_id": row[1],
                    "multiplier": float(row[2]),
                    "label": row[3],
                    "expires_at": row[4],
                }
                for row in rows
            ]


def get_effect_multiplier(user_id: int, effect_id: str) -> float:
    cleanup_expired_effects(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(multiplier), 1.0)
                FROM active_effects
                WHERE user_id = %s AND effect_id = %s
                """,
                (user_id, effect_id),
            )
            row = cur.fetchone()
            return float(row[0] or 1.0)


def use_dirty_tickets(user_id: int, ticket_count: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET dirty_tickets = dirty_tickets - %s
                WHERE user_id = %s AND dirty_tickets >= %s
                RETURNING user_id
                """,
                (ticket_count, user_id, ticket_count),
            )
            return cur.fetchone() is not None

def can_chat_with_pawn_owner(user_id: int) -> bool:
    player = get_player(user_id)
    if not player:
        return False

    last_chat = player.get("last_pawn_chat_date")
    return last_chat != date.today()
    
def update_pawn_chat(
    user_id: int,
    relationship_delta: int = 0,
    coins_delta: int = 0,
    dirty_ticket_delta: int = 0,
) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                SET pawn_relationship = pawn_relationship + %s,
                    coins = coins + %s,
                    dirty_tickets = dirty_tickets + %s,
                    last_pawn_chat_date = CURRENT_DATE
                WHERE user_id = %s
                """,
                (relationship_delta, coins_delta, dirty_ticket_delta, user_id),
             )
                

def get_equipment(user_id: int) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT slot, item_id, equipped_at
                FROM player_equipment
                WHERE user_id = %s
                ORDER BY equipped_at ASC
                """,
                (user_id,),
            )
            return [
                {"slot": row[0], "item_id": row[1], "equipped_at": row[2]}
                for row in cur.fetchall()
            ]


def get_completed_collections(user_id: int) -> set[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT collection_key
                FROM museum_completed_collections
                WHERE user_id = %s
                ORDER BY completed_at ASC
                """,
                (user_id,),
            )
            return {row[0] for row in cur.fetchall()}


def complete_collection(user_id: int, collection_key: str, xp_award: int = 50) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO museum_completed_collections (user_id, collection_key, completed_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (user_id, collection_key) DO NOTHING
                RETURNING collection_key
                """,
                (user_id, collection_key),
            )
            if not cur.fetchone():
                return False
            
            cur.execute(
                """
                UPDATE players
                SET museum_xp = museum_xp + %s
                WHERE user_id = %s
                """,
                (xp_award, user_id),
            )
            return True


def get_collection_progress(user_id: int, collection_key: str, required_item_ids: list[str]) -> int:
    discovered = get_discovered_item_ids(user_id)
    return sum(1 for item_id in required_item_ids if item_id in discovered)


def update_museum_level(user_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT museum_xp FROM players WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return 1
            
            museum_xp = row[0]
            new_level = 1 + (museum_xp // 100)
            
            cur.execute(
                """
                UPDATE players
                SET museum_level = %s
                WHERE user_id = %s
                """,
                (new_level, user_id),
            )
            return new_level


def check_and_complete_collections(user_id: int) -> list[str]:
    """Check for any newly completed collections and award XP."""
    discovered = get_discovered_item_ids(user_id)
    completed = get_completed_collections(user_id)
    
    newly_completed: list[str] = []
    for collection_key, collection_data in MUSEUM_COLLECTIONS.items():
        if collection_key in completed:
            continue
        
        required_items = set(collection_data.get("item_ids", []))
        if required_items.issubset(discovered):
            if complete_collection(user_id, collection_key, xp_award=50):
                newly_completed.append(collection_key)
    
    if newly_completed:
        update_museum_level(user_id)
    
    return newly_completed
