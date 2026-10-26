from __future__ import annotations

"""
Dragon Ball / Anime Crossover RPG — Combat Engine (Part 1)
==========================================================
This file handles the core battle simulation, including:
  - Turn-based combat logic
  - Damage, Critical Hit, and Dodge calculations
  - Elemental Weaknesses and Faction Synergies
  - Zenkai Boosts (Comeback mechanics)
  - Boss Enrage mechanics

PART 1 CONTAINS:
  - Combat Configuration & Constants
  - Math & Random Number Generation Utilities
  - The CombatEngine Class (Battle Simulation)
  - Detailed Battle Logging

PART 2 WILL CONTAIN:
  - CombatHistory Class (Logging to DB)
  - CombatAchievements Class (Milestone checks)
  - QuestTracker Class (Daily/Weekly progress)
  - Full Self-Test Suite
"""

import random
import math
from datetime import datetime, timezone
from typing import Optional, Any, Tuple, List, Dict

import db
import game_data as G


# =============================================================
# COMBAT CONFIGURATION & CONSTANTS
# =============================================================
# These constants define the core balancing of the entire game.
# Changing these numbers will drastically alter the difficulty.

# The absolute minimum damage a hit can deal. Prevents infinite loops.
MIN_DAMAGE: int = 1

# The maximum number of rounds a battle can last before it times out.
# If the player and enemy are too tanky, the battle ends in a draw.
MAX_ROUNDS_DEFAULT: int = 60

# When a Boss is below 50% HP, their damage is multiplied by this factor.
ENRAGE_MULTIPLIER: float = 1.3

# Zenkai is a comeback mechanic. If the player's HP drops below this
# percentage (20%), their attack power surges.
ZENKAI_THRESHOLD: float = 0.20

# The actual multiplier applied to the player's ATK during Zenkai.
ZENKAI_ATK_BOOST: float = 1.35

# Critical hits deal 160% damage.
CRIT_MULTIPLIER: float = 1.6

# The base chance for any character to dodge an attack (5%).
DODGE_BASE_CHANCE: float = 0.05

# For every 1 point of Speed above 20, the character gains +0.5% dodge chance.
DODGE_SPEED_FACTOR: float = 0.005

# The maximum possible dodge chance (35%). Prevents invincibility.
MAX_DODGE_CHANCE: float = 0.35

# Damage variance. A hit will randomly land between 80% and 135% of base ATK.
DAMAGE_SPREAD_PLAYER: Tuple[float, float] = (0.8, 1.35)
DAMAGE_SPREAD_ENEMY: Tuple[float, float] = (0.8, 1.25)


# =============================================================
# UTILITY & MATH FUNCTIONS
# =============================================================

def format_number(num: Any) -> str:
    """
    Formats large numbers into a readable string.
    Example: 1500 -> 1.5K, 2000000 -> 2.00M
    """
    if num is None:
        return "0"
    try:
        num = int(num)
    except (ValueError, TypeError):
        return str(num)
        
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num / 1_000:.2f}K"
    return f"{num:,}"


def get_hp_bar(current_hp: int, max_hp: int, length: int = 10) -> str:
    """
    Generates a visual progress bar for HP.
    Example: [🟩🟩🟩🟩🟩⬛⬛⬛⬛⬛] 50%
    """
    if max_hp <= 0:
        return "💀 DEAD"
        
    current_hp = max(0, min(current_hp, max_hp))
    pct = int((current_hp / max_hp) * 100)
    
    filled = int((pct / 100) * length)
    empty = length - filled
    
    bar = "🟩" * filled + "⬛" * empty
    return f"[{bar}] {format_number(current_hp)}/{format_number(max_hp)}"


def roll_damage(base_atk: int, spread: Tuple[float, float] = DAMAGE_SPREAD_PLAYER) -> int:
    """
    Rolls a random damage value around the base attack using a spread factor.
    Ensures the damage is never lower than MIN_DAMAGE.
    """
    lo, hi = spread
    multiplier = random.uniform(lo, hi)
    final_damage = int(base_atk * multiplier)
    return max(MIN_DAMAGE, final_damage)


def roll_crit(crit_chance: int) -> bool:
    """
    Determines if a critical hit lands.
    Rolls a random number between 1 and 100. If it's less than or equal
    to the crit_chance percentage, the hit is a critical.
    """
    chance = max(0, min(100, int(crit_chance)))
    return random.randint(1, 100) <= chance


