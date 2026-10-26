from __future__ import annotations

"""
Dragon Ball / Anime Crossover RPG — Clan System (Part 1)
========================================================
This file handles the entire Clan Management backend.
It interacts directly with the SQLite database via db.py.

PART 1 CONTAINS:
  - Schema Creation & Migrations (init_tables)
  - Validation & Permission Helpers
  - Core Clan Lifecycle (Create, Join, Leave, Disband)
  - Member Management (Promote, Demote, Kick, Transfer)
  - Clan Treasury (Donate, Withdraw, Audit Logs)
  - Clan Perks (Research Tree)
  - Clan Raids (Start, Hit, Damage Tracking)
  - Clan Territory (Planet Capture)

PART 2 WILL CONTAIN:
  - Announcements
  - Leaderboards & Rankings
  - Full Test Suite
"""

import json
import re
import time
from typing import Optional, Any, List, Dict, Tuple, Union
from sqlite3 import Row

import db
import game_data as G


# =============================================================
# CONSTANTS & CONFIGURATION
# =============================================================

# Cost to create a clan (in Crystals)
CREATE_COST: int = G.CLAN_CREATE_CRYSTALS

# Minimum and maximum characters for a clan name
MIN_NAME_LENGTH: int = 3
MAX_NAME_LENGTH: int = 20

# Maximum number of members allowed in a clan
MAX_CLAN_MEMBERS: int = 50

# Valid roles in a clan hierarchy
ROLE_LEADER: str = "leader"
ROLE_OFFICER: str = "officer"
ROLE_MEMBER: str = "member"

VALID_ROLES: Tuple[str, str, str] = (ROLE_LEADER, ROLE_OFFICER, ROLE_MEMBER)


class ClanError(Exception):
    """
    Custom exception raised for user-facing Clan errors.
    The bot catches this and displays the message to the user.
    """
    pass


# =============================================================
# 1. DATABASE SCHEMA & INITIALIZATION
# =============================================================

def init_tables(c) -> None:
    """
    Creates all required tables for the Clan system.
    This is called automatically by db.init() on bot startup.
    
    Args:
        c (sqlite3.Connection): The active database connection.
    """
    c.executescript(
        """
        -- =====================================================
        -- CLANS TABLE (The core clan data)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS clans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE COLLATE NOCASE,
            created INTEGER DEFAULT (strftime('%s','now')),
            treasure_yens INTEGER DEFAULT 0,
            treasure_gems INTEGER DEFAULT 0,
            treasure_crystals INTEGER DEFAULT 0,
            announcement TEXT DEFAULT '',
            perks_json TEXT DEFAULT '{}',
            exp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            territory_json TEXT DEFAULT '[]'
        );

        -- =====================================================
        -- CLAN MEMBERS TABLE (Who is in what clan)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS clan_members (
            user_id INTEGER PRIMARY KEY,
            clan_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            joined_at INTEGER DEFAULT (strftime('%s','now')),
            contribution INTEGER DEFAULT 0,
            FOREIGN KEY(clan_id) REFERENCES clans(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_members_clan ON clan_members(clan_id);

        -- =====================================================
        -- CLAN RAIDS TABLE (Active boss battles)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS clan_raids (
            clan_id INTEGER NOT NULL,
            boss_name TEXT NOT NULL,
            hp INTEGER,
            max_hp INTEGER,
            damage_json TEXT DEFAULT '{}',
            active INTEGER DEFAULT 0,
            started_at INTEGER DEFAULT (strftime('%s','now')),
            PRIMARY KEY(clan_id, boss_name),
            FOREIGN KEY(clan_id) REFERENCES clans(id) ON DELETE CASCADE
        );

        -- =====================================================
        -- CLAN LOGS TABLE (Audit trail for treasury & actions)
        -- =====================================================
        CREATE TABLE IF NOT EXISTS clan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created INTEGER DEFAULT (strftime('%s','now')),
            FOREIGN KEY(clan_id) REFERENCES clans(id) ON DELETE CASCADE
        );
        """
    )

    # ---------------------------------------------------------
    # MIGRATIONS (Ensure older DBs get new columns)
    # ---------------------------------------------------------
    cols = [r[1] for r in c.execute("PRAGMA table_info(clans)")]
    
    if "perks_json" not in cols:
        c.execute("ALTER TABLE clans ADD COLUMN perks_json TEXT DEFAULT '{}'")
    if "announcement" not in cols:
        c.execute("ALTER TABLE clans ADD COLUMN announcement TEXT DEFAULT ''")
    if "exp" not in cols:
        c.execute("ALTER TABLE clans ADD COLUMN exp INTEGER DEFAULT 0")
    if "level" not in cols:
        c.execute("ALTER TABLE clans ADD COLUMN level INTEGER DEFAULT 1")
    if "territory_json" not in cols:
        c.execute("ALTER TABLE clans ADD COLUMN territory_json TEXT DEFAULT '[]'")

    member_cols = [r[1] for r in c.execute("PRAGMA table_info(clan_members)")]
    if "contribution" not in member_cols:
        c.execute("ALTER TABLE clan_members ADD COLUMN contribution INTEGER DEFAULT 0")


# =============================================================
# 2. VALIDATION & HELPER FUNCTIONS
# =============================================================

