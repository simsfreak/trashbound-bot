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
                    zone_id,
                    time,
                    difficulty,
                    flavor_text,
                    started_at,
                    expires_at,
                    completed,
                    redeemed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    zone_id = EXCLUDED.zone_id,
                    time = EXCLUDED.time,
                    difficulty = EXCLUDED.difficulty,
                    flavor_text = EXCLUDED.flavor_text,
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
                    template.get("zone_id", "back_alley"),
                    template.get("time", "morning"),
                    template.get("difficulty", 1),
                    template.get("flavor_text", "A quest awaits."),
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
                SELECT quest_key, quest_type, name, description, progress, target, reward_coins, reward_tickets, zone_id, time, difficulty, flavor_text, started_at, expires_at, completed, redeemed
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
                "zone_id": row[8],
                "time": row[9],
                "difficulty": row[10],
                "flavor_text": row[11],
                "started_at": row[12],
                "expires_at": row[13],
                "completed": row[14],
                "redeemed": row[15],
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


# ==================== GENERATED QUEST SYSTEM ====================

def store_generated_quest(user_id: int, quest: dict) -> None:
    """
    Store a newly generated quest for a player.
    Automatically orders them for pagination.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Insert the quest
            cur.execute(
                """
                INSERT INTO generated_quests (
                    user_id, quest_id, template_id, name, description,
                    objective_type, zone_id, zone_name, time, difficulty,
                    flavor_text, progress, target, reward_coins, reward_tickets,
                    objective_meta, is_active, is_completed, is_redeemed,
                    generated_at, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s::jsonb, %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (quest_id) DO NOTHING
                """,
                (
                    user_id,
                    quest.get("quest_id"),
                    quest.get("template_id"),
                    quest.get("name"),
                    quest.get("description"),
                    quest.get("objective_type"),
                    quest.get("zone_id"),
                    quest.get("zone_name"),
                    quest.get("time"),
                    quest.get("difficulty"),
                    quest.get("flavor_text"),
                    0,  # progress
                    quest.get("target", 1),
                    quest.get("reward_coins", 0),
                    quest.get("reward_tickets", 0),
                    str(quest.get("objective_meta", {})),
                    False,  # is_active
                    False,  # is_completed
                    False,  # is_redeemed
                    quest.get("generated_at", datetime.utcnow()),
                    quest.get("expires_at", datetime.utcnow() + timedelta(hours=24)),
                ),
            )
            
            # Add to pagination queue
            cur.execute(
                """
                SELECT COUNT(*) FROM quest_pagination WHERE user_id = %s
                """,
                (user_id,),
            )
            view_order = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO quest_pagination (user_id, quest_id, view_order)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, quest.get("quest_id"), view_order),
            )


def get_next_generated_quest(user_id: int) -> dict | None:
    """
    Get the next unviewed quest for a player from their pagination queue.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Get the next unviewed quest in order
            cur.execute(
                """
                SELECT gq.quest_id, gq.name, gq.description, gq.objective_type,
                       gq.zone_id, gq.zone_name, gq.time, gq.difficulty,
                       gq.flavor_text, gq.progress, gq.target,
                       gq.reward_coins, gq.reward_tickets, gq.objective_meta,
                       gq.is_active, gq.is_completed, gq.is_redeemed,
                       gq.expires_at
                FROM generated_quests gq
                INNER JOIN quest_pagination qp ON gq.quest_id = qp.quest_id
                WHERE gq.user_id = %s AND qp.viewed_at IS NULL
                ORDER BY qp.view_order ASC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            # Mark as viewed
            cur.execute(
                """
                UPDATE quest_pagination
                SET viewed_at = NOW()
                WHERE user_id = %s AND quest_id = %s
                """,
                (user_id, row[0]),
            )
            
            return {
                "quest_id": row[0],
                "name": row[1],
                "description": row[2],
                "objective_type": row[3],
                "zone_id": row[4],
                "zone_name": row[5],
                "time": row[6],
                "difficulty": row[7],
                "hearts": _difficulty_to_hearts(row[7]),
                "flavor_text": row[8],
                "progress": row[9],
                "target": row[10],
                "reward_coins": row[11],
                "reward_tickets": row[12],
                "objective_meta": row[13],
                "is_active": row[14],
                "is_completed": row[15],
                "is_redeemed": row[16],
                "expires_at": row[17],
            }


def _difficulty_to_hearts(difficulty: int) -> str:
    """Convert difficulty to hearts display"""
    hearts_map = {
        1: "♥♡♡♡♡",
        2: "♥♥♡♡♡",
        3: "♥♥♥♡♡",
        4: "♥♥♥♥♡",
        5: "♥♥♥♥♥",
    }
    return hearts_map.get(difficulty, "♥♡♡♡♡")


def set_active_quest(user_id: int, quest_id: str) -> bool:
    """
    Accept a quest and set it as the player's active quest.
    Only one quest can be active at a time.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Verify the quest exists and belongs to this player
            cur.execute(
                """
                SELECT quest_id FROM generated_quests
                WHERE user_id = %s AND quest_id = %s AND NOT is_redeemed
                """,
                (user_id, quest_id),
            )
            if not cur.fetchone():
                return False
            
            # Deactivate any previous active quest
            cur.execute(
                """
                UPDATE generated_quests
                SET is_active = FALSE
                WHERE user_id = %s AND is_active = TRUE
                """,
                (user_id,),
            )
            
            # Set this quest as active
            cur.execute(
                """
                UPDATE generated_quests
                SET is_active = TRUE
                WHERE user_id = %s AND quest_id = %s
                """,
                (user_id, quest_id),
            )
            
            # Also update the player's active_quest_id
            cur.execute(
                """
                UPDATE players
                SET active_quest_id = %s
                WHERE user_id = %s
                """,
                (quest_id, user_id),
            )
            
            return True


def get_active_quest(user_id: int) -> dict | None:
    """
    Get the player's currently active quest.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT quest_id, name, description, objective_type,
                       zone_id, zone_name, time, difficulty,
                       flavor_text, progress, target,
                       reward_coins, reward_tickets, objective_meta,
                       is_completed, is_redeemed, expires_at
                FROM generated_quests
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "quest_id": row[0],
                "name": row[1],
                "description": row[2],
                "objective_type": row[3],
                "zone_id": row[4],
                "zone_name": row[5],
                "time": row[6],
                "difficulty": row[7],
                "hearts": _difficulty_to_hearts(row[7]),
                "flavor_text": row[8],
                "progress": row[9],
                "target": row[10],
                "reward_coins": row[11],
                "reward_tickets": row[12],
                "objective_meta": row[13],
                "is_completed": row[14],
                "is_redeemed": row[15],
                "expires_at": row[16],
            }


def progress_generated_quest(user_id: int, quest_id: str, progress_amount: int = 1) -> bool:
    """
    Update progress on an active generated quest.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT progress, target, is_completed, is_redeemed, expires_at
                FROM generated_quests
                WHERE user_id = %s AND quest_id = %s
                """,
                (user_id, quest_id),
            )
            row = cur.fetchone()
            if not row:
                return False
            
            progress, target, is_completed, is_redeemed, expires_at = row
            
            # Check if quest is still valid
            if is_redeemed or expires_at <= datetime.utcnow():
                return False
            
            # Update progress
            new_progress = min(progress + progress_amount, target)
            new_completed = new_progress >= target
            
            cur.execute(
                """
                UPDATE generated_quests
                SET progress = %s, is_completed = %s
                WHERE user_id = %s AND quest_id = %s
                """,
                (new_progress, new_completed, user_id, quest_id),
            )
            
            return True


def redeem_generated_quest(user_id: int, quest_id: str) -> bool:
    """
    Redeem a completed generated quest and award the player.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT progress, target, is_completed, is_redeemed,
                       reward_coins, reward_tickets, expires_at
                FROM generated_quests
                WHERE user_id = %s AND quest_id = %s
                """,
                (user_id, quest_id),
            )
            row = cur.fetchone()
            if not row:
                return False
            
            progress, target, is_completed, is_redeemed, reward_coins, reward_tickets, expires_at = row
            
            # Check if quest can be redeemed
            if is_redeemed or not is_completed or expires_at <= datetime.utcnow():
                return False
            
            # Award the player
            cur.execute(
                """
                UPDATE players
                SET coins = coins + %s, dirty_tickets = dirty_tickets + %s
                WHERE user_id = %s
                """,
                (reward_coins, reward_tickets, user_id),
            )
            
            # Mark quest as redeemed
            cur.execute(
                """
                UPDATE generated_quests
                SET is_redeemed = TRUE
                WHERE user_id = %s AND quest_id = %s
                """,
                (user_id, quest_id),
            )
            
            return True


def get_player_quest_history(user_id: int, limit: int = 10) -> list[dict]:
    """
    Get the player's recent quest history for display.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT quest_id, name, template_id, difficulty,
                       is_completed, is_redeemed, generated_at
                FROM generated_quests
                WHERE user_id = %s
                ORDER BY generated_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return [
                {
                    "quest_id": row[0],
                    "name": row[1],
                    "template_id": row[2],
                    "difficulty": row[3],
                    "is_completed": row[4],
                    "is_redeemed": row[5],
                    "generated_at": row[6],
                }
                for row in cur.fetchall()
            ]


# ==================== PAWN REQUEST SYSTEM ====================

def store_pawn_request(user_id: int, request_data: dict) -> bool:
    """
    Store a new pawn request for a player.
    Only one active request per player.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Clear any previous pending requests
            cur.execute(
                """
                DELETE FROM pawn_requests
                WHERE user_id = %s AND status = 'pending_choice'
                """,
                (user_id,),
            )
            
            # Insert new request
            cur.execute(
                """
                INSERT INTO pawn_requests (
                    user_id, request_id, item_name, flavor,
                    reward_coins, reward_tickets, reward_exclusive,
                    difficulty, status, deadline
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    request_data.get("request_id"),
                    request_data.get("item_name"),
                    request_data.get("flavor"),
                    request_data.get("reward_coins"),
                    request_data.get("reward_tickets"),
                    request_data.get("reward_exclusive"),
                    request_data.get("difficulty"),
                    "pending_choice",
                    request_data.get("deadline"),
                ),
            )
            
            return True


def get_active_pawn_request(user_id: int) -> dict | None:
    """
    Get the player's active pawn request (non-completed).
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, request_id, item_name, flavor,
                       reward_coins, reward_tickets, reward_exclusive,
                       difficulty, status, deadline, created_at
                FROM pawn_requests
                WHERE user_id = %s AND status IN ('pending_choice', 'active')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": row[0],
                "request_id": row[1],
                "item_name": row[2],
                "flavor": row[3],
                "reward_coins": row[4],
                "reward_tickets": row[5],
                "reward_exclusive": row[6],
                "difficulty": row[7],
                "status": row[8],
                "deadline": row[9],
                "created_at": row[10],
            }


def update_pawn_request_status(user_id: int, request_id: int, new_status: str) -> bool:
    """
    Update the status of a pawn request.
    Statuses: pending_choice -> active -> completed/failed
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pawn_requests
                SET status = %s, updated_at = NOW()
                WHERE user_id = %s AND id = %s
                RETURNING id
                """,
                (new_status, user_id, request_id),
            )
            
            return cur.fetchone() is not None


def complete_pawn_request(user_id: int, request_id: int, reward_coins: int, reward_tickets: int, exclusive_item: str = None) -> bool:
    """
    Complete a pawn request and award the player.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Mark request as completed
            cur.execute(
                """
                UPDATE pawn_requests
                SET status = 'completed', updated_at = NOW()
                WHERE user_id = %s AND id = %s
                RETURNING id
                """,
                (user_id, request_id),
            )
            
            if not cur.fetchone():
                return False
            
            # Award player
            cur.execute(
                """
                UPDATE players
                SET coins = coins + %s, dirty_tickets = dirty_tickets + %s
                WHERE user_id = %s
                """,
                (reward_coins, reward_tickets, user_id),
            )
            
            # If there's an exclusive reward item, add to inventory
            if exclusive_item:
                cur.execute(
                    """
                    INSERT INTO inventory (user_id, item_id, quantity)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (user_id, item_id)
                    DO UPDATE SET quantity = inventory.quantity + 1
                    """,
                    (user_id, exclusive_item),
                )
            
            return True


def fail_pawn_request(user_id: int, request_id: int) -> bool:
    """
    Fail a pawn request.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pawn_requests
                SET status = 'failed', updated_at = NOW()
                WHERE user_id = %s AND id = %s
                RETURNING id
                """,
                (user_id, request_id),
            )
            
            return cur.fetchone() is not None