def roll_dodge(speed: int) -> bool:
    """
    Determines if an afterimage dodge triggers based on the player's Speed.
    The faster the character, the higher the chance to dodge.
    """
    chance = DODGE_BASE_CHANCE + max(0, speed - 20) * DODGE_SPEED_FACTOR
    chance = min(MAX_DODGE_CHANCE, chance)
    return random.random() < chance


def get_elemental_multiplier(player_element: str, enemy_element: str) -> float:
    """
    Calculates the damage multiplier based on elemental advantages.
    - Strong vs: 1.5x Damage
    - Weak vs: 0.5x Damage
    - Neutral: 1.0x Damage
    """
    p_el = (player_element or "LIGHT").upper()
    e_el = (enemy_element or "DARK").upper()
    
    # Ensure the elements actually exist in our game data
    if p_el not in G.ELEMENTS or e_el not in G.ELEMENTS:
        return 1.0
        
    # Check if the player's element is strong against the enemy
    if e_el in G.ELEMENTS[p_el]["strong_against"]:
        return 1.5
        
    # Check if the player's element is weak against the enemy
    if p_el in G.ELEMENTS[e_el]["strong_against"]:
        return 0.5
        
    return 1.0


def calculate_power_level(stats: Dict[str, int]) -> int:
    """
    Calculates a Scouter-style Power Level based on the player's stats.
    This creates massive, satisfying numbers that reflect the anime lore.
    """
    hp = int(stats.get("hp", 0) or 0)
    atk = int(stats.get("atk", 0) or 0)
    spd = int(stats.get("spd", 10) or 10)
    crit = int(stats.get("crit", 5) or 5)
    
    # Weighted formula: ATK and Speed contribute the most to Power Level
    power_level = hp + (atk * 10) + (spd * 50) + (crit * 100)
    return power_level


