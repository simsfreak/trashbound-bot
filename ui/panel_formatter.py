"""
NEON WASTES PANEL FORMATTER

Renders Discord embeds in standardized panel format.
Supports all 4 layout modes (DASHBOARD, LIST, EVENT, COMBAT).
"""

from typing import Optional, List, Tuple
from game.icons import get_icon, format_status_bar


class PanelFormatter:
    """
    Renders game screens in consistent terminal-style panel format.
    
    All screens follow this structure:
    ╔══════════════ TITLE ══════════════╗
    <description/context>
    <SECTION HEADER>
    <line>
    <line>
    <optional footer>
    ╚═══════════════════════════════════╝
    """
    
    # Box drawing characters
    CORNER_TL = "╔"
    CORNER_TR = "╗"
    CORNER_BL = "╚"
    CORNER_BR = "╝"
    LINE_H = "═"
    LINE_V = "║"
    
    def __init__(self, width: int = 50):
        """
        Initialize formatter.
        
        Args:
            width: Total panel width (including borders)
        """
        self.width = width
        self.content_width = width - 4  # Space for borders and padding
    
    # ══════════════════════════════════════════════════════════════════════════
    # UTILITY: Text padding and alignment
    # ══════════════════════════════════════════════════════════════════════════
    
    def _strip_emoji(self, text: str) -> int:
        """
        Calculate display length of text (emoji-safe).
        Emojis are typically 2 chars wide but display as 1.
        """
        # Simple heuristic: count visible characters
        return len(text)
    
    def _pad_line(self, text: str, align: str = "left") -> str:
        """
        Pad text to content width.
        
        Args:
            text: Text to pad
            align: "left", "center", or "right"
        
        Returns:
            Padded text
        """
        display_len = self._strip_emoji(text)
        
        if display_len >= self.content_width:
            return text[:self.content_width]
        
        padding = self.content_width - display_len
        
        if align == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            return " " * left_pad + text + " " * right_pad
        elif align == "right":
            return " " * padding + text
        else:  # left
            return text + " " * padding
    
    # ══════════════════════════════════════════════════════════════════════════
    # CORE PANEL COMPONENTS
    # ══════════════════════════════════════════════════════════════════════════
    
    def header(self, title: str) -> str:
        """
        Create panel header line.
        
        Usage:
            header("PROFILE")  → "╔══════════════ PROFILE ══════════════╗"
        """
        title_text = f" {title} "
        remaining = self.width - 4 - len(title_text)
        left_dashes = remaining // 2
        right_dashes = remaining - left_dashes
        
        return (
            f"{self.CORNER_TL}"
            f"{self.LINE_H * left_dashes}"
            f"{title_text}"
            f"{self.LINE_H * right_dashes}"
            f"{self.CORNER_TR}"
        )
    
    def footer(self) -> str:
        """Create panel footer line."""
        return (
            f"{self.CORNER_BL}"
            f"{self.LINE_H * (self.width - 2)}"
            f"{self.CORNER_BR}"
        )
    
    def section_header(self, emoji: str, label: str) -> str:
        """
        Create section header within panel.
        
        Usage:
            section_header("📊", "STATS")  → "║ 📊 STATS"
        """
        text = f" {emoji} {label.upper()}"
        padded = self._pad_line(text, align="left")
        return f"{self.LINE_V} {padded} {self.LINE_V}"
    
    def line(self, text: str = "", align: str = "left") -> str:
        """
        Create a content line within panel.
        
        Usage:
            line("Health: 80/100")  → "║ Health: 80/100                        ║"
        """
        padded = self._pad_line(text, align=align)
        return f"{self.LINE_V} {padded} {self.LINE_V}"
    
    def blank_line(self) -> str:
        """Create an empty line for spacing."""
        return self.line("")
    
    # ══════════════════════════════════════════════════════════════════════════
    # STANDARDIZED LINE FORMATS (6 types from spec)
    # ══════════════════════════════════════════════════════════════════════════
    
    def format_status_bar_line(
        self,
        label: str,
        current: int,
        max_val: int,
        bar_size: int = 10
    ) -> str:
        """
        Format 6.1: STATUS BAR FORMAT
        
        Example:
            "❤️ Health      [████████░░] 80%"
        
        Usage:
            format_status_bar_line("Health", 80, 100)
        """
        if max_val <= 0:
            percentage = 0
            filled = 0
        else:
            percentage = int((current / max_val) * 100)
            filled = int((current / max_val) * bar_size)
            filled = max(0, min(bar_size, filled))
        
        empty = bar_size - filled
        bar = "█" * filled + "░" * empty
        
        icon = get_icon(label.lower(), "✨")
        text = f"{icon} {label:10} [{bar}] {percentage}%"
        
        return self.line(text)
    
    def format_stat_line(
        self,
        stat1: Tuple[str, int],
        stat2: Tuple[str, int],
        stat3: Optional[Tuple[str, int]] = None
    ) -> str:
        """
        Format 6.2: STAT LINE FORMAT
        
        Example:
            "[💪] STR 8   [🏃] AGI 11   [🧠] INT 6"
        
        Usage:
            format_stat_line(("STR", 8), ("AGI", 11), ("INT", 6))
        """
        from game.icons import STAT_SHORT
        
        def format_stat(name: str, value: int) -> str:
            if name.upper() in STAT_SHORT:
                icon = STAT_SHORT[name.upper()]
                short = name.upper()
            else:
                icon = get_icon(name, "✨")
                short = name.upper()
            return f"[{icon}] {short} {value}"
        
        text = f"{format_stat(stat1[0], stat1[1])}   {format_stat(stat2[0], stat2[1])}"
        if stat3:
            text += f"   {format_stat(stat3[0], stat3[1])}"
        
        return self.line(text)
    
    def format_item_line(
        self,
        item_emoji: str,
        item_name: str,
        primary_stat: str,
        secondary_effect: Optional[str] = None,
        status_icon: Optional[str] = None,
        status_text: Optional[str] = None
    ) -> str:
        """
        Format 6.3: ITEM LINE FORMAT
        
        Example:
            "[🧪] Signal Shard      +12% Rare Loot      ☢️ +3 Rad"
        
        Usage:
            format_item_line("🧪", "Signal Shard", "+12% Rare Loot", status_icon="☢️", status_text="+3 Rad")
        """
        text = f"[{item_emoji}] {item_name:16} {primary_stat}"
        if status_icon and status_text:
            text += f"      {status_icon} {status_text}"
        elif secondary_effect:
            text += f"      {secondary_effect}"
        
        return self.line(text)
    
    def format_shop_line(
        self,
        item_emoji: str,
        item_name: str,
        sell_price: int,
        buy_price: int,
        trend_icon: str = "📉",
        trend_text: str = "Stable"
    ) -> str:
        """
        Format 6.4: SHOP / MARKET LINE FORMAT
        
        Example:
            "[🥫] Food Ration       Sell 6   Buy 10     📉 Falling"
        
        Usage:
            format_shop_line("🥫", "Food Ration", 6, 10, "📉", "Falling")
        """
        text = (
            f"[{item_emoji}] {item_name:17} "
            f"Sell {sell_price}   Buy {buy_price}     "
            f"{trend_icon} {trend_text}"
        )
        return self.line(text)
    
    def format_contract_line(
        self,
        contract_emoji: str,
        contract_name: str,
        objective: str,
        coin_reward: int,
        xp_reward: int
    ) -> str:
        """
        Format 6.5: CONTRACT LINE FORMAT
        
        Example:
            "[⚔️] Hunt Order        Kill 3 Targets      💰 40   ✨ 60 XP"
        
        Usage:
            format_contract_line("⚔️", "Hunt Order", "Kill 3 Targets", 40, 60)
        """
        text = (
            f"[{contract_emoji}] {contract_name:17} "
            f"{objective:20} "
            f"💰 {coin_reward}   ✨ {xp_reward} XP"
        )
        return self.line(text)
    
    def format_zone_line(
        self,
        zone_emoji: str,
        zone_name: str,
        resources: str,
        risk_level: str
    ) -> str:
        """
        Format 6.6: ZONE LINE FORMAT
        
        Example:
            "[🏪] Ruined Market     🍖 Food / 💧 Water   ⚠️ Low Risk"
        
        Usage:
            format_zone_line("🏪", "Ruined Market", "🍖 Food / 💧 Water", "⚠️ Low Risk")
        """
        text = (
            f"[{zone_emoji}] {zone_name:15} "
            f"{resources:20} "
            f"{risk_level}"
        )
        return self.line(text)
    
    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT MODES (4 types)
    # ══════════════════════════════════════════════════════════════════════════
    
    def mode_a_dashboard(
        self,
        title: str,
        description: str,
        sections: List[Tuple[str, str, List[str]]],  # (emoji, label, lines)
        footer_text: Optional[str] = None
    ) -> str:
        """
        MODE A - DASHBOARD
        
        Used for: profile, shelter, crew, season
        
        Structure:
            ╔════════════╗
            description
            📊 SECTION
            line
            line
            footer
            ╚════════════╝
        
        Args:
            title: Panel title
            description: Brief context
            sections: List of (emoji, label, lines)
            footer_text: Optional footer
        
        Returns:
            Formatted panel string
        """
        lines = [self.header(title)]
        
        if description:
            lines.append(self.line(description))
            lines.append(self.blank_line())
        
        for section_emoji, section_label, content_lines in sections:
            lines.append(self.section_header(section_emoji, section_label))
            for content_line in content_lines:
                lines.append(self.line(content_line))
            lines.append(self.blank_line())
        
        if footer_text:
            lines.append(self.line(footer_text))
        
        lines.append(self.footer())
        
        return "\n".join(lines)
    
    def mode_b_list(
        self,
        title: str,
        category_label: str,
        items: List[str],
        page_info: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> str:
        """
        MODE B - LIST
        
        Used for: inventory, contracts, shop, market, recipes
        
        Structure:
            ╔════════════╝
            category
            [item]
            [item]
            [item]
            footer
            ╚════════════╝
        
        Args:
            title: Panel title
            category_label: Category or filter label
            items: List of formatted item lines
            page_info: Optional pagination info
            footer_text: Optional footer
        
        Returns:
            Formatted panel string
        """
        lines = [self.header(title)]
        
        if category_label:
            lines.append(self.line(category_label))
            lines.append(self.blank_line())
        
        if items:
            for item in items:
                lines.append(self.line(item))
        else:
            lines.append(self.line("(empty)"))
        
        lines.append(self.blank_line())
        
        if page_info:
            lines.append(self.line(page_info))
        
        if footer_text:
            lines.append(self.line(footer_text))
        
        lines.append(self.footer())
        
        return "\n".join(lines)
    
    def mode_c_event(
        self,
        title: str,
        flavor_text: str,
        risk_reward_lines: List[str]
    ) -> str:
        """
        MODE C - EVENT
        
        Used for: scavenging events, story choices, anomaly prompts
        
        Structure:
            ╔════════════╝
            flavor_text
            risk/reward
            ╚════════════╝
        
        Args:
            title: Event title
            flavor_text: Descriptive text
            risk_reward_lines: Risk/reward lines
        
        Returns:
            Formatted panel string
        """
        lines = [self.header(title)]
        lines.append(self.blank_line())
        
        # Flavor text block
        for text_line in flavor_text.split("\n"):
            lines.append(self.line(text_line))
        
        lines.append(self.blank_line())
        
        # Risk/reward section
        for reward_line in risk_reward_lines:
            lines.append(self.line(reward_line))
        
        lines.append(self.blank_line())
        lines.append(self.footer())
        
        return "\n".join(lines)
    
    def mode_d_combat(
        self,
        title: str,
        description: str,
        player_name: str,
        player_stats: List[str],
        enemy_name: str,
        enemy_stats: List[str]
    ) -> str:
        """
        MODE D - COMBAT
        
        Used for: encounters, turn updates
        
        Structure:
            ╔════════════╝
            description
            🧍 YOU
            stats
            👾 ENEMY
            stats
            ╚════════════╝
        
        Args:
            title: Combat title
            description: Context
            player_name: Player name
            player_stats: Player stat lines
            enemy_name: Enemy name
            enemy_stats: Enemy stat lines
        
        Returns:
            Formatted panel string
        """
        lines = [self.header(title)]
        lines.append(self.blank_line())
        
        if description:
            lines.append(self.line(description))
            lines.append(self.blank_line())
        
        # Player section
        lines.append(self.line(f"🧍 {player_name.upper()}"))
        for stat_line in player_stats:
            lines.append(self.line(stat_line))
        
        lines.append(self.blank_line())
        
        # Enemy section
        lines.append(self.line(f"👾 {enemy_name.upper()}"))
        for stat_line in enemy_stats:
            lines.append(self.line(stat_line))
        
        lines.append(self.blank_line())
        lines.append(self.footer())
        
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE INSTANCE
# ══════════════════════════════════════════════════════════════════════════════
formatter = PanelFormatter(width=50)


# ══════════════════════════════════════════════════════════════════════════════
# PRESET BUILDERS FOR COMMON SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

def build_error_panel(error_title: str, error_message: str, required: List[str], have: List[str]) -> str:
    """
    Build a standardized error panel.
    
    Example from spec:
        ╔════════════ ⚠️ ACTION FAILED ═══════════╗
        Not enough resources.
        Required:
        🔩 Scrap x5
        You have: x2
        ╚═══════════════════════════════════════════╝
    """
    panel = formatter
    lines = [panel.header(f"⚠️ {error_title}")]
    lines.append(panel.blank_line())
    lines.append(panel.line(error_message))
    lines.append(panel.blank_line())
    
    if required:
        lines.append(panel.line("REQUIRED:"))
        for req in required:
            lines.append(panel.line(req))
    
    if have:
        lines.append(panel.blank_line())
        lines.append(panel.line("YOU HAVE:"))
        for item in have:
            lines.append(panel.line(item))
    
    lines.append(panel.blank_line())
    lines.append(panel.footer())
    
    return "\n".join(lines)
