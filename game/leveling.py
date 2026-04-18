def xp_to_next_level(level: int) -> int:
    return 50 + (level * 25) + (level * level * 5)


def apply_xp(current_xp: int, current_level: int, gained_xp: int) -> tuple[int, int, bool]:
    xp = current_xp + gained_xp
    level = current_level
    leveled_up = False

    while xp >= xp_to_next_level(level):
        xp -= xp_to_next_level(level)
        level += 1
        leveled_up = True

    return xp, level, leveled_up