# =============================================================
# THE COMBAT ENGINE
# =============================================================
class CombatEngine:
    """
    The core turn-based battle simulator.
    This class is instantiated for every single battle in the game.
    
    It handles:
    - Turn order (based on Speed)
    - Player attacks (with Crits, Elemental Advantage, and Zenkai)
    - Enemy attacks (with Dodges, Crits, and Enrage)
    - Battle Logging
    """

    def __init__(
        self,
        player_atk: int,
        player_hp: int,
        crit: int = 5,
        speed: int = 10,
        player_element: str = "LIGHT",
        enemy_element: str = "DARK",
        enable_dodge: bool = True,
        enable_zenkai: bool = True,
        max_rounds: int = MAX_ROUNDS_DEFAULT,
    ):
        """
        Initializes the battle state with the player's stats.
        """
        # Player Stats (Sanitized to prevent crashes from bad data)
        self.p_atk = max(1, int(player_atk))
        self.p_hp = max(1, int(player_hp))
        self.max_hp = self.p_hp
        self.crit = max(0, int(crit))
        self.speed = max(1, int(speed))
        
        # Elements
        self.p_element = player_element or "LIGHT"
        self.e_element = enemy_element or "DARK"
        
        # Feature Flags (can be toggled for specific bosses)
        self.enable_dodge = enable_dodge
        self.enable_zenkai = enable_zenkai
        self.max_rounds = max(1, int(max_rounds))

        # Battle Statistics (Tracked for Post-Battle Rewards)
        self.damage_dealt = 0
        self.damage_taken = 0
        self.rounds = 0
        self.crits_landed = 0
        self.dodges_triggered = 0
        self.zenkai_activations = 0
        
        # Battle Log (List of strings)
        self.log: List[str] = []
        
        # Enemy Info (Set during fight())
        self._enemy_name = "Enemy"
        self._enemy_max_hp = 0
        self._enemy_el_mult = 1.0

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------
    def _log(self, text: str) -> None:
        """Appends a message to the battle log."""
        self.log.append(text)

    def _is_zenkai_active(self, current_hp: int) -> bool:
        """Checks if the Zenkai boost should be active."""
        if not self.enable_zenkai:
            return False
        return current_hp <= int(self.max_hp * ZENKAI_THRESHOLD)

    def _apply_zenkai(self, base_atk: int, current_hp: int) -> int:
        """Returns the boosted ATK if Zenkai is active."""
        if self._is_zenkai_active(current_hp):
            return int(base_atk * ZENKAI_ATK_BOOST)
        return base_atk

    def _resolve_player_attack(self, enemy_hp: int, current_hp: int) -> int:
        """
        Handles the player's turn.
        Returns the enemy's new HP.
        """
        current_atk = self.p_atk
        
        # 1. Check Zenkai Activation
        if self._is_zenkai_active(current_hp):
            if self.zenkai_activations == 0:
                self.zenkai_activations += 1
                self._log("🔥 **ZENKAI BOOST ACTIVATED!** Your ATK surges by 35%!")
            current_atk = self._apply_zenkai(current_atk, current_hp)
            
        # 2. Apply Elemental Multiplier
        current_atk = int(current_atk * self._enemy_el_mult)
        
        # 3. Roll Damage & Crit
        hit = roll_damage(current_atk, DAMAGE_SPREAD_PLAYER)
        is_crit = roll_crit(self.crit)
        
        if is_crit:
            hit = int(hit * CRIT_MULTIPLIER)
            self.crits_landed += 1
            
        # 4. Apply Damage
        enemy_hp -= hit
        self.damage_dealt += hit
        
        # 5. Log the Attack
        crit_text = "🔥 CRITICAL HIT!" if is_crit else ""
        self._log(
            f"Round {self.rounds}: You struck {self._enemy_name} for **{format_number(hit)}** damage! {crit_text} "
            f"[Enemy HP: {format_number(max(0, enemy_hp))}]"
        )
        
        return enemy_hp

    def _resolve_enemy_attack(self, player_hp: int, enemy_dmg: int, is_enraged: bool) -> int:
        """
        Handles the enemy's turn.
        Returns the player's new HP.
        """
        # 1. Check Dodge (Player dodges enemy)
        if self.enable_dodge and roll_dodge(self.speed):
            self.dodges_triggered += 1
            self._log(f"Round {self.rounds}: You used **Afterimage** and dodged {self._enemy_name}'s attack!")
            return player_hp

        # 2. Apply Enrage (Boss mechanic)
        current_dmg = enemy_dmg
        if is_enraged:
            current_dmg = int(current_dmg * ENRAGE_MULTIPLIER)
            
        # 3. Roll Damage & Crit
        taken = roll_damage(current_dmg, DAMAGE_SPREAD_ENEMY)
        # Enemies have a flat 5% crit chance
        is_crit = roll_crit(5) 
        
        if is_crit:
            taken = int(taken * CRIT_MULTIPLIER)
            
        # 4. Apply Damage
        player_hp -= taken
        self.damage_taken += taken
        
        # 5. Log the Attack
        crit_text = "🔥 CRITICAL!" if is_crit else ""
        enrage_text = "😡 (Enraged)" if is_enraged else ""
        self._log(
            f"Round {self.rounds}: {self._enemy_name} hit you for **{format_number(taken)}** damage! {crit_text} {enrage_text} "
            f"[Your HP: {format_number(max(0, player_hp))}]"
        )
        
        return player_hp

    # ---------------------------------------------------------
    # MAIN FIGHT METHOD
    # ---------------------------------------------------------
    def fight(
        self,
        enemy_name: str,
        enemy_hp: int,
        enemy_dmg: int,
        enrage: bool = False,
    ) -> Tuple[bool, int, List[str]]:
        """
        Simulates the entire battle.
        
        Args:
            enemy_name: Name of the enemy (for logging)
            enemy_hp: Starting HP of the enemy
            enemy_dmg: Base damage of the enemy
            enrage: Whether the enemy has boss enrage mechanics
            
        Returns:
            Tuple containing:
            - bool: True if player won, False if player lost
            - int: Player's remaining HP
            - List[str]: The battle log
        """
        # Setup
        self._enemy_name = enemy_name
        self._enemy_max_hp = int(enemy_hp)
        p_hp = self.p_hp
        e_hp = int(enemy_hp)
        
        if e_hp <= 0:
            return True, p_hp, ["The enemy was already defeated."]

        # Check Elemental Advantage
        self._enemy_el_mult = get_elemental_multiplier(self.p_element, self.e_element)
        if self._enemy_el_mult > 1.0:
            self._log(f"⚡ **Elemental Advantage!** Your {self.p_element} attacks deal 50% more damage!")
        elif self._enemy_el_mult < 1.0:
            self._log(f"⚠️ **Elemental Weakness!** Your {self.p_element} attacks deal 50% less damage!")

        self._log(f"⚔️ **Battle Started:** You vs {enemy_name}!")
        self._log(f"❤️ Enemy HP: {format_number(e_hp)}")

        # Round Loop
        for rnd in range(1, self.max_rounds + 1):
            self.rounds = rnd
            
            # Determine Turn Order
            # If Speed > 30, player always goes first.
            # Otherwise, it's a 50/50 coin flip.
            player_first = self.speed > 30 or random.random() < 0.5

            if player_first:
                # Player attacks
                e_hp = self._resolve_player_attack(e_hp, p_hp)
                if e_hp <= 0:
                    self._log(f"🏆 **VICTORY!** You defeated {enemy_name}!")
                    return True, max(1, p_hp), self.log
                    
                # Enemy attacks
                p_hp = self._resolve_enemy_attack(p_hp, enemy_dmg, enrage)
                if p_hp <= 0:
                    self._log(f"❌ **DEFEAT!** You were defeated by {enemy_name}.")
                    return False, 0, self.log
            else:
                # Enemy attacks
                p_hp = self._resolve_enemy_attack(p_hp, enemy_dmg, enrage)
                if p_hp <= 0:
                    self._log(f"❌ **DEFEAT!** You were defeated by {enemy_name}.")
                    return False, 0, self.log
                    
                # Player attacks
                e_hp = self._resolve_player_attack(e_hp, p_hp)
                if e_hp <= 0:
                    self._log(f"🏆 **VICTORY!** You defeated {enemy_name}!")
                    return True, max(1, p_hp), self.log

        # If the battle exceeds max rounds
        self._log("⏱️ **Time Out!** The battle dragged on for too long.")
        return False, max(1, p_hp), self.log

    # ---------------------------------------------------------
    # ANALYSIS HELPERS
    # ---------------------------------------------------------
    def get_summary(self, won: bool, left_hp: int) -> str:
        """Returns a nicely formatted summary of the battle."""
        return (
            f"{'✅ Victory' if won else '❌ Defeat'}\n"
            f"⏱️ Rounds: {self.rounds}\n"
            f"⚔️ Damage Dealt: {format_number(self.damage_dealt)}\n"
            f"🩸 Damage Taken: {format_number(self.damage_taken)}\n"
            f"🔥 Crits Landed: {self.crits_landed}\n"
            f"💨 Dodges: {self.dodges_triggered}\n"
            f"❤️ HP Left: {format_number(max(0, left_hp))}/{format_number(self.max_hp)}"
        )

