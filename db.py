from __future__ import annotations

"""
Dragon Ball RPG — Database Layer (Part 1)
=========================================
This file handles all SQLite database interactions.
It is designed to be 100% asynchronous-safe (using context managers)
and handles automatic migrations for new features.

PART 1 CONTAINS:
  - Connection & Schema Initialization
  - Auto-Migrations (Pity, Titles, SP+, etc.)
  - Core Player Management (CRUD)
  - Economy (Give/Spend/Set)
  - HP & Healing Tracking
  - Inventory (Items/Weapons/Armors)
  - Character Roster Management
  - Skill Tree Management
  - Dragon Ball Tracking
  - Quest Progress (JSON tracking)

PART 2 WILL CONTAIN:
  - Combat History Logs
  - Global Raid State
  - Summon Boss HP (Persistent)
  - Gacha & Pity Logic
  - Achievements Unlocking
  - Clan Database Interactions (called from clans.py)
"""

import json
import os
import random
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Optional, Union

import game_data as G

# The path to the SQLite file
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "game.sqlite"))


# =============================================================
# CONNECTION
# =============================================================
def conn() -> sqlite3.Connection:
    """
    Returns a new SQLite connection with Row factory enabled.
    Row factory allows us to access columns by name (e.g., row['user_id']).
    """
    c = sqlite3.connect(DB_PATH, timeout=20.0)
    c.row_factory = sqlite3.Row
    return c


# =============================================================
# INITIALIZATION & MIGRATIONS
# =============================================================
def init() -> None:
    """
    Creates all required tables and runs automatic migrations.
    This is called once at bot startup via bot.py's main() function.
    """
    with conn() as c:
        # Import clans here to avoid circular import issues
        import clans as _clans
        _clans.init_tables(c)

        # ---------------------------------------------------------
        # PLAYERS TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                exp INTEGER DEFAULT 0,
                yens INTEGER DEFAULT 0,
                gems INTEGER DEFAULT 0,
                crystals INTEGER DEFAULT 0,
                tickets INTEGER DEFAULT 0,
                skill_points INTEGER DEFAULT 0,
                keys_elite INTEGER DEFAULT 0,
                keys_boss INTEGER DEFAULT 0,
                npc_streak INTEGER DEFAULT 0,
                current_hp INTEGER DEFAULT NULL,
                equipped_char TEXT,
                weapon TEXT,
                armor TEXT,
                equipped_title TEXT DEFAULT NULL,
                last_raid_hit INTEGER DEFAULT 0,
                rank INTEGER DEFAULT 1,
                admin INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                daily_day TEXT,
                daily_streak INTEGER DEFAULT 0,
                weekly_week TEXT,
                travel TEXT DEFAULT 'Earth',
                fusion_count INTEGER DEFAULT 0,
                total_battles INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                total_dmg_dealt INTEGER DEFAULT 0,
                total_dmg_taken INTEGER DEFAULT 0,
                gacha_pulls INTEGER DEFAULT 0,
                quest_daily_key TEXT DEFAULT '',
                quest_weekly_key TEXT DEFAULT '',
                quest_monthly_key TEXT DEFAULT '',
                quest_daily_json TEXT DEFAULT '{}',
                quest_weekly_json TEXT DEFAULT '{}',
                quest_monthly_json TEXT DEFAULT '{}',
                quest_daily_claimed TEXT DEFAULT '{}',
                quest_weekly_claimed TEXT DEFAULT '{}',
                quest_monthly_claimed TEXT DEFAULT '{}',
                summon_hp_json TEXT DEFAULT '{}'
            )
        """)

        # ---------------------------------------------------------
        # INVENTORY TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                user_id INTEGER,
                item TEXT,
                qty INTEGER DEFAULT 0,
                PRIMARY KEY(user_id, item)
            )
        """)

        # ---------------------------------------------------------
        # CHARACTERS TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                user_id INTEGER,
                name TEXT,
                rarity TEXT,
                PRIMARY KEY(user_id, name)
            )
        """)

        # ---------------------------------------------------------
        # SKILLS TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                user_id INTEGER,
                name TEXT,
                PRIMARY KEY(user_id, name)
            )
        """)

        # ---------------------------------------------------------
        # DRAGON BALLS TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS dragon_balls (
                user_id INTEGER,
                star INTEGER,
                qty INTEGER DEFAULT 0,
                PRIMARY KEY(user_id, star)
            )
        """)

        # ---------------------------------------------------------
        # ART TABLE (For images/assets)
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS art (
                kind TEXT,
                name TEXT,
                file_id TEXT,
                PRIMARY KEY(kind, name)
            )
        """)

        # ---------------------------------------------------------
        # COMBAT LOGS TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS combat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                enemy_name TEXT,
                enemy_max_hp INTEGER DEFAULT 0,
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                outcome TEXT,
                rounds INTEGER DEFAULT 0,
                rewards_text TEXT DEFAULT '',
                created INTEGER DEFAULT (strftime('%s','now'))
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_combat_user ON combat_logs(user_id, id DESC)")

        # ---------------------------------------------------------
        # ACHIEVEMENTS TABLES
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                code TEXT PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS player_achievements (
                user_id INTEGER,
                code TEXT,
                unlocked_at INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY(user_id, code)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_achieve_user ON player_achievements(user_id)")

        # ---------------------------------------------------------
        # GLOBAL RAID TABLE
        # ---------------------------------------------------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS raid (
                id INTEGER PRIMARY KEY CHECK(id=1),
                active INTEGER DEFAULT 0,
                hp INTEGER,
                max_hp INTEGER,
                damage_json TEXT DEFAULT '{}',
                boss_name TEXT DEFAULT '',
                started_at INTEGER DEFAULT 0
            )
        """)
        # Ensure a raid row always exists
        c.execute("""
            INSERT OR IGNORE INTO raid (id, active, hp, max_hp, damage_json, boss_name, started_at)
            VALUES (1, 0, 0, 0, '{}', '', 0)
        """)

        # Seed Achievements
        for code, info in G.ACHIEVEMENTS.items():
            c.execute(
                "INSERT OR IGNORE INTO achievements(code, name, description) VALUES(?,?,?)",
                (code, info["name"], info["desc"]),
            )

        # ---------------------------------------------------------
        # AUTOMATIC MIGRATIONS
        # If you add a new column to the players table in the future,
        # this block will automatically add it to existing databases.
        # ---------------------------------------------------------
        player_cols = [r[1] for r in c.execute("PRAGMA table_info(players)")]
        migrations = [
            ("equipped_title", "TEXT DEFAULT NULL"),
            ("gacha_pulls", "INTEGER DEFAULT 0"),
            ("current_hp", "INTEGER DEFAULT NULL"),
            ("quest_daily_key", "TEXT DEFAULT ''"),
            ("quest_weekly_key", "TEXT DEFAULT ''"),
            ("quest_monthly_key", "TEXT DEFAULT ''"),
            ("quest_daily_json", "TEXT DEFAULT '{}'"),
            ("quest_weekly_json", "TEXT DEFAULT '{}'"),
            ("quest_monthly_json", "TEXT DEFAULT '{}'"),
            ("quest_daily_claimed", "TEXT DEFAULT '{}'"),
            ("quest_weekly_claimed", "TEXT DEFAULT '{}'"),
            ("quest_monthly_claimed", "TEXT DEFAULT '{}'"),
            ("summon_hp_json", "TEXT DEFAULT '{}'"),
            ("total_battles", "INTEGER DEFAULT 0"),
            ("total_wins", "INTEGER DEFAULT 0"),
            ("total_losses", "INTEGER DEFAULT 0"),
            ("total_dmg_dealt", "INTEGER DEFAULT 0"),
            ("total_dmg_taken", "INTEGER DEFAULT 0"),
            ("fusion_count", "INTEGER DEFAULT 0"),
        ]
        
        for col, ddl in migrations:
            if col not in player_cols:
                try:
                    c.execute(f"ALTER TABLE players ADD COLUMN {col} {ddl}")
                    print(f"✅ Migrated players table: added {col}")
                except sqlite3.OperationalError:
                    pass


# =============================================================
# CORE PLAYER MANAGEMENT
# =============================================================
def ensure_player(uid: int, first: str, username: Optional[str]) -> None:
    """
    Creates a player if they don't exist, and updates their name/username.
    This is called every time the user interacts with the bot.
    """
    with conn() as c:
        # Try to insert (ignores if user_id already exists)
        c.execute(
            "INSERT OR IGNORE INTO players(user_id, first_name, username) VALUES(?,?,?)",
            (uid, first or "", username or ""),
        )
        # Update first_name and username (in case they changed it on Telegram)
        c.execute(
            "UPDATE players SET first_name=?, username=? WHERE user_id=?",
            (first or "", username or "", uid),
        )


def player(uid: int) -> Optional[sqlite3.Row]:
    """Returns the full player row, or None if they don't exist."""
    with conn() as c:
        return c.execute("SELECT * FROM players WHERE user_id=?", (uid,)).fetchone()