def _valid_name(name: str) -> str:
    """
    Validates and normalizes a clan name.
    Throws ClanError if the name is invalid.
    """
    if not name:
        raise ClanError("Clan name cannot be empty.")
        
    # Strip excess whitespace
    cleaned_name = " ".join(name.split())
    
    # Check length
    if len(cleaned_name) < MIN_NAME_LENGTH:
        raise ClanError(f"Clan name must be at least {MIN_NAME_LENGTH} characters.")
    if len(cleaned_name) > MAX_NAME_LENGTH:
        raise ClanError(f"Clan name cannot exceed {MAX_NAME_LENGTH} characters.")
        
    # Check characters (Alphanumeric and spaces only)
    if not re.fullmatch(r"[A-Za-z0-9 ]+", cleaned_name):
        raise ClanError("Clan name can only contain letters, numbers, and spaces.")
        
    return cleaned_name


def _valid_role(role: str) -> bool:
    """Checks if a role string is valid."""
    return role in VALID_ROLES


def _format_time(timestamp: int) -> str:
    """Formats a Unix timestamp into a readable date string."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


# =============================================================
# 3. LOOKUP FUNCTIONS
# =============================================================

def clan_by_name(name: str) -> Optional[Row]:
    """
    Fetches a clan by its name (case-insensitive).
    Returns the Row if found, None otherwise.
    """
    if not name:
        return None
    with db.conn() as c:
        return c.execute(
            "SELECT * FROM clans WHERE name=? COLLATE NOCASE",
            (name.strip(),),
        ).fetchone()


def clan_by_id(clan_id: int) -> Optional[Row]:
    """Fetches a clan by its numerical ID."""
    with db.conn() as c:
        return c.execute("SELECT * FROM clans WHERE id=?", (clan_id,)).fetchone()


def membership(user_id: int) -> Optional[Row]:
    """
    Returns the player's clan membership details (joined with clan data).
    Returns None if the player is not in a clan.
    """
    with db.conn() as c:
        return c.execute(
            "SELECT m.clan_id, m.role, m.joined_at, m.contribution, "
            "k.name, k.created, k.treasure_yens, k.treasure_gems, "
            "k.treasure_crystals, k.announcement, k.perks_json, k.level, k.exp "
            "FROM clan_members m "
            "JOIN clans k ON k.id = m.clan_id "
            "WHERE m.user_id = ?",
            (user_id,),
        ).fetchone()


def members(clan_id: int) -> List[Row]:
    """
    Fetches all members of a clan, sorted by role hierarchy (Leader > Officer > Member).
    Also fetches their player names from the players table.
    """
    with db.conn() as c:
        return c.execute(
            "SELECT m.user_id, m.role, m.joined_at, m.contribution, "
            "p.first_name, p.username, p.exp, p.rank "
            "FROM clan_members m "
            "LEFT JOIN players p ON p.user_id = m.user_id "
            "WHERE m.clan_id = ? "
            "ORDER BY CASE m.role "
            "  WHEN 'leader' THEN 0 "
            "  WHEN 'officer' THEN 1 "
            "  ELSE 2 END, p.first_name",
            (clan_id,),
        ).fetchall()


def member_count(clan_id: int) -> int:
    """Returns the total number of players in a clan."""
    with db.conn() as c:
        result = c.execute(
            "SELECT COUNT(*) FROM clan_members WHERE clan_id=?", (clan_id,)
        ).fetchone()
        return result[0] if result else 0


def _role_of(user_id: int, clan_id: int) -> Optional[str]:
    """Internal helper to get a player's role in a specific clan."""
    with db.conn() as c:
        row = c.execute(
            "SELECT role FROM clan_members WHERE user_id=? AND clan_id=?",
            (user_id, clan_id),
        ).fetchone()
        return row["role"] if row else None


def _require_permission(actor_id: int, clan_id: int, allowed_roles: Tuple[str, ...]) -> str:
    """
    Checks if a player has the required role to perform an action.
    Throws ClanError if they don't have permission.
    Returns the actor's role if successful.
    """
    role = _role_of(actor_id, clan_id)
    
    if role is None:
        raise ClanError("You are not a member of this clan.")
        
    if role not in allowed_roles:
        raise ClanError(f"You do not have permission. Required role: {', '.join(allowed_roles).title()}")
        
    return role


# =============================================================
# 4. AUDIT LOGGING
# =============================================================

def add_log(clan_id: int, user_id: int, action: str, details: str = "") -> None:
    """
    Adds an entry to the Clan Audit Log. Used for tracking treasury donations,
    member kicks, and raid hits.
    """
    with db.conn() as c:
        c.execute(
            "INSERT INTO clan_logs(clan_id, user_id, action, details) VALUES(?,?,?,?)",
            (clan_id, user_id, action, details)
        )


def get_logs(clan_id: int, limit: int = 10) -> List[Row]:
    """Fetches the most recent audit logs for a clan."""
    with db.conn() as c:
        return c.execute(
            "SELECT l.*, p.first_name FROM clan_logs l "
            "LEFT JOIN players p ON p.user_id = l.user_id "
            "WHERE l.clan_id=? ORDER BY l.id DESC LIMIT ?",
            (clan_id, limit)
        ).fetchall()


# =============================================================
# 5. CLAN LIFECYCLE (Create, Join, Leave, Disband)
# =============================================================