# =============================================================
# END OF PART 1
# =============================================================
# Part 2 will contain:
# - CombatHistory Class (Database Logging)
# - CombatAchievements Class (Milestone checks)
# - QuestTracker Class (Daily/Weekly progress)
# - Full Self-Test Suite
# =============================================================
# =============================================================
# PART 2: HISTORY, ACHIEVEMENTS, QUESTS & TEST SUITE
# =============================================================

# =============================================================
# COMBAT HISTORY MANAGER
# =============================================================
class CombatHistory:
    """
    Manages, retrieves, and formats the player's combat history.
    This class acts as the bridge between the raw SQLite database
    and the beautiful UI displayed in Telegram.
    """

    def __init__(self, uid: int, limit: int = 10):
        """
        Initializes the History Manager for a specific player.
        
        Args:
            uid (int): The Telegram user ID of the player.
            limit (int): The default number of recent battles to fetch.
        """
        self.uid = int(uid)
        self.limit = max(1, min(int(limit), 50))  # Clamp between 1 and 50

    # ---------------------------------------------------------
    # DATABASE INTERACTIONS
    # ---------------------------------------------------------
    def log(
        self,
        enemy_name: str,
        enemy_max_hp: int,
        damage_dealt: int,
        damage_taken: int,
        outcome: str,
        rounds: int,
        rewards_text: str = "",
    ) -> None:
        """
        Saves a completed battle to the database.
        
        Args:
            enemy_name (str): The name of the defeated (or defeating) enemy.
            enemy_max_hp (int): The starting HP of the enemy.
            damage_dealt (int): Total damage the player dealt.
            damage_taken (int): Total damage the player received.
            outcome (str): Either 'victory' or 'defeat'.
            rounds (int): How many rounds the battle lasted.
            rewards_text (str): A short string describing loot (e.g., "50k Yens").
        """
        # Sanitize outcome to prevent DB pollution
        safe_outcome = "victory" if outcome.lower() == "victory" else "defeat"
        
        try:
            db.add_combat_log(
                uid=self.uid,
                enemy_name=enemy_name,
                enemy_max_hp=enemy_max_hp,
                damage_dealt=max(0, damage_dealt),
                damage_taken=max(0, damage_taken),
                outcome=safe_outcome,
                rounds=max(1, rounds),
                rewards_text=rewards_text[:100],  # Truncate to prevent DB bloat
            )
        except Exception as e:
            print(f"⚠️ Error saving combat log: {e}")

    def get_recent_battles(self, custom_limit: Optional[int] = None) -> List[Any]:
        """
        Fetches the most recent battles from the database.
        
        Args:
            custom_limit (Optional[int]): Override the default limit.
            
        Returns:
            List[sqlite3.Row]: A list of database rows.
        """
        fetch_limit = custom_limit if custom_limit is not None else self.limit
        try:
            return db.get_combat_history(self.uid, fetch_limit)
        except Exception as e:
            print(f"⚠️ Error fetching combat history: {e}")
            return []

    def get_lifetime_stats(self) -> Dict[str, int]:
        """
        Fetches the player's cumulative combat statistics.
        
        Returns:
            Dict[str, int]: A dictionary containing battles, wins, losses, etc.
        """
        try:
            return db.combat_stats(self.uid)
        except Exception as e:
            print(f"⚠️ Error fetching combat stats: {e}")
            return {"battles": 0, "wins": 0, "losses": 0, "dealt": 0, "taken": 0}

    # ---------------------------------------------------------
    # ANALYSIS & CALCULATIONS
    # ---------------------------------------------------------
    def calculate_win_streak(self) -> int:
        """
        Calculates the player's current consecutive win streak
        based on their most recent battles.
        """
        recent = self.get_recent_battles(20)  # Check last 20
        streak = 0
        for row in recent:
            if row["outcome"] == "victory":
                streak += 1
            else:
                break # Streak broken
        return streak

    def calculate_damage_per_round(self, limit: int = 10) -> float:
        """
        Calculates the average damage the player deals per round.
        Useful for advanced player analytics.
        """
        recent = self.get_recent_battles(limit)
        if not recent:
            return 0.0
            
        total_dmg = 0
        total_rounds = 0
        for row in recent:
            total_dmg += row["damage_dealt"]
            total_rounds += row["rounds"]
            
        if total_rounds == 0:
            return 0.0
            
        return round(total_dmg / total_rounds, 2)

    def get_best_fight(self) -> Optional[Any]:
        """Returns the battle where the player dealt the most damage."""
        recent = self.get_recent_battles(50)
        if not recent:
            return None
        return max(recent, key=lambda r: r["damage_dealt"])

    def get_worst_fight(self) -> Optional[Any]:
        """Returns the battle where the player took the most damage."""
        recent = self.get_recent_battles(50)
        if not recent:
            return None
        return max(recent, key=lambda r: r["damage_taken"])

    def get_longest_fight(self) -> Optional[Any]:
        """Returns the battle with the highest number of rounds."""
        recent = self.get_recent_battles(50)
        if not recent:
            return None
        return max(recent, key=lambda r: r["rounds"])

    # ---------------------------------------------------------
    # UI RENDERING HELPERS
    # ---------------------------------------------------------
    def _get_outcome_emoji(self, outcome: str) -> str:
        """Returns an emoji based on the battle outcome."""
        return "🏆" if outcome == "victory" else "💀"

    def _format_rewards(self, rewards_text: str) -> str:
        """Formats the rewards string for display."""
        if not rewards_text:
            return ""
        return f"\n      🎁 **Drops:** {rewards_text}"

    def render_history(self, title: str = "📜 **Combat History**") -> str:
        """
        Renders the player's last 10 battles as a beautifully formatted string.
        """
        recent = self.get_recent_battles()
        stats = self.get_lifetime_stats()
        
        if not recent:
            return (
                f"{title}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"*You have not fought any battles yet.*\n\n"
                f"Use `/explore` to find enemies and start fighting!"
            )
            
        lines = [f"{title}", "━━━━━━━━━━━━━━━━━━", ""]
        
        # 1. Loop through the battles
        for idx, row in enumerate(recent, 1):
            emoji = self._get_outcome_emoji(row["outcome"])
            enemy = row["enemy_name"]
            dealt = format_number(row["damage_dealt"])
            taken = format_number(row["damage_taken"])
            rounds = row["rounds"]
            
            lines.append(f"**{idx}.** {emoji} vs **{enemy}**")
            lines.append(f"      ⚔️ {dealt} Dealt | 🩸 {taken} Taken")
            lines.append(f"      🔄 {rounds} Rounds")
            
            reward_str = self._format_rewards(row["rewards_text"])
            if reward_str:
                lines.append(reward_str)
                
            lines.append("")  # Blank line between fights

        # 2. Add Lifetime Stats at the bottom
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("📊 **Lifetime Record:**")
        lines.append(f"⚔️ Battles: {stats['battles']} ({stats['wins']}W / {stats['losses']}L)")
        lines.append(f"🩸 Damage Dealt: {format_number(stats['dealt'])}")
        lines.append(f"🩹 Damage Taken: {format_number(stats['taken'])}")
        
        win_rate = 0
        if stats["battles"] > 0:
            win_rate = int((stats["wins"] / stats["battles"]) * 100)
        lines.append(f"📈 Win Rate: {win_rate}%")
        
        # 3. Add Win Streak
        streak = self.calculate_win_streak()
        if streak > 1:
            lines.append(f"🔥 **Current Win Streak:** {streak}")
            
        # 4. Add Best Fight highlight
        best = self.get_best_fight()
        if best and best["damage_dealt"] > 0:
            lines.append(f"💥 **Highest Damage:** {format_number(best['damage_dealt'])} vs {best['enemy_name']}")
            
        return "\n".join(lines)