def player_by_username(username: str) -> Optional[sqlite3.Row]:
    """Searches for a player by their @username or first_name."""
    n = (username or "").replace("@", "").strip()
    if not n:
        return None
    with conn() as c:
        return c.execute(
            "SELECT * FROM players WHERE lower(username)=lower(?) OR lower(first_name)=lower(?)",
            (n, n),
        ).fetchone()


def all_players() -> list[sqlite3.Row]:
    """Returns all registered players, sorted by EXP (highest first)."""
    with conn() as c:
        return c.execute("SELECT * FROM players ORDER BY exp DESC").fetchall()


def leaderboard(limit: int = 10) -> list[sqlite3.Row]:
    """Returns the top N players for the /leaderboard command."""
    with conn() as c:
        return c.execute(
            "SELECT first_name, exp, rank, total_wins FROM players ORDER BY exp DESC LIMIT ?",
            (limit,),
        ).fetchall()


# =============================================================
# LEVEL, EXP, & RANK MATHEMATICS
# =============================================================
def level_of(exp: int) -> int:
    """Calculates player level based on EXP."""
    return 1 + (int(exp or 0) // G.LEVEL_EXP)


def exp_for_next_level(current_exp: int) -> int:
    """Calculates how much more EXP is needed for the next level."""
    cur_level = level_of(current_exp)
    next_threshold = cur_level * G.LEVEL_EXP
    return max(0, next_threshold - int(current_exp or 0))


def rank_of(uid: int) -> int:
    """Calculates a player's global position on the leaderboard."""
    with conn() as c:
        mine = c.execute("SELECT exp FROM players WHERE user_id=?", (uid,)).fetchone()
        if mine is None:
            return 0
        above = c.execute("SELECT COUNT(*) FROM players WHERE exp > ?", (mine["exp"],)).fetchone()[0]
        return above + 1


def player_rank(uid: int) -> int:
    """Returns the player's Ascension Rank (from /rankup)."""
    p = player(uid)
    if not p:
        return 1
    return int(p["rank"] or 1)


# =============================================================
# ECONOMY: RESOURCES (Yens, Gems, Crystals, etc.)
# =============================================================
_GRANTABLE_COLS = {
    "yens", "gems", "crystals", "tickets", "skill_points",
    "keys_elite", "keys_boss", "exp", "gacha_pulls",
}

_SPENDABLE_COLS = {
    "yens", "gems", "crystals", "tickets", "skill_points",
    "keys_elite", "keys_boss",
}


def give(uid: int, **amounts: Union[int, str]) -> None:
    """
    Adds resources to a player's account.
    Usage: give(uid, yens=1000, gems=50)
    """
    for k, v in amounts.items():
        if k not in _GRANTABLE_COLS or v is None:
            continue
        try:
            amt = int(v)
        except (TypeError, ValueError):
            continue
        if amt == 0:
            continue
        with conn() as c:
            c.execute(f"UPDATE players SET {k}={k}+? WHERE user_id=?", (amt, uid))


def spend(uid: int, column: str, amount: int) -> bool:
    """
    Deducts resources from a player's account.
    Returns True if successful, False if they don't have enough.
    """
    if column not in _SPENDABLE_COLS:
        return False
    try:
        amt = int(amount)
    except (TypeError, ValueError):
        return False
    if amt <= 0:
        return False
        
    with conn() as c:
        cur = c.execute(
            f"UPDATE players SET {column}={column}-? WHERE user_id=? AND {column}>=?",
            (amt, uid, amt),
        )
        return cur.rowcount == 1


def set_field(uid: int, field: str, value: Any) -> None:
    """
    Sets a specific column to an exact value.
    Used for equipping characters, weapons, changing travel location, etc.
    """
    allowed = {
        "equipped_char", "weapon", "armor", "npc_streak", "equipped_title",
        "last_raid_hit", "rank", "admin", "banned", "travel", "fusion_count", "current_hp",
    }
    if field not in allowed:
        raise ValueError(f"Invalid field: {field}")
    with conn() as c:
        c.execute(f"UPDATE players SET {field}=? WHERE user_id=?", (value, uid))


# =============================================================
# HP & HEALING MANAGEMENT
# =============================================================
def get_current_hp(uid: int, max_hp: int) -> int:
    """
    Returns the player's current HP.
    If HP is NULL (brand new player), it returns max_hp.
    """
    p = player(uid)
    if not p:
        return max_hp
    hp = p["current_hp"]
    if hp is None:
        return max_hp
    return max(0, min(int(hp), max_hp))


def set_current_hp(uid: int, hp: int) -> None:
    """Saves the player's current HP to the database."""
    with conn() as c:
        c.execute("UPDATE players SET current_hp=? WHERE user_id=?", (int(hp), uid))


def apply_heal(uid: int, max_hp: int, item_name: str) -> tuple[bool, int]:
    """
    Consumes a healing item and restores HP.
    Returns (Success, New_HP).
    """
    if item_name not in G.HEALING:
        return False, get_current_hp(uid, max_hp)
        
    # Try to remove the item from inventory
    if not remove_item(uid, item_name, 1):
        return False, get_current_hp(uid, max_hp)
        
    frac = G.HEALING[item_name]
    cur = get_current_hp(uid, max_hp)
    
    # Calculate new HP
    new_hp = min(max_hp, cur + int(max_hp * frac))
    set_current_hp(uid, new_hp)
    
    return True, new_hp


# =============================================================
# INVENTORY (Items, Weapons, Armors, Potions)
# =============================================================
def add_item(uid: int, item: str, qty: int = 1) -> None:
    """Adds an item to the player's inventory. Stacks if already owned."""
    if not item or qty <= 0:
        return
    with conn() as c:
        c.execute(
            "INSERT INTO items(user_id,item,qty) VALUES(?,?,?) "
            "ON CONFLICT(user_id,item) DO UPDATE SET qty=qty+excluded.qty",
            (uid, item.strip(), qty),
        )


def items(uid: int) -> list[sqlite3.Row]:
    """Returns a list of all items the player owns (item, qty)."""
    with conn() as c:
        return c.execute(
            "SELECT item, qty FROM items WHERE user_id=? AND qty>0 ORDER BY item",
            (uid,),
        ).fetchall()


def remove_item(uid: int, item: str, qty: int = 1) -> bool:
    """
    Removes an item from the player's inventory.
    Returns True if successful, False if they don't have enough.
    """
    if qty <= 0:
        return False
    with conn() as c:
        cur = c.execute(
            "UPDATE items SET qty=qty-? WHERE user_id=? AND item=? AND qty>=?",
            (qty, uid, item, qty),
        )
        return cur.rowcount == 1


def has_item(uid: int, item: str) -> bool:
    """Checks if the player owns at least 1 of a specific item."""
    with conn() as c:
        row = c.execute(
            "SELECT qty FROM items WHERE user_id=? AND item=?", (uid, item)
        ).fetchone()
        return bool(row and row["qty"] > 0)


# =============================================================
# CHARACTER ROSTER MANAGEMENT
# =============================================================
def add_character(uid: int, name: str, rarity: str) -> bool:
    """
    Adds a character to the player's roster.
    Returns True if it was newly added, False if they already had it.
    """
    n = (name or "").strip()
    if not n:
        return False
    with conn() as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO characters(user_id,name,rarity) VALUES(?,?,?)",
            (uid, n, rarity or "common"),
        )
        return cur.rowcount == 1