def create(user_id: int, name: str) -> int:
    """
    Creates a new Clan.
    
    Args:
        user_id: The Telegram ID of the creator.
        name: The desired clan name.
        
    Returns:
        int: The newly created clan ID.
        
    Raises:
        ClanError: If the user is already in a clan, the name is taken, or they lack funds.
    """
    # 1. Validate Name
    clean_name = _valid_name(name)
    
    # 2. Check if user is already in a clan
    if membership(user_id):
        raise ClanError("You are already in a clan. Leave it first before creating a new one.")
        
    # 3. Check if clan name is taken
    if clan_by_name(clean_name):
        raise ClanError("That clan name is already taken.")
        
    # 4. Check funds
    if not db.spend(user_id, "crystals", CREATE_COST):
        raise ClanError(f"You need {CREATE_COST} Crystals to create a clan.")

    # 5. Create the clan
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO clans(name, treasure_yens, treasure_gems, treasure_crystals, perks_json, announcement) "
            "VALUES(?, 0, 0, 0, '{}', '')",
            (clean_name,),
        )
        clan_id = cur.lastrowid
        
        # 6. Assign creator as Leader
        c.execute(
            "INSERT INTO clan_members(user_id, clan_id, role) VALUES(?, ?, 'leader')",
            (user_id, clan_id),
        )
        
    add_log(clan_id, user_id, "CREATE", f"Clan '{clean_name}' was founded.")
    return clan_id


def join(user_id: int, name: str) -> int:
    """
    Joins an existing Clan.
    
    Raises:
        ClanError: If already in a clan, clan doesn't exist, or clan is full.
    """
    if membership(user_id):
        raise ClanError("You are already in a clan.")
        
    clan = clan_by_name(name)
    if not clan:
        raise ClanError("No clan with that name exists.")
        
    if member_count(clan["id"]) >= MAX_CLAN_MEMBERS:
        raise ClanError("This clan is currently full.")
        
    with db.conn() as c:
        c.execute(
            "INSERT INTO clan_members(user_id, clan_id, role) VALUES(?, ?, 'member')",
            (user_id, clan["id"]),
        )
        
    add_log(clan["id"], user_id, "JOIN", "Joined the clan.")
    return clan["id"]


def leave(user_id: int) -> str:
    """
    Leaves the current Clan.
    If the Leader leaves and is the only member, the clan is disbanded.
    If the Leader leaves and there are others, they must transfer leadership first.
    
    Returns:
        str: 'left' or 'disbanded'
    """
    m = membership(user_id)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    others = [r for r in members(clan_id) if r["user_id"] != user_id]
    
    if _role_of(user_id, clan_id) == ROLE_LEADER and others:
        raise ClanError("You are the Leader. Transfer leadership to someone else before leaving.")
        
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE user_id=?", (user_id,))
        
        # If the clan is empty, delete it entirely
        if not others:
            c.execute("DELETE FROM clan_raids WHERE clan_id=?", (clan_id,))
            c.execute("DELETE FROM clan_logs WHERE clan_id=?", (clan_id,))
            c.execute("DELETE FROM clans WHERE id=?", (clan_id,))
            return "disbanded"
            
    add_log(clan_id, user_id, "LEAVE", "Left the clan.")
    return "left"


def disband(user_id: int) -> None:
    """
    Disbands the entire Clan. Only the Leader can do this.
    """
    m = membership(user_id)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(user_id, clan_id, (ROLE_LEADER,))
    
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE clan_id=?", (clan_id,))
        c.execute("DELETE FROM clan_raids WHERE clan_id=?", (clan_id,))
        c.execute("DELETE FROM clan_logs WHERE clan_id=?", (clan_id,))
        c.execute("DELETE FROM clans WHERE id=?", (clan_id,))


# =============================================================
# 6. MEMBER MANAGEMENT
# =============================================================

def add_member(actor: int, target: int) -> None:
    """Invites/Adds a player to the clan. Leader/Officer only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER, ROLE_OFFICER))
    
    if membership(target):
        raise ClanError("That player is already in a clan.")
        
    if member_count(clan_id) >= MAX_CLAN_MEMBERS:
        raise ClanError("Clan is full.")
        
    with db.conn() as c:
        c.execute(
            "INSERT INTO clan_members(user_id, clan_id, role) VALUES(?, ?, 'member')",
            (target, clan_id),
        )
    add_log(clan_id, actor, "ADD", f"Added user {target} to the clan.")


def remove_member(actor: int, target: int) -> None:
    """Kicks a member from the clan. Leader/Officer only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    actor_role = _require_permission(actor, clan_id, (ROLE_LEADER, ROLE_OFFICER))
    
    target_membership = membership(target)
    if not target_membership or target_membership["clan_id"] != clan_id:
        raise ClanError("That player is not in your clan.")
        
    if actor == target:
        raise ClanError("Use the Leave command instead.")
        
    target_role = _role_of(target, clan_id)
    
    if target_role == ROLE_LEADER:
        raise ClanError("You cannot kick the Leader.")
        
    if actor_role == ROLE_OFFICER and target_role == ROLE_OFFICER:
        raise ClanError("Officers cannot kick other Officers.")
        
    with db.conn() as c:
        c.execute("DELETE FROM clan_members WHERE user_id=?", (target,))
        
    add_log(clan_id, actor, "KICK", f"Kicked user {target} from the clan.")