# =============================================================
# COMBAT ACHIEVEMENTS
# =============================================================
class CombatAchievements:
    """
    Handles unlocking achievements based on player milestones.
    This class checks the DB for new milestones and grants rewards.
    """

    def __init__(self, uid: int):
        self.uid = int(uid)
        self.newly_unlocked: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # CORE UNLOCK LOGIC
    # ---------------------------------------------------------
    def _attempt_unlock(self, code: str) -> bool:
        """
        Attempts to unlock an achievement.
        If successful, adds it to the `newly_unlocked` list.
        """
        if code not in G.ACHIEVEMENTS:
            return False
            
        try:
            # db.unlock_achievement returns the info dict if newly unlocked, None if already owned
            info = db.unlock_achievement(self.uid, code)
            if info:
                self.newly_unlocked.append(info)
                return True
        except Exception as e:
            print(f"⚠️ Error unlocking achievement {code}: {e}")
            
        return False

    # ---------------------------------------------------------
    # SPECIFIC MILESTONE CHECKS
    # ---------------------------------------------------------
    def check_combat_milestones(self, battles: int, wins: int) -> None:
        """Checks achievements related to number of battles."""
        if battles >= 1: self._attempt_unlock("first_blood")
        if battles >= 10: self._attempt_unlock("battle_10")
        if battles >= 50: self._attempt_unlock("battle_50")
        if battles >= 100: self._attempt_unlock("battle_100")
        if battles >= 500: self._attempt_unlock("battle_500")
        if wins >= 100: self._attempt_unlock("explore_vet")

    def check_wealth_milestones(self, yens: int, gems: int) -> None:
        """Checks achievements related to wealth."""
        if yens >= 1_000_000: self._attempt_unlock("rich")
        if gems >= 1_000: self._attempt_unlock("gem_hoarder")

    def check_progression_milestones(self, rank: int, travel: str) -> None:
        """Checks achievements related to rank and travel."""
        if rank >= 5: self._attempt_unlock("rank_5")
        if rank >= 10: self._attempt_unlock("rank_10")
        if travel == "Omniverse": self._attempt_unlock("traveler")
        if travel == "Anime Multiverse": self._attempt_unlock("anime_weeb")

    def check_dragon_balls(self) -> None:
        """Checks if the player has collected all 7 dragon balls."""
        have = db.dragon_balls(self.uid)
        if all(have.get(s, 0) >= 1 for s in G.DRAGON_BALL_STARS):
            self._attempt_unlock("dragon_collector")

    def check_character_pull(self, rarity: str) -> None:
        """Checks if the player pulled a high-rarity character."""
        if rarity == "mythical": self._attempt_unlock("mythical_owner")
        elif rarity == "omni": self._attempt_unlock("omni_owner")

    def check_clan_founder(self, is_leader: bool) -> None:
        """Checks if the player created a clan."""
        self._attempt_unlock("clan_founder")
        if is_leader:
            self._attempt_unlock("clan_leader")

    def check_raid_cleared(self) -> None:
        """Called when the World Raid boss is defeated."""
        self._attempt_unlock("raid_warrior")

    def check_clan_raid_cleared(self) -> None:
        """Called when a Clan Raid boss is defeated."""
        self._attempt_unlock("clan_raid_clear")

    # ---------------------------------------------------------
    # POST-BATTLE WRAPPER
    # ---------------------------------------------------------
    def run_all_battle_checks(self, won: bool, damage_taken: int, is_boss: bool = False, is_summon: bool = False) -> None:
        """
        A convenience method to run all relevant checks after a battle ends.
        Called directly by bot.py.
        """
        stats = db.combat_stats(self.uid)
        
        if won:
            self.check_combat_milestones(stats["battles"], stats["wins"])
            
            if damage_taken == 0:
                self._attempt_unlock("flawless")
            if is_boss:
                self._attempt_unlock("boss_slayer")
            if is_summon:
                self._attempt_unlock("summon_hunter")
                
        p = db.player(self.uid)
        if p:
            self.check_wealth_milestones(p["yens"], p["gems"])
            self.check_progression_milestones(int(p["rank"] or 1), p["travel"] or "Earth")
            if p["fusion_count"]:
                self._attempt_unlock("fusion_master")

    # ---------------------------------------------------------
    # UI RENDERING
    # ---------------------------------------------------------
    def get_unlock_message(self) -> str:
        """Returns a string summarizing the achievements unlocked in this session."""
        if not self.newly_unlocked:
            return ""
            
        lines = ["\n🏆 **Achievements Unlocked!**"]
        for info in self.newly_unlocked:
            rewards = []
            if info.get("yens", 0) > 0: rewards.append(f"{format_number(info['yens'])} Yens")
            if info.get("gems", 0) > 0: rewards.append(f"{info['gems']} Gems")
            if info.get("crystals", 0) > 0: rewards.append(f"{info['crystals']} Crystals")
            
            reward_text = f" ({', '.join(rewards)})" if rewards else ""
            lines.append(f"• **{info['name']}**{reward_text}")
            
        return "\n".join(lines)