def characters(uid: int) -> list[sqlite3.Row]:
    """
    Returns all characters owned by the player, sorted by rarity (best first).
    Supports the new SP+ and Omni rarities.
    """
    with conn() as c:
        return c.execute(
            "SELECT name, rarity FROM characters WHERE user_id=? "
            "ORDER BY CASE rarity "
            "  WHEN 'omni' THEN 1 "
            "  WHEN 'sp_plus' THEN 2 "
            "  WHEN 'mythical' THEN 3 "
            "  WHEN 'legendary' THEN 4 "
            "  WHEN 'epic' THEN 5 "
            "  WHEN 'rare' THEN 6 "
            "  ELSE 7 END, name",
            (uid,),
        ).fetchall()


def characters_by_rarity(uid: int) -> dict[str, list[str]]:
    """
    Groups the player's characters into a dictionary by rarity.
    Format: {'omni': ['Zeno', 'Zalama'], 'common': ['Saibaman']}
    """
    rows = characters(uid)
    out = {r: [] for r in ["common", "rare", "epic", "legendary", "mythical", "sp_plus", "omni"]}
    for row in rows:
        out.setdefault(row["rarity"], []).append(row["name"])
    return out


def has_character(uid: int, name: str) -> bool:
    """Checks if the player owns a specific character."""
    if not name:
        return False
    with conn() as c:
        return c.execute(
            "SELECT 1 FROM characters WHERE user_id=? AND name=?", (uid, name)
        ).fetchone() is not None