def promote(actor: int, target: int) -> None:
    """Promotes a Member to Officer. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    if membership(target) is None or membership(target)["clan_id"] != clan_id:
        raise ClanError("That player is not in your clan.")
        
    if _role_of(target, clan_id) != ROLE_MEMBER:
        raise ClanError("Only Members can be promoted to Officer.")
        
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='officer' WHERE user_id=?", (target,))
    add_log(clan_id, actor, "PROMOTE", f"Promoted user {target} to Officer.")


def demote(actor: int, target: int) -> None:
    """Demotes an Officer to Member. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    if _role_of(target, clan_id) != ROLE_OFFICER:
        raise ClanError("Only Officers can be demoted.")
        
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='member' WHERE user_id=?", (target,))
    add_log(clan_id, actor, "DEMOTE", f"Demoted user {target} to Member.")


def transfer_leadership(actor: int, target: int) -> None:
    """Transfers Clan Leadership to another member. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    if membership(target) is None or membership(target)["clan_id"] != clan_id:
        raise ClanError("That player is not in your clan.")
        
    with db.conn() as c:
        c.execute("UPDATE clan_members SET role='officer' WHERE user_id=?", (actor,))
        c.execute("UPDATE clan_members SET role='leader' WHERE user_id=?", (target,))
        
    add_log(clan_id, actor, "TRANSFER", f"Transferred leadership to user {target}.")


# =============================================================
# 7. CLAN TREASURY (Deposit / Withdraw)
# =============================================================

def add_treasure(clan_id: int, yens: int = 0, gems: int = 0, crystals: int = 0, actor_id: int = 0) -> None:
    """
    Adds resources to the Clan Vault.
    Called by /clan donate.
    """
    yens = max(0, int(yens or 0))
    gems = max(0, int(gems or 0))
    crystals = max(0, int(crystals or 0))
    
    if yens == 0 and gems == 0 and crystals == 0:
        return
        
    with db.conn() as c:
        c.execute(
            "UPDATE clans SET "
            "treasure_yens = treasure_yens + ?, "
            "treasure_gems = treasure_gems + ?, "
            "treasure_crystals = treasure_crystals + ? "
            "WHERE id=?",
            (yens, gems, crystals, clan_id),
        )
        
        # Update member contribution
        if actor_id:
            c.execute(
                "UPDATE clan_members SET contribution = contribution + ? WHERE user_id=?",
                (yens + (gems * 100) + (crystals * 1000), actor_id)  # Convert to a unified score
            )
            
    if actor_id:
        add_log(clan_id, actor_id, "DONATE", f"Donated {yens} Yens, {gems} Gems, {crystals} Crystals.")


def withdraw_treasure(actor: int, yens: int = 0, gems: int = 0, crystals: int = 0) -> None:
    """
    Withdraws resources from the Clan Vault.
    Leader only.
    """
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    yens = max(0, int(yens or 0))
    gems = max(0, int(gems or 0))
    crystals = max(0, int(crystals or 0))
    
    with db.conn() as c:
        # Check if vault has enough
        row = c.execute(
            "SELECT treasure_yens, treasure_gems, treasure_crystals FROM clans WHERE id=?",
            (clan_id,)
        ).fetchone()
        
        if (yens > row["treasure_yens"] or gems > row["treasure_gems"] or crystals > row["treasure_crystals"]):
            raise ClanError("Not enough resources in the Clan Vault.")
            
        c.execute(
            "UPDATE clans SET "
            "treasure_yens = treasure_yens - ?, "
            "treasure_gems = treasure_gems - ?, "
            "treasure_crystals = treasure_crystals - ? "
            "WHERE id=?",
            (yens, gems, crystals, clan_id),
        )
        
    db.give(actor, yens=yens, gems=gems, crystals=crystals)
    add_log(clan_id, actor, "WITHDRAW", f"Withdrew {yens} Yens, {gems} Gems, {crystals} Crystals.")


# =============================================================
# 8. CLAN PERKS (Research Tree)
# =============================================================

def get_perks(clan_id: int) -> Dict[str, int]:
    """Returns a dictionary of researched perks for a clan."""
    with db.conn() as c:
        row = c.execute("SELECT perks_json FROM clans WHERE id=?", (clan_id,)).fetchone()
        if not row:
            return {}
        try:
            return json.loads(row["perks_json"] or "{}")
        except (ValueError, TypeError):
            return {}


def has_perk(clan_id: int, code: str) -> bool:
    """Checks if a clan has a specific perk."""
    perks = get_perks(clan_id)
    return code in perks


def buy_perk(actor: int, code: str) -> None:
    """Researches a new perk using Clan Vault Crystals. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    if code not in G.CLAN_PERKS:
        raise ClanError("Unknown perk.")
        
    perks = get_perks(clan_id)
    if code in perks:
        raise ClanError("This perk is already researched.")
        
    cost = G.CLAN_PERKS[code]["cost"]
    if m["treasure_crystals"] < cost:
        raise ClanError(f"Not enough Crystals in the Clan Vault. Needs {cost}.")
        
    perks[code] = 1
    
    with db.conn() as c:
        c.execute(
            "UPDATE clans SET treasure_crystals = treasure_crystals - ?, perks_json = ? WHERE id=?",
            (cost, json.dumps(perks), clan_id),
        )
        
    add_log(clan_id, actor, "RESEARCH", f"Researched perk: {G.CLAN_PERKS[code]['name']}.")


# =============================================================
# 9. CLAN RAIDS
# =============================================================