# =============================================================
# QUEST TRACKER
# =============================================================
class QuestTracker:
    """
    Handles automatically incrementing quest progress when
    specific in-game actions occur.
    """

    def __init__(self, uid: int):
        self.uid = int(uid)

    def _inc(self, kind: str, code: str, amount: int = 1) -> None:
        """Internal helper to safely increment quests."""
        if amount <= 0:
            return
        try:
            db.quest_increment(self.uid, kind, code, amount)
        except Exception as e:
            print(f"⚠️ Error incrementing quest {code}: {e}")

    # ---------------------------------------------------------
    # EVENT HOOKS
    # ---------------------------------------------------------
    def on_npc_kill(self) -> None:
        """Triggered when a standard NPC is defeated."""
        self._inc("daily", "daily_npc_10")
        self._inc("weekly", "weekly_npc_100")
        self._inc("monthly", "monthly_npc_500")

    def on_battle_win(self) -> None:
        """Triggered on ANY battle victory."""
        self._inc("daily", "daily_win_5")
        self._inc("monthly", "monthly_win_250")

    def on_boss_kill(self) -> None:
        """Triggered when a World Boss is defeated."""
        self._inc("weekly", "weekly_boss_3")

    def on_summon_kill(self) -> None:
        """Triggered when a Summon Boss is defeated."""
        self._inc("monthly", "monthly_summon_5")

    def on_yens_earned(self, amount: int) -> None:
        """Triggered when the player earns Yens."""
        if amount <= 0: return
        self._inc("daily", "daily_earn_5000", amount)
        self._inc("weekly", "weekly_earn_50k", amount)
        self._inc("monthly", "monthly_earn_500k", amount)

    def on_gacha(self, rolls: int) -> None:
        """Triggered when the player rolls the Gacha."""
        if rolls <= 0: return
        self._inc("daily", "daily_gacha_1", rolls)
        self._inc("weekly", "weekly_gacha_10", rolls)