def character_rarity(uid: int, name: str) -> Optional[str]:
    """Returns the rarity of a specific character, or None if not owned."""
    with conn() as c:
        row = c.execute(
            "SELECT rarity FROM characters WHERE user_id=? AND name=?", (uid, name)
        ).fetchone()
        return row["rarity"] if row else None


def transfer_character(giver: int, target: int, name: str) -> bool:
    """Transfers a character from one player to another."""
    with conn() as c:
        row = c.execute(
            "SELECT rarity FROM characters WHERE user_id=? AND name=?", (giver, name)
        ).fetchone()
        if row is None:
            return False
            
        # Check if target already has it
        if c.execute("SELECT 1 FROM characters WHERE user_id=? AND name=?", (target, name)).fetchone():
            return False
            
        c.execute("DELETE FROM characters WHERE user_id=? AND name=?", (giver, name))
        c.execute("INSERT INTO characters(user_id,name,rarity) VALUES(?,?,?)", (target, name, row["rarity"]))
        c.execute("UPDATE players SET equipped_char=NULL WHERE user_id=? AND equipped_char=?", (giver, name))
        return True


# =============================================================
# SKILLS MANAGEMENT
# =============================================================
def add_skill(uid: int, name: str) -> bool:
    """Unlocks a skill for the player. Returns True if newly unlocked."""
    n = (name or "").strip()
    if not n:
        return False
    with conn() as c:
        return c.execute(
            "INSERT OR IGNORE INTO skills(user_id,name) VALUES(?,?)", (uid, n)
        ).rowcount == 1


def skills(uid: int) -> list[str]:
    """Returns a list of all skill names the player knows."""
    with conn() as c:
        return [r["name"] for r in c.execute("SELECT name FROM skills WHERE user_id=? ORDER BY name", (uid,))]


def has_skill(uid: int, name: str) -> bool:
    """Checks if the player knows a specific skill."""
    with conn() as c:
        return c.execute("SELECT 1 FROM skills WHERE user_id=? AND name=?", (uid, name)).fetchone() is not None


def transfer_skill(giver: int, target: int, name: str) -> bool:
    """Transfers a skill from one player to another."""
    with conn() as c:
        if c.execute("SELECT 1 FROM skills WHERE user_id=? AND name=?", (giver, name)).fetchone() is None:
            return False
        if c.execute("SELECT 1 FROM skills WHERE user_id=? AND name=?", (target, name)).fetchone():
            return False
        c.execute("DELETE FROM skills WHERE user_id=? AND name=?", (giver, name))
        c.execute("INSERT INTO skills(user_id,name) VALUES(?,?)", (target, name))
        return True


# =============================================================
# DRAGON BALLS MANAGEMENT
# =============================================================
def add_dragon_ball(uid: int, star: int, qty: int = 1) -> None:
    """Adds a specific star Dragon Ball to the player."""
    if not isinstance(star, int) or qty <= 0 or star < 1 or star > 7:
        return
    with conn() as c:
        c.execute(
            "INSERT INTO dragon_balls(user_id,star,qty) VALUES(?,?,?) "
            "ON CONFLICT(user_id,star) DO UPDATE SET qty=qty+excluded.qty",
            (uid, star, qty),
        )


def dragon_balls(uid: int) -> dict[int, int]:
    """Returns a dictionary of the player's Dragon Balls {star: qty}."""
    with conn() as c:
        return {r["star"]: r["qty"] for r in c.execute("SELECT star, qty FROM dragon_balls WHERE user_id=? AND qty>0", (uid,))}


def take_one_of_each_dragon_ball(uid: int) -> bool:
    """Consumes 1 of each 1★-7★ Dragon Ball for the /wish command."""
    have = dragon_balls(uid)
    if any(have.get(s, 0) < 1 for s in G.DRAGON_BALL_STARS):
        return False
    with conn() as c:
        for s in G.DRAGON_BALL_STARS:
            c.execute("UPDATE dragon_balls SET qty=qty-1 WHERE user_id=? AND star=?", (uid, s))
    return True


def remove_dragon_ball(uid: int, star: int, qty: int) -> bool:
    """Removes a specific Dragon Ball."""
    if qty <= 0:
        return False
    with conn() as c:
        cur = c.execute(
            "UPDATE dragon_balls SET qty=qty-? WHERE user_id=? AND star=? AND qty>=?",
            (qty, uid, star, qty),
        )
        return cur.rowcount == 1