def clan_raid_state(clan_id: int) -> Optional[Row]:
    """Returns the current active raid for a clan."""
    with db.conn() as c:
        return c.execute(
            "SELECT * FROM clan_raids WHERE clan_id=? AND active=1",
            (clan_id,)
        ).fetchone()


def clan_raid_start(clan_id: int, boss_name: str, hp: int, dmg: int) -> None:
    """Starts a new Clan Raid Boss."""
    with db.conn() as c:
        c.execute(
            "INSERT INTO clan_raids(clan_id, boss_name, hp, max_hp, damage_json, active, started_at) "
            "VALUES(?,?,?,?,?,1,?) "
            "ON CONFLICT(clan_id, boss_name) DO UPDATE SET "
            "hp=excluded.hp, max_hp=excluded.max_hp, damage_json=excluded.damage_json, active=1, started_at=excluded.started_at",
            (clan_id, boss_name, hp, hp, json.dumps({}), int(time.time())),
        )


def clan_raid_hit(clan_id: int, user_id: int, damage: int) -> Tuple[int, bool, Dict[str, int], str]:
    """
    Attacks the active Clan Raid Boss.
    Returns (hp_left, defeated, damage_map, boss_name).
    """
    damage = max(0, int(damage))
    
    with db.conn() as c:
        row = c.execute(
            "SELECT * FROM clan_raids WHERE clan_id=? AND active=1",
            (clan_id,)
        ).fetchone()
        
        if not row:
            raise ClanError("There is no active Clan Raid.")
            
        try:
            dmg_by = json.loads(row["damage_json"] or "{}")
        except (ValueError, TypeError):
            dmg_by = {}
            
        key = str(user_id)
        dmg_by[key] = int(dmg_by.get(key, 0)) + damage
        
        hp = max(0, int(row["hp"]) - damage)
        defeated = hp == 0
        
        c.execute(
            "UPDATE clan_raids SET hp=?, damage_json=?, active=? WHERE clan_id=? AND boss_name=?",
            (hp, json.dumps(dmg_by), 0 if defeated else 1, clan_id, row["boss_name"]),
        )
        
        # Update member contribution for raid hit
        c.execute(
            "UPDATE clan_members SET contribution = contribution + ? WHERE user_id=?",
            (damage, user_id)
        )
        
    add_log(clan_id, user_id, "RAID_HIT", f"Dealt {damage} damage to {row['boss_name']}.")
    return hp, defeated, dmg_by, row["boss_name"]


def clan_raid_damage_report(clan_id: int) -> List[Dict[str, Any]]:
    """Returns a sorted list of damage dealers for the active raid."""
    st = clan_raid_state(clan_id)
    if not st:
        return []
        
    try:
        dmg_by = json.loads(st["damage_json"] or "{}")
    except (ValueError, TypeError):
        dmg_by = {}
        
    report = []
    for uid_str, dmg in dmg_by.items():
        try:
            uid = int(uid_str)
            p = db.player(uid)
            name = p["first_name"] if p else f"User {uid}"
        except (ValueError, TypeError):
            name = uid_str
            
        report.append({"name": name, "damage": int(dmg)})
        
    return sorted(report, key=lambda x: x["damage"], reverse=True)


# =============================================================
# 10. TERRITORY CAPTURE
# =============================================================