# =============================================================
# ADVANCED SIMULATION TOOLS (For Admin/Debug)
# =============================================================
def estimate_win_chance(
    player_atk: int,
    player_hp: int,
    enemy_hp: int,
    enemy_dmg: int,
    crit: int = 5,
    iterations: int = 100
) -> float:
    """
    Runs a Monte Carlo simulation to estimate the player's win rate.
    Useful for balancing bosses.
    """
    wins = 0
    for _ in range(iterations):
        engine = CombatEngine(player_atk, player_hp, crit=crit)
        won, _, _ = engine.fight("Simulated Enemy", enemy_hp, enemy_dmg)
        if won:
            wins += 1
    return round((wins / iterations) * 100, 2)


# =============================================================
# SELF-TEST SUITE
# =============================================================
if __name__ == "__main__":
    import os
    import sqlite3
    
    print("=============================================")
    print("🔧 RUNNING COMBAT.PY SELF-TESTS")
    print("=============================================\n")

    # 1. Setup Temporary DB
    TEST_DB = "test_combat_engine.sqlite"
    os.environ["DB_PATH"] = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    print("1. Initializing Database...")
    db.init()
    test_uid = 999_888_777
    db.ensure_player(test_uid, "Combat Tester", "tester")
    print("   ✅ DB Initialized.")

    # 2. Test Utility Functions
    print("\n2. Testing Utility Functions...")
    assert roll_damage(100) >= MIN_DAMAGE
    assert roll_crit(0) == False
    assert roll_crit(100) == True
    assert roll_dodge(1) == False  # Very low chance
    assert get_elemental_multiplier("FIRE", "WIND") == 1.5
    assert get_elemental_multiplier("FIRE", "WATER") == 0.5
    assert get_elemental_multiplier("FIRE", "EARTH") == 1.0
    print("   ✅ Math & Elemental logic verified.")

    # 3. Test Combat Engine (Basic Fight)
    print("\n3. Testing Basic Combat Engine...")
    engine = CombatEngine(player_atk=500, player_hp=2000, crit=10, speed=20)
    won, left_hp, log = engine.fight("Saibaman", enemy_hp=500, enemy_dmg=50)
    
    assert won == True, "Player should win against a weak Saibaman"
    assert left_hp > 0, "Player should have HP left"
    assert engine.damage_dealt > 0, "Player should deal damage"
    assert engine.rounds > 0, "Battle should have rounds"
    print(f"   ✅ Basic Fight Won. HP Left: {left_hp}")

    # 4. Test Combat Engine (Hard Fight + Zenkai)
    print("\n4. Testing Boss Fight with Zenkai...")
    # Give player very low HP to trigger Zenkai
    engine_boss = CombatEngine(player_atk=1000, player_hp=100, crit=20, speed=50)
    won_boss, left_hp_boss, log_boss = engine_boss.fight("Beerus", enemy_hp=5000, enemy_dmg=200, enrage=True)
    
    assert engine_boss.zenkai_activations == 1, "Zenkai should have triggered"
    assert won_boss == False, "Player should lose to Beerus with 100 HP"
    assert left_hp_boss == 0, "Player should be dead"
    print(f"   ✅ Boss Fight Lost as expected. Zenkai Activated.")

    # 5. Test Combat History Logging
    print("\n5. Testing Combat History...")
    history = CombatHistory(test_uid)
    
    # Log the won fight
    history.log("Saibaman", 500, engine.damage_dealt, engine.damage_taken, "victory", engine.rounds, "100 Yens")
    # Log the lost fight
    history.log("Beerus", 5000, engine_boss.damage_dealt, engine_boss.damage_taken, "defeat", engine_boss.rounds)
    
    recent = history.get_recent_battles()
    assert len(recent) == 2, "Should have 2 battles in history"
    
    stats = history.get_lifetime_stats()
    assert stats["battles"] == 2, "Lifetime battles should be 2"
    assert stats["wins"] == 1, "Lifetime wins should be 1"
    assert stats["losses"] == 1, "Lifetime losses should be 1"
    
    print(history.render_history())

    # 6. Test Achievements
    print("\n6. Testing Achievements...")
    ach = CombatAchievements(test_uid)
    
    # Trigger checks
    ach.check_combat_milestones(1, 1) # first_blood should unlock
    ach.check_wealth_milestones(2_000_000, 5000) # rich and gem_hoarder
    
    msg = ach.get_unlock_message()
    assert "First Blood" in msg, "First Blood should be in message"
    assert "Millionaire" in msg, "Millionaire should be in message"
    print(msg)

    # 7. Test Quest Tracker
    print("\n7. Testing Quest Tracker...")
    quest = QuestTracker(test_uid)
    quest.on_npc_kill()
    quest.on_battle_win()
    quest.on_yens_earned(5000)
    
    daily_progress = db.quest_progress(test_uid, "daily", "daily_npc_10")
    assert daily_progress == 1, "Daily NPC progress should be 1"
    print(f"   ✅ Quest Progress Verified: {daily_progress} / 10")

    # 8. Test Monte Carlo Simulation
    print("\n8. Testing Monte Carlo Win Rate Estimation...")
    win_chance = estimate_win_chance(500, 2000, 500, 50, iterations=20)
    assert win_chance > 80.0, "Win chance vs weak enemy should be high"
    print(f"   ✅ Estimated Win Chance vs Saibaman: {win_chance}%")

    # Cleanup
    os.remove(TEST_DB)
    print("\n=============================================")
    print("🎉 ALL COMBAT.PY TESTS PASSED SUCCESSFULLY!")
    print("=============================================")