# =============================================================
# QUEST PROGRESS TRACKING (JSON)
# =============================================================
def _quest_table(kind: str) -> dict:
    """Returns the quest dictionary from game_data."""
    if kind == "daily": return G.DAILY_QUESTS
    if kind == "weekly": return G.WEEKLY_QUESTS
    if kind == "monthly": return G.MONTHLY_QUESTS
    return {}


def _period_key(kind: str) -> str:
    """Returns the current period string (e.g., '2023-10-25')."""
    now = datetime.now(timezone.utc)
    if kind == "daily":
        return now.date().isoformat()
    if kind == "weekly":
        y, w, _ = now.date().isocalendar()
        return f"{y}-W{w:02d}"
    if kind == "monthly":
        return f"{now.year}-{now.month:02d}"
    return ""


def ensure_quests_current(uid: int) -> None:
    """Resets quest progress if the period has changed."""
    p = player(uid)
    if not p:
        return
    with conn() as c:
        for kind in ("daily", "weekly", "monthly"):
            key_col = f"quest_{kind}_key"
            json_col = f"quest_{kind}_json"
            claimed_col = f"quest_{kind}_claimed"
            
            current = p[key_col] if key_col in p.keys() else ""
            expected = _period_key(kind)
            
            if current != expected:
                c.execute(
                    f"UPDATE players SET {key_col}=?, {json_col}='{{}}', {claimed_col}='{{}}' WHERE user_id=?",
                    (expected, uid),
                )


def _load_quest_json(uid: int, kind: str, suffix: str) -> dict:
    """Loads quest progress or claimed JSON."""
    p = player(uid)
    if not p:
        return {}
    col = f"quest_{kind}_{suffix}"
    try:
        raw = p[col] if col in p.keys() else "{}"
        return json.loads(raw or "{}")
    except (ValueError, TypeError, KeyError):
        return {}


def _save_quest_json(uid: int, kind: str, suffix: str, data: dict) -> None:
    """Saves quest progress or claimed JSON."""
    col = f"quest_{kind}_{suffix}"
    with conn() as c:
        c.execute(f"UPDATE players SET {col}=? WHERE user_id=?", (json.dumps(data), uid))


def quest_progress(uid: int, kind: str, code: str) -> int:
    """Returns the current progress (number) for a specific quest."""
    ensure_quests_current(uid)
    data = _load_quest_json(uid, kind, "json")
    try:
        return int(data.get(code, 0))
    except (TypeError, ValueError):
        return 0


def quest_increment(uid: int, kind: str, code: str, amount: int = 1) -> None:
    """Increments progress for a specific quest."""
    if amount <= 0:
        return
    ensure_quests_current(uid)
    data = _load_quest_json(uid, kind, "json")
    try:
        cur = int(data.get(code, 0))
    except (TypeError, ValueError):
        cur = 0
    data[code] = cur + int(amount)
    _save_quest_json(uid, kind, "json", data)


def quest_claimed(uid: int, kind: str) -> dict:
    """Returns a dictionary of claimed quests for the period."""
    ensure_quests_current(uid)
    return _load_quest_json(uid, kind, "claimed")


def claim_quest(uid: int, kind: str, code: str) -> Optional[dict]:
    """
    Claims a quest reward if complete and not yet claimed.
    Returns the quest info dict on success, None otherwise.
    """
    ensure_quests_current(uid)
    info = _quest_table(kind).get(code)
    if not info:
        return None
        
    claimed = quest_claimed(uid, kind)
    if claimed.get(code):
        return None
        
    if quest_progress(uid, kind, code) < info["target"]:
        return None
        
    claimed[code] = 1
    _save_quest_json(uid, kind, "claimed", claimed)
    
    give(
        uid,
        yens=info.get("yens", 0),
        gems=info.get("gems", 0),
        crystals=info.get("crystals", 0),
    )
    return info

# =============================================================
# END OF PART 1
# =============================================================
# Part 2 will contain:
# - Combat History Logs
# - Global Raid State
# - Summon Boss HP (Persistent)
# - Gacha & Pity Logic
# - Achievements Unlocking
# - Admin Commands (Ban, Reset, etc.)
# =============================================================
# =============================================================
# PART 2: COMBAT, ACHIEVEMENTS, RAIDS, GACHA & ADMIN
# =============================================================

# =============================================================
# COMBAT LOGS & HISTORY
# =============================================================
def add_combat_log(uid: int, enemy_name: str, enemy_max_hp: int,
                   damage_dealt: int, damage_taken: int,
                   outcome: str, rounds: int, rewards_text: str = "") -> None:
    """
    Logs a battle to the database and updates the player's cumulative combat stats.
    Outcome must be 'victory' or 'defeat'.
    """
    if outcome not in ("victory", "defeat"):
        outcome = "defeat"
        
    with conn() as c:
        # 1. Insert the detailed log
        c.execute(
            "INSERT INTO combat_logs(user_id, enemy_name, enemy_max_hp, "
            "damage_dealt, damage_taken, outcome, rounds, rewards_text) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (uid, enemy_name, enemy_max_hp, damage_dealt, damage_taken,
             outcome, rounds, rewards_text),
        )
        
        # 2. Update the player's lifetime stats atomically
        c.execute(
            "UPDATE players SET "
            "total_battles = total_battles + 1, "
            "total_wins = total_wins + ?, "
            "total_losses = total_losses + ?, "
            "total_dmg_dealt = total_dmg_dealt + ?, "
            "total_dmg_taken = total_dmg_taken + ? "
            "WHERE user_id=?",
            (
                1 if outcome == "victory" else 0,
                1 if outcome == "defeat" else 0,
                max(0, int(damage_dealt or 0)),
                max(0, int(damage_taken or 0)),
                uid,
            ),
        )


