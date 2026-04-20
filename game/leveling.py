def xp_to_next_level(level: int) -> int:
    """
    Calculate XP required to reach the next level.
    
    Formula: 50 * (level ^ 1.5)
    - Early levels are fast (10→50 xp needed for levels 1-5)
    - Later levels take longer (level 100 needs ~50,000 xp)
    - No hard level cap, supports infinite progression
    """
    return int(50 * (level ** 1.5))



def apply_xp(current_xp: int, current_level: int, gained_xp: int) -> tuple[int, int, bool]:
    xp = current_xp + gained_xp
    level = current_level
    leveled_up = False

    while xp >= xp_to_next_level(level):
        xp -= xp_to_next_level(level)
        level += 1
        leveled_up = True

    return xp, level, leveled_up