def capture_planet(actor: int, planet: str) -> None:
    """Captures a planet for the clan. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    if planet not in G.PLANETS:
        raise ClanError("Unknown planet.")
        
    territory = []
    try:
        territory = json.loads(m["territory_json"] or "[]")
    except (ValueError, TypeError):
        pass
        
    if planet not in territory:
        territory.append(planet)
        
    with db.conn() as c:
        c.execute("UPDATE clans SET territory_json=? WHERE id=?", (json.dumps(territory), clan_id))
        
    add_log(clan_id, actor, "CAPTURE", f"Captured planet {planet}.")


def list_territory(clan_id: int) -> List[str]:
    """Returns a list of captured planets."""
    clan = clan_by_id(clan_id)
    if not clan:
        return []
    try:
        return json.loads(clan["territory_json"] or "[]")
    except (ValueError, TypeError):
        return []

# =============================================================
# END OF PART 1
# =============================================================
# Part 2 will contain:
# - Announcements
# - Leaderboards & Rankings
# - Full Self-Test Suite
# =============================================================
# =============================================================
# PART 2: ANNOUNCEMENTS, LEVELING, MISSIONS & LEADERBOARDS
# =============================================================

# =============================================================
# 11. ANNOUNCEMENTS
# =============================================================

def set_announcement(actor: int, text: str) -> None:
    """
    Sets a new announcement for the clan.
    Only Leaders and Officers can use this.
    
    Args:
        actor (int): The user_id of the person setting the announcement.
        text (str): The announcement text (max 300 characters).
    """
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER, ROLE_OFFICER))
    
    # Sanitize the text (prevent Telegram markdown injection and truncate)
    import html
    safe_text = html.escape(text.strip())
    if len(safe_text) > 300:
        safe_text = safe_text[:297] + "..."
        
    with db.conn() as c:
        c.execute("UPDATE clans SET announcement=? WHERE id=?", (safe_text, clan_id))
        
    add_log(clan_id, actor, "ANNOUNCE", f"Updated the clan announcement.")


def get_announcement(clan_id: int) -> str:
    """
    Retrieves the current announcement for a clan.
    Returns an empty string if no announcement is set.
    """
    with db.conn() as c:
        row = c.execute("SELECT announcement FROM clans WHERE id=?", (clan_id,)).fetchone()
        if row and row["announcement"]:
            return row["announcement"]
        return ""


# =============================================================
# 12. CLAN LEVELING & EXP SYSTEM
# =============================================================

# Formula for EXP required to reach the next level: 
# Level 1 -> 2 requires 10,000 EXP
# Level 2 -> 3 requires 25,000 EXP
# Level 3 -> 4 requires 50,000 EXP
def get_exp_needed_for_level(level: int) -> int:
    """Calculates the total EXP required to level up from the current level."""
    if level <= 0:
        return 10000
    return int(10000 * (level ** 1.5))


def add_clan_exp(clan_id: int, amount: int, reason: str = "Activity") -> bool:
    """
    Adds EXP to a clan. If the clan reaches the threshold, it levels up.
    
    Returns:
        bool: True if the clan leveled up, False otherwise.
    """
    amount = max(0, int(amount))
    if amount == 0:
        return False
        
    with db.conn() as c:
        clan = c.execute("SELECT level, exp FROM clans WHERE id=?", (clan_id,)).fetchone()
        if not clan:
            return False
            
        current_level = clan["level"]
        current_exp = clan["exp"]
        new_exp = current_exp + amount
        
        leveled_up = False
        needed_exp = get_exp_needed_for_level(current_level)
        
        while new_exp >= needed_exp:
            new_exp -= needed_exp
            current_level += 1
            leveled_up = True
            needed_exp = get_exp_needed_for_level(current_level)
            
            # Log the level up
            add_log(clan_id, 0, "LEVEL_UP", f"Clan reached Level {current_level}!")
            
        c.execute(
            "UPDATE clans SET exp=?, level=? WHERE id=?",
            (new_exp, current_level, clan_id)
        )
        
    return leveled_up


def get_clan_level_bonus(level: int) -> float:
    """
    Returns a percentage bonus to all stats based on Clan Level.
    Example: Level 5 grants a 5% bonus to ATK and HP for all members.
    """
    return min(level * 0.01, 0.20)  # Max 20% bonus at level 20


# =============================================================
# 13. CLAN MISSIONS (Weekly Objectives)
# =============================================================

CLAN_MISSIONS = {
    "clan_raid_10": {
        "name": "Raid Fanatics",
        "desc": "Defeat 10 Clan Raid Bosses collectively.",
        "target": 10,
        "reward_exp": 50000,
        "reward_crystals": 500,
    },
    "clan_donate_100k": {
        "name": "Generous Hearts",
        "desc": "Donate a total of 100,000 Yens to the vault.",
        "target": 100000,
        "reward_exp": 25000,
        "reward_crystals": 300,
    },
    "clan_member_join_5": {
        "name": "Recruitment Drive",
        "desc": "Recruit 5 new members to the clan.",
        "target": 5,
        "reward_exp": 15000,
        "reward_crystals": 200,
    },
}


def _clan_mission_key() -> str:
    """Returns the current weekly period key (e.g., '2023-W42')."""
    now = datetime.now(timezone.utc)
    y, w, _ = now.date().isocalendar()
    return f"{y}-W{w:02d}"


def increment_clan_mission(clan_id: int, code: str, amount: int = 1) -> None:
    """
    Increments progress for a specific clan mission.
    Missions reset automatically every Monday.
    """
    if code not in CLAN_MISSIONS or amount <= 0:
        return
        
    with db.conn() as c:
        clan = c.execute("SELECT missions_json, mission_week FROM clans WHERE id=?", (clan_id,)).fetchone()
        if not clan:
            return
            
        current_week = _clan_mission_key()
        
        # Check if we need to reset the missions
        if clan["mission_week"] != current_week:
            missions_data = {}
            c.execute(
                "UPDATE clans SET missions_json='{}', mission_week=? WHERE id=?",
                (current_week, clan_id)
            )
        else:
            try:
                missions_data = json.loads(clan["missions_json"] or "{}")
            except (ValueError, TypeError):
                missions_data = {}
                
        # Increment
        try:
            cur_progress = int(missions_data.get(code, 0))
        except (ValueError, TypeError):
            cur_progress = 0
            
        missions_data[code] = cur_progress + amount
        
        c.execute(
            "UPDATE clans SET missions_json=? WHERE id=?",
            (json.dumps(missions_data), clan_id)
        )


def get_clan_missions(clan_id: int) -> Dict[str, Dict[str, Any]]:
    """Returns the current progress of all clan missions."""
    with db.conn() as c:
        clan = c.execute("SELECT missions_json, mission_week FROM clans WHERE id=?", (clan_id,)).fetchone()
        if not clan:
            return {}
            
        if clan["mission_week"] != _clan_mission_key():
            return {code: {"progress": 0, **info} for code, info in CLAN_MISSIONS.items()}
            
        try:
            data = json.loads(clan["missions_json"] or "{}")
        except (ValueError, TypeError):
            data = {}
            
        result = {}
        for code, info in CLAN_MISSIONS.items():
            result[code] = {
                "progress": int(data.get(code, 0)),
                "target": info["target"],
                "name": info["name"],
                "desc": info["desc"],
                "reward_exp": info["reward_exp"],
                "reward_crystals": info["reward_crystals"],
            }
        return result


def claim_clan_mission(actor: int, code: str) -> bool:
    """Claims the reward for a completed clan mission. Leader only."""
    m = membership(actor)
    if not m:
        raise ClanError("You are not in a clan.")
        
    clan_id = m["clan_id"]
    _require_permission(actor, clan_id, (ROLE_LEADER,))
    
    missions = get_clan_missions(clan_id)
    if code not in missions:
        raise ClanError("Invalid mission code.")
        
    mission = missions[code]
    if mission["progress"] < mission["target"]:
        raise ClanError("This mission is not yet complete.")
        
    with db.conn() as c:
        # Reset this specific mission to 0
        clan = c.execute("SELECT missions_json FROM clans WHERE id=?", (clan_id,)).fetchone()
        try:
            data = json.loads(clan["missions_json"] or "{}")
        except (ValueError, TypeError):
            data = {}
            
        if data.get(code, 0) == -1:
            raise ClanError("Reward already claimed this week.")
            
        data[code] = -1 # Mark as claimed
        c.execute("UPDATE clans SET missions_json=? WHERE id=?", (json.dumps(data), clan_id))
        
        # Grant rewards directly to the vault
        c.execute(
            "UPDATE clans SET treasure_crystals = treasure_crystals + ? WHERE id=?",
            (mission["reward_crystals"], clan_id)
        )
        
    add_clan_exp(clan_id, mission["reward_exp"], f"Completed mission: {mission['name']}")
    add_log(clan_id, actor, "MISSION", f"Claimed reward for {mission['name']}.")
    return True


# =============================================================
# 14. CLAN LEADERBOARDS
# =============================================================

def get_top_clans_by_power(limit: int = 10) -> List[Row]:
    """Returns the top clans sorted by their overall Level and EXP."""
    with db.conn() as c:
        return c.execute(
            "SELECT k.name, k.level, k.exp, COUNT(m.user_id) as member_count "
            "FROM clans k "
            "LEFT JOIN clan_members m ON m.clan_id = k.id "
            "GROUP BY k.id "
            "ORDER BY k.level DESC, k.exp DESC, member_count DESC "
            "LIMIT ?",
            (limit,)
        ).fetchall()


def get_top_clans_by_members(limit: int = 10) -> List[Row]:
    """Returns the top clans sorted by member count."""
    with db.conn() as c:
        return c.execute(
            "SELECT k.name, COUNT(m.user_id) as member_count "
            "FROM clans k "
            "LEFT JOIN clan_members m ON m.clan_id = k.id "
            "GROUP BY k.id "
            "ORDER BY member_count DESC, k.name ASC "
            "LIMIT ?",
            (limit,)
        ).fetchall()


def get_top_clans_by_contribution(limit: int = 10) -> List[Row]:
    """Returns the top clans sorted by the total contribution of their members."""
    with db.conn() as c:
        return c.execute(
            "SELECT k.name, SUM(m.contribution) as total_contribution "
            "FROM clans k "
            "JOIN clan_members m ON m.clan_id = k.id "
            "GROUP BY k.id "
            "ORDER BY total_contribution DESC "
            "LIMIT ?",
            (limit,)
        ).fetchall()


def get_top_contributors(clan_id: int, limit: int = 10) -> List[Row]:
    """Returns the top contributing members within a specific clan."""
    with db.conn() as c:
        return c.execute(
            "SELECT p.first_name, m.contribution, m.role "
            "FROM clan_members m "
            "JOIN players p ON p.user_id = m.user_id "
            "WHERE m.clan_id = ? "
            "ORDER BY m.contribution DESC "
            "LIMIT ?",
            (clan_id, limit)
        ).fetchall()


# =============================================================
# 15. COMPREHENSIVE SELF-TEST SUITE
# =============================================================
if __name__ == "__main__":
    import os
    import sys
    
    print("==================================================")
    print("🔧 RUNNING CLANS.PY SELF-TESTS")
    print("==================================================\n")
    
    # 1. Setup Temporary DB
    TEST_DB = "test_clans_engine.sqlite"
    os.environ["DB_PATH"] = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    print("1. Initializing Test Database...")
    db.init()
    print("   ✅ DB Initialized with Clan Tables.")

    # 2. Create Test Players
    print("\n2. Creating Test Players...")
    uid_leader = 100_000_001
    uid_officer = 100_000_002
    uid_member = 100_000_003
    
    db.ensure_player(uid_leader, "Saiyan Leader", "leader")
    db.ensure_player(uid_officer, "Ninja Officer", "officer")
    db.ensure_player(uid_member, "Pirate Member", "member")
    print("   ✅ 3 Test Players Created.")

    # 3. Test Clan Creation
    print("\n3. Testing Clan Creation...")
    # Give leader some crystals to create a clan
    db.give(uid_leader, crystals=500)
    
    try:
        clan_id = create(uid_leader, "Z-Fighters")
        print(f"   ✅ Clan 'Z-Fighters' created by Leader (ID: {clan_id}).")
    except ClanError as e:
        print(f"   ❌ Failed: {e}")
        sys.exit(1)
        
    # Ensure only leader can create while already in a clan
    try:
        create(uid_leader, "Second Clan")
        print("   ❌ Error: Should not be able to create a second clan!")
    except ClanError:
        print("   ✅ Leader correctly blocked from creating a second clan.")

    # 4. Test Joining
    print("\n4. Testing Clan Joining...")
    join(uid_officer, "Z-Fighters")
    join(uid_member, "Z-Fighters")
    
    assert member_count(clan_id) == 3, "Member count should be 3"
    print("   ✅ Officer and Member successfully joined the clan.")

    # 5. Test Permissions & Roles
    print("\n5. Testing Role Management...")
    promote(uid_leader, uid_officer)
    assert _role_of(uid_officer, clan_id) == ROLE_OFFICER, "Officer role check failed"
    print("   ✅ Leader promoted Ninja Officer to Officer.")
    
    demote(uid_leader, uid_officer)
    assert _role_of(uid_officer, clan_id) == ROLE_MEMBER, "Demote failed"
    promote(uid_leader, uid_officer) # Re-promote for later tests
    print("   ✅ Leader demoted and re-promoted Officer.")

    # 6. Test Treasury & Donations
    print("\n6. Testing Clan Treasury...")
    db.give(uid_leader, yens=50000)
    add_treasure(clan_id, yens=50000, actor_id=uid_leader)
    
    m = membership(uid_leader)
    assert m["treasure_yens"] == 50000, "Vault yens should be 50000"
    print("   ✅ Leader donated 50,000 Yens to vault.")

    # 7. Test Perks
    print("\n7. Testing Clan Perks...")
    # Add crystals to vault for perk
    add_treasure(clan_id, crystals=1000, actor_id=uid_officer)
    buy_perk(uid_leader, "war_drums")
    
    perks = get_perks(clan_id)
    assert "war_drums" in perks, "Perk should be researched"
    print("   ✅ Researched 'War Drums' perk.")

    # 8. Test Clan EXP & Leveling
    print("\n8. Testing Clan Leveling...")
    needed = get_exp_needed_for_level(1)
    leveled = add_clan_exp(clan_id, needed)
    assert leveled == True, "Clan should have leveled up"
    
    clan = clan_by_id(clan_id)
    assert clan["level"] == 2, "Clan level should be 2"
    print(f"   ✅ Clan leveled up to Level 2!")

    # 9. Test Clan Raids
    print("\n9. Testing Clan Raids...")
    clan_raid_start(clan_id, "Perfect Cell", 40000, 400)
    
    st = clan_raid_state(clan_id)
    assert st["hp"] == 40000, "Raid HP mismatch"
    
    # Simulate hits
    hp_left, defeated, dmg_map, boss = clan_raid_hit(clan_id, uid_leader, 15000)
    assert hp_left == 25000, "Raid HP should be 25000"
    assert defeated == False, "Raid should not be defeated yet"
    
    hp_left, defeated, dmg_map, boss = clan_raid_hit(clan_id, uid_officer, 25000)
    assert defeated == True, "Raid should be defeated"
    print("   ✅ Clan Raid 'Perfect Cell' defeated by combined efforts.")

    # 10. Test Territory
    print("\n10. Testing Territory Capture...")
    capture_planet(uid_leader, "Earth")
    territories = list_territory(clan_id)
    assert "Earth" in territories, "Earth should be captured"
    print("   ✅ Clan captured Earth.")

    # 11. Test Announcements
    print("\n11. Testing Announcements...")
    set_announcement(uid_leader, "We are the strongest clan!")
    ann = get_announcement(clan_id)
    assert "strongest" in ann, "Announcement mismatch"
    print("   ✅ Announcement set successfully.")

    # 12. Test Missions
    print("\n12. Testing Clan Missions...")
    increment_clan_mission(clan_id, "clan_raid_10", 10)
    missions = get_clan_missions(clan_id)
    
    assert missions["clan_raid_10"]["progress"] == 10, "Mission progress should be 10"
    assert missions["clan_raid_10"]["target"] == 10, "Mission target should be 10"
    
    # Claim mission
    claimed = claim_clan_mission(uid_leader, "clan_raid_10")
    assert claimed == True, "Mission should be claimable"
    
    # Verify crystals were added
    clan = clan_by_id(clan_id)
    assert clan["treasure_crystals"] >= 500, "Mission crystals should be in vault"
    print("   ✅ Mission 'Raid Fanatics' completed and claimed.")

    # 13. Test Leaderboards
    print("\n13. Testing Leaderboards...")
    top_power = get_top_clans_by_power(10)
    top_members = get_top_clans_by_members(10)
    top_contrib = get_top_clans_by_contribution(10)
    
    assert len(top_power) > 0, "Leaderboard should not be empty"
    assert len(top_members) > 0, "Member leaderboard should not be empty"
    assert len(top_contrib) > 0, "Contribution leaderboard should not be empty"
    print("   ✅ Leaderboards generated successfully.")

    # 14. Test Leaving and Disbanding
    print("\n14. Testing Leaving Clan...")
    leave(uid_member) # Member can just leave
    assert membership(uid_member) is None, "Member should be removed"
    
    transfer_leadership(uid_leader, uid_officer)
    assert _role_of(uid_officer, clan_id) == ROLE_LEADER, "Officer should be new leader"
    
    leave(uid_leader) # Old leader can now leave safely
    print("   ✅ Members left and leadership transferred.")

    # 15. Cleanup
    print("\n==================================================")
    print("🎉 ALL CLANS.PY TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
    
    os.remove(TEST_DB)