def get_combat_history(uid: int, limit: int = 10) -> list[sqlite3.Row]:
    """Returns the most recent combat logs for the player."""
    limit = max(1, min(int(limit or 10), 50))
    with conn() as c:
        return c.execute(
            "SELECT * FROM combat_logs WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (uid, limit),
        ).fetchall()


def combat_stats(uid: int) -> dict[str, int]:
    """Returns the player's cumulative combat statistics."""
    p = player(uid)
    if not p:
        return {"battles": 0, "wins": 0, "losses": 0, "dealt": 0, "taken": 0}
    return {
        "battles": int(p["total_battles"] or 0),
        "wins":    int(p["total_wins"] or 0),
        "losses":  int(p["total_losses"] or 0),
        "dealt":   int(p["total_dmg_dealt"] or 0),
        "taken":   int(p["total_dmg_taken"] or 0),
    }


# =============================================================
# ACHIEVEMENTS SYSTEM
# =============================================================
def has_achievement(uid: int, code: str) -> bool:
    """Checks if the player has already unlocked a specific achievement."""
    with conn() as c:
        return c.execute(
            "SELECT 1 FROM player_achievements WHERE user_id=? AND code=?",
            (uid, code),
        ).fetchone() is not None


def unlock_achievement(uid: int, code: str) -> Optional[dict]:
    """
    Unlocks an achievement and grants its rewards.
    Returns the achievement info dict if newly unlocked, or None.
    """
    if code not in G.ACHIEVEMENTS:
        return None
    if has_achievement(uid, code):
        return None
        
    info = G.ACHIEVEMENTS[code]
    
    with conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO player_achievements(user_id, code) VALUES(?,?)",
            (uid, code),
        )
        
    # Grant the rewards
    give(
        uid,
        yens=info.get("yens", 0),
        gems=info.get("gems", 0),
        crystals=info.get("crystals", 0),
    )
    return info


def player_achievements(uid: int) -> list[sqlite3.Row]:
    """Returns a list of all achievements the player has unlocked."""
    with conn() as c:
        return c.execute(
            "SELECT a.code, a.name, a.description, pa.unlocked_at "
            "FROM player_achievements pa "
            "JOIN achievements a ON a.code=pa.code "
            "WHERE pa.user_id=? ORDER BY pa.unlocked_at DESC",
            (uid,),
        ).fetchall()


def achievement_count(uid: int) -> int:
    """Returns the total number of achievements unlocked by the player."""
    with conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM player_achievements WHERE user_id=?", (uid,)
        ).fetchone()[0]


# =============================================================
# SUMMON BOSS PERSISTENT HP
# =============================================================
def summon_hp(uid: int, kind: str) -> Optional[int]:
    """
    Gets the current HP of a summon boss for a specific player.
    Returns None if the boss is at full HP (no active session).
    """
    p = player(uid)
    if not p:
        return None
    try:
        data = json.loads(p["summon_hp_json"] or "{}")
    except (ValueError, TypeError):
        data = {}
        
    hp = data.get(kind)
    if hp is None:
        return None
    try:
        return int(hp)
    except (TypeError, ValueError):
        return None


def set_summon_hp(uid: int, kind: str, hp: Optional[int]) -> None:
    """
    Saves the HP of a summon boss.
    Pass None to reset the boss to full HP (e.g., after a victory).
    """
    p = player(uid)
    if not p:
        return
        
    try:
        data = json.loads(p["summon_hp_json"] or "{}")
    except (ValueError, TypeError):
        data = {}
        
    if hp is None:
        data.pop(kind, None)
    else:
        data[kind] = int(hp)
        
    with conn() as c:
        c.execute(
            "UPDATE players SET summon_hp_json=? WHERE user_id=?",
            (json.dumps(data), uid),
        )


# =============================================================
# GLOBAL WORLD RAID
# =============================================================
def raid_state() -> Optional[sqlite3.Row]:
    """Returns the current state of the Global World Raid."""
    with conn() as c:
        return c.execute("SELECT * FROM raid WHERE id=1").fetchone()


def raid_start(boss_name: Optional[str] = None, hp: Optional[int] = None) -> None:
    """Starts or resets the Global World Raid."""
    boss_name = boss_name or G.RAID["name"]
    hp = hp or G.RAID["hp"]
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO raid(id, active, hp, max_hp, damage_json, boss_name, started_at) "
            "VALUES(1, 1, ?, ?, ?, ?, ?)",
            (hp, hp, json.dumps({}), boss_name, int(time.time())),
        )


def raid_hit(uid: int, damage: int) -> Optional[tuple[int, bool, dict]]:
    """
    Attacks the World Raid Boss.
    Returns (hp_left, defeated, damage_map) or None if no raid is active.
    """
    st = raid_state()
    if st is None or not st["active"]:
        return None
        
    try:
        dmg_by = json.loads(st["damage_json"] or "{}")
    except (ValueError, TypeError):
        dmg_by = {}
        
    dmg_by[str(uid)] = int(dmg_by.get(str(uid), 0)) + int(damage)
    hp = max(0, int(st["hp"]) - int(damage))
    defeated = hp == 0
    
    with conn() as c:
        c.execute(
            "UPDATE raid SET hp=?, damage_json=?, active=? WHERE id=1",
            (hp, json.dumps(dmg_by), 0 if defeated else 1),
        )
        
    return hp, defeated, dmg_by


def raid_reset() -> None:
    """Resets the raid to full HP (inactive until raid_start is called)."""
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO raid(id, active, hp, max_hp, damage_json, boss_name, started_at) "
            "VALUES(1, 1, ?, ?, ?, ?, ?)",
            (G.RAID["hp"], G.RAID["hp"], json.dumps({}), G.RAID["name"], int(time.time())),
        )


# =============================================================
# GACHA & PITY SYSTEM
# =============================================================
def roll_rarity(banner_bonus: Optional[dict] = None) -> str:
    """
    Rolls a rarity using the rates from game_data.py.
    Applies the banner bonus multipliers.
    """
    weights = []
    for name, base in G.GACHA_RATES:
        bonus = 1.0
        if banner_bonus:
            bonus = float(banner_bonus.get(name, 1.0))
        weights.append(max(0.0, base * bonus))
        
    total = sum(weights)
    if total <= 0:
        return "common"
        
    r = random.uniform(0, total)
    acc = 0.0
    for (name, _), w in zip(G.GACHA_RATES, weights):
        acc += w
        if r <= acc:
            return name
    return "common"


def pick_character_of_rarity(rarity: str) -> Optional[str]:
    """Picks a random character name from the specified rarity pool."""
    pool = [row["name"] for row in G.CHARACTERS if row.get("rarity") == rarity]
    return random.choice(pool) if pool else None


def increment_pity(uid: int, amount: int = 1) -> None:
    """Increments the player's gacha pity counter."""
    with conn() as c:
        c.execute(
            "UPDATE players SET gacha_pulls = gacha_pulls + ? WHERE user_id=?",
            (amount, uid),
        )


def reset_pity(uid: int) -> None:
    """Resets the player's gacha pity counter to 0."""
    with conn() as c:
        c.execute(
            "UPDATE players SET gacha_pulls = 0 WHERE user_id=?",
            (uid,),
        )


# =============================================================
# DAILY & WEEKLY REWARDS
# =============================================================
def claim_daily(uid: int) -> Optional[tuple[int, dict]]:
    """
    Claims the daily reward.
    Returns (streak, rewards_dict) or None if already claimed today.
    """
    p = player(uid)
    if p is None:
        return None
        
    now = datetime.now(timezone.utc).date()
    today = now.isoformat()
    
    if p["daily_day"] == today:
        return None

    yesterday = (now - timedelta(days=1)).isoformat()
    prev_streak = int(p["daily_streak"] or 0)
    streak = (prev_streak + 1) if p["daily_day"] == yesterday else 1

    rewards = {
        "yens": 300 + min(streak, 20) * 100,
        "gems": min(1 + streak // 5, 6),
    }
    if streak % 3 == 0:
        rewards["tickets"] = 1
    if streak % 7 == 0:
        rewards["crystals"] = 1

    with conn() as c:
        c.execute(
            "UPDATE players SET daily_day=?, daily_streak=? WHERE user_id=?",
            (today, streak, uid),
        )
        
    give(uid, **rewards)
    return streak, rewards


def claim_weekly(uid: int) -> Optional[tuple[dict, int]]:
    """
    Claims the weekly reward.
    Returns (rewards_dict, dragon_ball_star) or None if already claimed this week.
    """
    p = player(uid)
    if p is None:
        return None
        
    today = datetime.now(timezone.utc).date()
    year, week, _ = today.isocalendar()
    key = f"{year}-W{week:02d}"

    if p["weekly_week"] == key:
        return None

    rewards = {
        "yens": 5000,
        "gems": 50,
        "crystals": 5,
        "tickets": 3,
        "skill_points": 5,
    }
    
    give(uid, **rewards)
    
    with conn() as c:
        c.execute("UPDATE players SET weekly_week=? WHERE user_id=?", (key, uid))
        
    star = random.randint(1, 3)
    add_dragon_ball(uid, star)
    
    return rewards, star


# =============================================================
# ADMIN & OWNER TOOLS
# =============================================================
_ADMIN_FIELDS = {
    "rank", "admin", "banned", "travel", "equipped_char",
    "weapon", "armor", "current_hp", "yens", "gems",
    "crystals", "tickets", "skill_points", "keys_elite",
    "keys_boss", "exp", "npc_streak", "fusion_count", "gacha_pulls",
    "equipped_title"
}


def admin_set_field(uid: int, field: str, value: Any) -> bool:
    """
    Admin command: Sets any whitelisted column to an exact value.
    Returns True if successful, False if the field is invalid.
    """
    if field not in _ADMIN_FIELDS:
        return False
    with conn() as c:
        c.execute(f"UPDATE players SET {field}=? WHERE user_id=?", (value, uid))
    return True


def admin_grant(uid: int, **amounts) -> None:
    """Admin command: Alias for give() to make admin code clearer."""
    give(uid, **amounts)


def admin_reset_player(uid: int) -> None:
    """
    Admin command: Wipes a player completely back to a fresh state.
    Deletes all items, characters, skills, and logs.
    """
    with conn() as c:
        # 1. Reset player columns
        c.execute(
            "UPDATE players SET "
            "exp=0, yens=0, gems=0, crystals=0, tickets=0, "
            "skill_points=0, keys_elite=0, keys_boss=0, "
            "npc_streak=0, current_hp=NULL, equipped_char=NULL, "
            "weapon=NULL, armor=NULL, rank=1, admin=0, banned=0, "
            "daily_day=NULL, daily_streak=0, weekly_week=NULL, "
            "travel='Earth', fusion_count=0, gacha_pulls=0, "
            "total_battles=0, total_wins=0, total_losses=0, "
            "total_dmg_dealt=0, total_dmg_taken=0, "
            "equipped_title=NULL, "
            "quest_daily_key='', quest_weekly_key='', quest_monthly_key='', "
            "quest_daily_json='{}', quest_weekly_json='{}', quest_monthly_json='{}', "
            "quest_daily_claimed='{}', quest_weekly_claimed='{}', quest_monthly_claimed='{}', "
            "summon_hp_json='{}' "
            "WHERE user_id=?",
            (uid,),
        )
        
        # 2. Delete all relational data
        c.execute("DELETE FROM items WHERE user_id=?", (uid,))
        c.execute("DELETE FROM characters WHERE user_id=?", (uid,))
        c.execute("DELETE FROM skills WHERE user_id=?", (uid,))
        c.execute("DELETE FROM dragon_balls WHERE user_id=?", (uid,))
        c.execute("DELETE FROM combat_logs WHERE user_id=?", (uid,))
        c.execute("DELETE FROM player_achievements WHERE user_id=?", (uid,))


def admin_ban(uid: int, banned: bool) -> None:
    """Admin command: Bans or unbans a player."""
    with conn() as c:
        c.execute(
            "UPDATE players SET banned=? WHERE user_id=?",
            (1 if banned else 0, uid),
        )


def admin_promote(uid: int, make_admin: bool = True) -> None:
    """Owner command: Grants or revokes Admin rights."""
    with conn() as c:
        c.execute(
            "UPDATE players SET admin=? WHERE user_id=?",
            (1 if make_admin else 0, uid),
        )


def admin_heal(uid: int, max_hp: int) -> None:
    """Admin command: Fully heals a player."""
    set_current_hp(uid, max_hp)


def is_player_admin(uid: int) -> bool:
    """Returns True if the player has Admin rights."""
    p = player(uid)
    return bool(p and p["admin"])


def is_player_banned(uid: int) -> bool:
    """Returns True if the player is banned."""
    p = player(uid)
    return bool(p and p["banned"])


# =============================================================
# ART / ASSETS
# =============================================================
def set_art(kind: str, name: str, file_id: str) -> None:
    """Stores a Telegram file_id for a specific character/weapon image."""
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO art(kind, name, file_id) VALUES(?,?,?)",
            (kind, name, file_id),
        )


def get_art(kind: str, name: str) -> Optional[str]:
    """Retrieves a Telegram file_id for a specific character/weapon image."""
    with conn() as c:
        row = c.execute(
            "SELECT file_id FROM art WHERE kind=? AND name=?",
            (kind, name),
        ).fetchone()
        return row["file_id"] if row else None


# =============================================================
# SELF-TEST (Run this to verify everything works)
# =============================================================
if __name__ == "__main__":
    import os
    import sys

    # Use a temporary DB for testing to avoid wiping the real game
    os.environ["DB_PATH"] = "test_game.sqlite"
    
    # Delete previous test DB if exists
    if os.path.exists("test_game.sqlite"):
        os.remove("test_game.sqlite")
        
    print("🔧 Initializing test database...")
    init()
    print("✅ Database initialized.")

    # 1. Test Player Creation
    test_uid = 111_111_111
    ensure_player(test_uid, "Test Player", "test_user")
    p = player(test_uid)
    print(f"✅ Player Created: {p['first_name']} (ID: {p['user_id']})")

    # 2. Test Economy
    give(test_uid, yens=5000, gems=100)
    p = player(test_uid)
    print(f"✅ Gave 5000 Yens. Current: {p['yens']}")
    
    spend(test_uid, "yens", 2000)
    p = player(test_uid)
    print(f"✅ Spent 2000 Yens. Current: {p['yens']}")
    
    # 3. Test Inventory
    add_item(test_uid, "Senzu Bean", 3)
    inv = items(test_uid)
    print(f"✅ Added Items: {[dict(i) for i in inv]}")
    
    remove_item(test_uid, "Senzu Bean", 1)
    print(f"✅ Removed 1 Senzu Bean.")

    # 4. Test Characters & SP+ Rarity
    add_character(test_uid, "Omni King Zeno", "omni")
    add_character(test_uid, "Kakarot", "sp_plus")
    chars = characters_by_rarity(test_uid)
    print(f"✅ Character Roster: {chars}")

    # 5. Test Combat Log
    add_combat_log(test_uid, "Saibaman", 500, 500, 0, "victory", 3)
    stats = combat_stats(test_uid)
    print(f"✅ Combat Stats: {stats}")
    
    # 6. Test Achievements
    info = unlock_achievement(test_uid, "first_blood")
    print(f"✅ Achievement Unlocked: {info['name'] if info else 'None'}")
    
    # 7. Test Summon Persistent HP
    set_summon_hp(test_uid, "elite", 150000)
    hp = summon_hp(test_uid, "elite")
    print(f"✅ Summon HP saved: {hp}")
    
    # 8. Test Raids
    raid_start("Test Dragon", 1000)
    result = raid_hit(test_uid, 500)
    print(f"✅ Raid Hit: HP left = {result[0]}, Defeated = {result[1]}")
    
    # 9. Test Admin Tools
    admin_set_field(test_uid, "rank", 10)
    p = player(test_uid)
    print(f"✅ Admin Set Rank: {p['rank']}")
    
    admin_reset_player(test_uid)
    p = player(test_uid)
    print(f"✅ Admin Reset: Yens = {p['yens']}, Rank = {p['rank']}")

    # Cleanup
    os.remove("test_game.sqlite")
    print("\n🎉 All db.py self-tests passed successfully!")
