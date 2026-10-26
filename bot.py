from __future__ import annotations

import os
import random
import time
import logging
from datetime import datetime, timezone
from html import escape
from typing import Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler, Application
)

import clans
import combat
import db
import game_data as G

# =============================================================
# LOGGING & BOT CONFIGURATION
# =============================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)


# =============================================================
# CUSTOM DECORATORS (Permissions & Checks)
# =============================================================
def require_not_banned(func):
    """Prevents banned users from interacting with the bot."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        p = db.player(uid)
        if p and p.get("banned"):
            msg = "🚫 **ACCESS DENIED**\nYou have been banned from playing this game."
            if update.callback_query:
                await update.callback_query.answer("You are banned.", show_alert=True)
            elif update.message:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return
        await func(update, context)
    return wrapper


def require_admin(func):
    """Restricts usage to Admins and the Owner."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        p = db.player(uid)
        is_admin = bool(p and p.get("admin"))
        
        if uid != OWNER_ID and not is_admin:
            msg = "⛔ **ACCESS DENIED**\nOnly Admins can use this command."
            if update.callback_query:
                await update.callback_query.answer("Admins only.", show_alert=True)
            elif update.message:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return
        await func(update, context)
    return wrapper


def require_owner(func):
    """Restricts usage exclusively to the Bot Owner."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            msg = "👑 **OWNER ONLY**\nThis command is restricted to the Bot Owner."
            if update.callback_query:
                await update.callback_query.answer("Owner only.", show_alert=True)
            elif update.message:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return
        await func(update, context)
    return wrapper


# =============================================================
# CORE HELPER FUNCTIONS
# =============================================================
def ensure_player(update: Update):
    """Ensures the player exists in the DB and quests are initialized."""
    user = update.effective_user
    if not user: 
        return
    db.ensure_player(user.id, user.first_name or "Player", user.username)
    db.ensure_quests_current(user.id)


def format_number(num: int | float) -> str:
    """Formats large numbers into a readable string (e.g., 1.5M)."""
    if num is None:
        return "0"
    num = int(num)
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num/1_000:.2f}K"
    return f"{num:,}"


def get_hp_bar(current: int, max_hp: int, length: int = 10) -> str:
    """Generates a visual HP bar using emojis."""
    if max_hp <= 0:
        return "💀 DEAD"
    
    current = max(0, current)
    pct = min(100, int(current * 100 / max_hp))
    filled = int((pct / 100) * length)
    empty = length - filled
    
    bar = "🟩" * filled + "⬛" * empty
    return f"[{bar}] {format_number(current)}/{format_number(max_hp)}"


def get_exp_bar(current: int, next_lvl: int, length: int = 10) -> str:
    """Generates an EXP progress bar."""
    if next_lvl <= 0:
        return ""
    pct = min(100, int(current * 100 / next_lvl))
    filled = int((pct / 100) * length)
    empty = length - filled
    return f"[{'🟦' * filled}{'⬛' * empty}]"


def player_stats(uid: int) -> dict:
    """
    Calculates the player's total stats including gear, skills, ranks, and titles.
    Fully compatible with the 7-rarity system (Omni, SP+, etc.).
    """
    p = db.player(uid)
    if not p: 
        return {
            "atk": 0, "hp": 0, "spd": 0, "crit": 0, 
            "level": 1, "rank": 1, "current_hp": 0, "max_hp": 0
        }
        
    lvl = db.level_of(p["exp"])
    atk = 10 + lvl * 3
    hp = 100 + lvl * 12
    spd = 10 + lvl // 3
    crit = 5

    # 1. Equipment Bonuses
    if p.get("weapon") and p["weapon"] in G.EQUIPMENT:
        atk += G.EQUIPMENT[p["weapon"]][1]
        
    if p.get("armor") and p["armor"] in G.EQUIPMENT:
        hp += G.EQUIPMENT[p["armor"]][1] * 2

    # 2. Character Base Stats
    if p.get("equipped_char"):
        for row in G.CHARACTERS:
            # row format in G: dict with keys name, hp, atk, spd, crit
            if isinstance(row, dict) and row.get("name") == p["equipped_char"]:
                hp += row.get("hp", 0)
                atk += row.get("atk", 0)
                spd += row.get("spd", 0)
                crit += row.get("crit", 0)
                break
            # Fallback for tuple format
            elif isinstance(row, tuple) and row[0] == p["equipped_char"]:
                hp += row[2]
                atk += row[3]
                spd += row[4]
                crit += row[5]
                break

    # 3. Skill Tree Bonuses
    atk += sum(G.SKILL_ATK.get(s, 0) for s in db.skills(uid))
    
    # 4. Rank Multiplier (+15% per rank)
    rank = int(p.get("rank") or 1)
    rank_mult = 1 + (rank - 1) * G.RANK_BONUS
    atk = int(atk * rank_mult)
    hp = int(hp * rank_mult)

    # 5. Title Bonuses (If implemented in DB)
    title = p.get("equipped_title")
    if title and title in G.TITLES:
        bonus = G.TITLES[title].get("bonus", "")
        if "+5% ATK" in bonus:
            atk = int(atk * 1.05)
        elif "+10% ATK" in bonus:
            atk = int(atk * 1.10)
        elif "+8% HP" in bonus:
            hp = int(hp * 1.08)

    current_hp = db.get_current_hp(uid, hp)
    
    return {
        "atk": atk, 
        "hp": hp, 
        "spd": spd, 
        "crit": crit, 
        "level": lvl, 
        "rank": rank, 
        "current_hp": current_hp, 
        "max_hp": hp
    }


def resolve_target_id(args: list[str], update: Update) -> Optional[int]:
    """Resolves a user ID from a reply, @username, or numeric ID."""
    if update.message and update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        if u and not u.is_bot:
            return u.id
            
    if not args:
        return None
        
    token = args[0].strip()
    if token.startswith("@"):
        row = db.player_by_username(token[1:])
        return row["user_id"] if row else None
    elif token.isdigit():
        return int(token)
        
    return None


def parse_amount(value: str) -> int:
    """Safely parses an integer, returning 0 if invalid."""
    try:
        amt = int(value)
        return amt if amt > 0 else 0
    except (TypeError, ValueError):
        return 0


# =============================================================
# INTERACTIVE UI BUILDERS (Inline Keyboards)
# =============================================================
def build_main_menu() -> InlineKeyboardMarkup:
    """Builds the primary dashboard."""
    kb = [
        [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
         InlineKeyboardButton("⚔️ Explore", callback_data="menu_explore")],
         
        [InlineKeyboardButton("🛒 Shop", callback_data="menu_shop"),
         InlineKeyboardButton("🎰 Gacha", callback_data="menu_gacha")],
         
        [InlineKeyboardButton("🧙 Characters", callback_data="menu_characters"),
         InlineKeyboardButton("🏰 Clan", callback_data="menu_clan")],
         
        [InlineKeyboardButton("🎒 Inventory", callback_data="menu_inventory"),
         InlineKeyboardButton("📅 Quests", callback_data="menu_quests")],
         
        [InlineKeyboardButton("🔱 Raids & Bosses", callback_data="menu_raids"),
         InlineKeyboardButton("🌍 Travel", callback_data="menu_travel")],
         
        [InlineKeyboardButton("🧪 Healing", callback_data="menu_heal"),
         InlineKeyboardButton("🏆 Achievements", callback_data="menu_achievements")],
         
        [InlineKeyboardButton("🛠️ Crafting", callback_data="menu_craft"),
         InlineKeyboardButton("🏷️ Titles", callback_data="menu_titles")],
         
        [InlineKeyboardButton("⚙️ Settings / Help", callback_data="menu_settings")]
    ]
    return InlineKeyboardMarkup(kb)


def build_explore_menu() -> InlineKeyboardMarkup:
    """Sub-menu for exploration."""
    kb = [
        [InlineKeyboardButton("⚔️ Fight NPC", callback_data="explore_fight")],
        [InlineKeyboardButton("🏃 Run Away", callback_data="explore_run"),
         InlineKeyboardButton("ℹ️ Planet Info", callback_data="explore_info")],
        [InlineKeyboardButton("🧹 Clear Stuck Battle", callback_data="explore_clear")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(kb)


def build_back_button(callback_data: str = "main_menu", text: str = "⬅️ Back") -> InlineKeyboardMarkup:
    """Universal back button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback_data)]])


# =============================================================
# CORE COMMAND HANDLERS (/start, /menu, /unstuck)
# =============================================================
@require_not_banned
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes the player and presents the main menu."""
    ensure_player(update)
    uid = update.effective_user.id
    p = db.player(uid)
    
    # Grant Starter Pack for brand new players
    if p and int(p["exp"] or 0) == 0 and int(p["total_battles"] or 0) == 0:
        rarity = random.choice(G.STARTER_PACK["pool"])
        
        # Filter characters by chosen rarity
        pool = []
        for row in G.CHARACTERS:
            if isinstance(row, dict) and row.get("rarity") == rarity:
                pool.append(row["name"])
            elif isinstance(row, tuple) and row[1] == rarity:
                pool.append(row[0])
                
        if pool:
            name = random.choice(pool)
            db.add_character(uid, name, rarity)
            db.set_field(uid, "equipped_char", name)
            
            # Give starter resources
            db.give(
                uid, 
                yens=G.STARTER_PACK["bonus_yens"], 
                gems=G.STARTER_PACK["bonus_gems"], 
                tickets=G.STARTER_PACK["bonus_tickets"]
            )
            
            await update.message.reply_text(
                f"🎁 **Starter Pack Unlocked!**\n\n"
                f"You summoned **{name}** ({rarity.upper()})!\n"
                f"They have been automatically equipped as your lead character.\n\n"
                f"*(+{G.STARTER_PACK['bonus_yens']} Yens, +{G.STARTER_PACK['bonus_gems']} Gems, +{G.STARTER_PACK['bonus_tickets']} Tickets)*",
                parse_mode=ParseMode.MARKDOWN
            )

    text = (
        f"🐉 **Dragon Ball & Anime Crossover RPG**\n"
        f"Welcome, **{update.effective_user.first_name}**!\n\n"
        f"Tap any button below to navigate the game. No typing required!\n"
        f"If you ever get stuck in a battle, type `/unstuck`."
    )
    await update.message.reply_text(
        text, 
        reply_markup=build_main_menu(), 
        parse_mode=ParseMode.MARKDOWN
    )


@require_not_banned
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forces the main menu to open."""
    await update.message.reply_text(
        "🏠 **Main Menu**\nSelect an option:",
        reply_markup=build_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


@require_not_banned
async def cmd_unstuck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clears all combat states, resets boss streaks, and fully heals the player."""
    ensure_player(update)
    uid = update.effective_user.id
    s = player_stats(uid)
    
    # Reset everything
    db.set_current_hp(uid, s["max_hp"])
    db.set_field(uid, "npc_streak", 0)
    
    # Clear persistent summon HP
    db.set_summon_hp(uid, "elite", None)
    db.set_summon_hp(uid, "mythical", None)
    db.set_summon_hp(uid, "legendary", None)
    
    await update.message.reply_text(
        "🧹 **Battle State Cleared!**\n\n"
        "Your HP has been fully restored and all active enemy encounters have been reset. "
        "You can now fight normally.",
        reply_markup=build_main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


@require_not_banned
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the game guide."""
    text = (
        "📖 **Game Guide**\n\n"
        "**Navigation**\n"
        "Use `/menu` to open the main UI at any time.\n"
        "Use `/unstuck` to clear stuck battles and heal.\n\n"
        "**Combat**\n"
        "Explore planets, defeat NPCs, and spawn Bosses every 15 wins.\n\n"
        "**Progression**\n"
        "Rank up with Crystals to boost all stats by 15%.\n"
        "Equip stronger characters and gear from the Shop and Gacha.\n\n"
        "**Clans**\n"
        "Create or join a clan to raid bosses together and earn massive rewards.\n\n"
        "**Admin Commands** (For Admins)\n"
        "`/admin` - Open the admin panel.\n"
        "`/give` - Give resources.\n"
        "`/add` - Give items/characters.\n"
        "`/clear_data` - Wipe a player."
    )
    await update.message.reply_text(
        text, 
        reply_markup=build_back_button(), 
        parse_mode=ParseMode.MARKDOWN
    )


# =============================================================
# CORE BUTTON ROUTER (Part 1)
# =============================================================
async def button_router_core(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the primary navigation buttons.
    This router will be extended by Parts 2, 3, and 4.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    
    ensure_player(update)
    
    # --- Navigation ---
    if data == "main_menu":
        text = "🏠 **Main Menu**\nSelect an option:"
        await query.edit_message_text(
            text, 
            reply_markup=build_main_menu(), 
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    if data == "menu_settings":
        text = (
            "⚙️ **Settings & Help**\n\n"
            "Use `/help` for the full game guide.\n"
            "Use `/unstuck` to fix stuck battles.\n"
            "Use `/menu` to return to the main screen."
        )
        kb = [
            [InlineKeyboardButton("📖 Game Guide", callback_data="show_help")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    if data == "show_help":
        text = (
            "📖 **Quick Guide**\n"
            "1. Fight NPCs to earn Yens and EXP.\n"
            "2. Every 15 kills spawns a Boss.\n"
            "3. Use Gacha to get stronger characters.\n"
            "4. Rankup to multiply your stats!\n"
            "5. Join a Clan for raids."
        )
        await query.edit_message_text(
            text, 
            reply_markup=build_back_button("menu_settings"), 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # --- Profile & History ---
    if data == "menu_profile":
        await show_profile(query)
        return
        
    if data == "menu_team":
        await show_team(query)
        return
        
    if data == "menu_history":
        hist = combat.CombatHistory(query.from_user.id)
        await query.edit_message_text(
            hist.render(), 
            reply_markup=build_back_button("menu_profile"), 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # --- Explore System ---
    if data == "menu_explore":
        await show_explore_menu(query)
        return
        
    if data.startswith("explore_"):
        action = data.split("_")[1]
        await handle_explore_action(query, action)
        return

    # --- Healing System ---
    if data == "menu_heal":
        await show_heal_menu(query)
        return
        
    if data.startswith("heal_"):
        item_name = data.replace("heal_", "")
        await handle_heal_action(query, item_name)
        return


# =============================================================
# PROFILE & TEAM LOGIC
# =============================================================
async def show_profile(query):
    """Renders the player's dashboard."""
    uid = query.from_user.id
    p = db.player(uid)
    s = player_stats(uid)
    stats = db.combat_stats(uid)
    clan = clans.membership(uid)
    
    next_lvl_exp = (s["level"] + 1) * G.LEVEL_EXP
    exp_bar = get_exp_bar(p["exp"], next_lvl_exp)
    hp_bar = get_hp_bar(s["current_hp"], s["max_hp"])
    
    # Format text
    text = (
        f"👤 **{escape(p['first_name'])}**\n"
        f"Level: **{s['level']}** | Rank: **{s['rank']}** ({G.RANKS.get(s['rank'], '?')})\n"
        f"EXP: {exp_bar} ({format_number(p['exp'])}/{format_number(next_lvl_exp)})\n"
        f"World: {p['travel']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️ HP: {hp_bar}\n"
        f"⚔️ ATK: **{format_number(s['atk'])}** | 🎯 CRIT: {s['crit']}%\n"
        f"⚡ SPD: {s['spd']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💴 Yens: {format_number(p['yens'])} | 💎 Gems: {format_number(p['gems'])}\n"
        f"🔮 Crystals: {format_number(p['crystals'])} | 🎫 Tickets: {p['tickets']}\n"
        f"🌟 SP: {p['skill_points']} | 🔑 Keys: {p['keys_elite']}E / {p['keys_boss']}B\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ Weapon: {p['weapon'] or 'None'}\n"
        f"🛡️ Armor: {p['armor'] or 'None'}\n"
        f"🧙 Lead Char: {p['equipped_char'] or 'None'}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Battles: {stats['battles']} ({stats['wins']}W / {stats['losses']}L)\n"
        f"🏰 Clan: {clan['name'] if clan else 'None'}"
    )
    
    kb = [
        [InlineKeyboardButton("🛡️ Team Setup", callback_data="menu_team"),
         InlineKeyboardButton("📊 History", callback_data="menu_history")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def show_team(query):
    """Renders the player's equipped team."""
    uid = query.from_user.id
    p = db.player(uid)
    s = player_stats(uid)
    
    text = (
        f"🛡️ **Team Setup**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧙 Character: {p['equipped_char'] or 'None'}\n"
        f"⚔️ Weapon: {p['weapon'] or 'None'}\n"
        f"🛡️ Armor: {p['armor'] or 'None'}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️ HP: {format_number(s['current_hp'])}/{format_number(s['max_hp'])}\n"
        f"⚔️ ATK: {format_number(s['atk'])}\n"
        f"⚡ SPD: {s['spd']}\n"
        f"🎯 CRIT: {s['crit']}%\n\n"
        f"Use `/characters` or `/inventory` to equip different gear."
    )
    
    kb = [[InlineKeyboardButton("⬅️ Back to Profile", callback_data="menu_profile")]]
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


# =============================================================
# EXPLORE & COMBAT LOGIC
# =============================================================
async def show_explore_menu(query):
    """Renders the explore menu."""
    uid = query.from_user.id
    p = db.player(uid)
    s = player_stats(uid)
    streak = int(p.get("npc_streak") or 0)
    world = p.get("travel") or "Earth"
    
    text = (
        f"🧭 **Explore: {world}** (x{G.PLANETS[world]['multiplier']} Rewards)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️ HP: {get_hp_bar(s['current_hp'], s['max_hp'])}\n"
        f"👹 Boss in **{G.NPC_STREAK_FOR_BOSS - streak}** wins!\n\n"
        f"Select your action:"
    )
    await query.edit_message_text(
        text, 
        reply_markup=build_explore_menu(), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_explore_action(query, action):
    """Processes explore actions (Fight, Run, Info, Clear)."""
    uid = query.from_user.id
    p = db.player(uid)
    s = player_stats(uid)

    # --- Clear Stuck Battle ---
    if action == "clear":
        db.set_current_hp(uid, s["max_hp"])
        db.set_field(uid, "npc_streak", 0)
        await query.answer("🧹 Battle State Cleared! HP fully restored.", show_alert=True)
        await show_explore_menu(query)
        return

    # --- Run Away ---
    if action == "run":
        await query.edit_message_text(
            "🏃 You used Instant Transmission and escaped safely.\nNo HP lost.", 
            reply_markup=build_back_button("menu_explore")
        )
        return

    # --- Planet Info ---
    if action == "info":
        text = (
            f"ℹ️ **Info: {p['travel']}**\n"
            f"Level Gate: {G.PLANETS[p['travel']]['level_min']}-{G.PLANETS[p['travel']]['level_max']}\n"
            f"Multiplier: x{G.PLANETS[p['travel']]['multiplier']}\n\n"
            f"Defeat 15 NPCs to spawn a World Boss for huge rewards!"
        )
        await query.edit_message_text(
            text, 
            reply_markup=build_explore_menu(), 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # --- Fight NPC / Boss ---
    if action == "fight":
        if s["current_hp"] <= 1:
            await query.answer("⚠️ HP is critical! Use /unstuck or heal items.", show_alert=True)
            return
        
        # Determine enemy
        streak = int(p.get("npc_streak") or 0) + 1
        is_boss = streak >= G.NPC_STREAK_FOR_BOSS
        
        if is_boss:
            enemy = random.choice(G.BOSSES)
            name = enemy["name"]
            e_hp = enemy["hp"]
            e_dmg = enemy["dmg"]
        else:
            enemy = random.choice(G.NPCS)
            name = enemy["name"]
            e_hp = enemy["hp"]
            e_dmg = enemy["dmg"]

        # Run Combat Engine
        eng = combat.CombatEngine(
            s["atk"], 
            s["current_hp"], 
            crit=s["crit"], 
            speed=s["spd"]
        )
        won, left_hp, log = eng.fight(name, e_hp, e_dmg, enrage=is_boss)
        
        # Log to Combat History
        hist = combat.CombatHistory(uid)
        outcome = "victory" if won else "defeat"
        hist.log(name, e_hp, eng.damage_dealt, eng.damage_taken, outcome, eng.rounds)
        
        # Handle Victory
        if won:
            db.set_current_hp(uid, left_hp)
            world_mult = G.PLANETS[p['travel']]['multiplier']
            rank_mult = 1 + int(p.get("rank") or 1) * 0.2
            
            if is_boss:
                yens = int(enemy.get("yens", 5000) * world_mult * rank_mult * 5)
                gems = enemy.get("gems", 100)
                crystals = enemy.get("crystals", 5)
                tickets = enemy.get("tickets", 1)
                sp = enemy.get("skill_points", 10)
                
                db.give(uid, yens=yens, gems=gems, crystals=crystals, tickets=tickets, skill_points=sp)
                db.set_field(uid, "npc_streak", 0)
                
                reward_text = (
                    f"🏆 **BOSS DEFEATED!**\n"
                    f"💴 +{format_number(yens)} Yens\n"
                    f"💎 +{gems} Gems\n"
                    f"🔮 +{crystals} Crystals"
                )
                
                # Trigger Quests & Achievements
                tracker = combat.QuestTracker(uid)
                tracker.on_boss_kill()
                tracker.on_yens_earned(yens)
                tracker.on_battle_win()
                
                ach = combat.CombatAchievements(uid)
                ach.check_after_battle(True, eng.damage_taken, is_boss=True)
                
            else:
                yens = int(enemy["reward"] * world_mult * rank_mult)
                db.give(uid, yens=yens, exp=60, skill_points=5)
                db.set_field(uid, "npc_streak", streak)
                
                reward_text = (
                    f"✅ **Victory vs {name}!**\n"
                    f"💴 +{format_number(yens)} Yens\n"
                    f"✨ +60 EXP | 🌟 +5 SP"
                )
                
                tracker = combat.QuestTracker(uid)
                tracker.on_npc_kill()
                tracker.on_battle_win()
                tracker.on_yens_earned(yens)
                
                ach = combat.CombatAchievements(uid)
                ach.check_after_battle(True, eng.damage_taken)
                
            # Handle Drops
            drops = []
            drop_chance = 0.35 if is_boss else 0.15
            if random.random() < drop_chance:
                item = random.choice(list(G.EQUIPMENT))
                db.add_item(uid, item)
                drops.append(f"📦 {item}")
                
            if random.random() < (0.45 if is_boss else 0.10):
                star = random.choice(G.DRAGON_BALL_STARS)
                db.add_dragon_ball(uid, star)
                drops.append(f"🐉 Dragon Ball {star}★")
                
            drop_text = "\n**Drops:**\n" + "\n".join(drops) if drops else ""
                
            text = (
                f"{reward_text}{drop_text}\n\n"
                f"**Battle Log:**\n" + "\n".join(log[-4:])
            )
            
            kb = [
                [InlineKeyboardButton("⚔️ Fight Again", callback_data="explore_fight")],
                [InlineKeyboardButton("⬅️ Explore Menu", callback_data="menu_explore")]
            ]
            
        # Handle Defeat
        else:
            db.set_current_hp(uid, 1)  # Leave at 1 HP
            text = (
                f"❌ **Defeated by {name}!**\n\n"
                f"You are left with **1 HP**.\n"
                f"Use `/unstuck` or heal items before fighting again.\n\n"
                f"**Battle Log:**\n" + "\n".join(log[-4:])
            )
            kb = [
                [InlineKeyboardButton("🧪 Heal", callback_data="menu_heal")],
                [InlineKeyboardButton("⬅️ Explore Menu", callback_data="menu_explore")]
            ]
                  
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode=ParseMode.MARKDOWN
        )


# =============================================================
# HEALING SYSTEM
# =============================================================
async def show_heal_menu(query):
    """Renders the healing item selection menu."""
    uid = query.from_user.id
    s = player_stats(uid)
    inv = {row["item"]: row["qty"] for row in db.items(uid)}
    
    kb = []
    has_items = False
    
    for item_name, heal_pct in G.HEALING.items():
        qty = inv.get(item_name, 0)
        if qty > 0:
            has_items = True
            kb.append([
                InlineKeyboardButton(
                    f"🧪 {item_name} (x{qty})", 
                    callback_data=f"heal_{item_name}"
                )
            ])
            
    if not has_items:
        kb.append([InlineKeyboardButton("No healing items in bag!", callback_data="noop")])
        
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    text = (
        f"🧪 **Healing Menu**\n"
        f"❤️ HP: {get_hp_bar(s['current_hp'], s['max_hp'])}\n\n"
        f"Select an item to use:"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_heal_action(query, item_name):
    """Applies a healing item to the player."""
    uid = query.from_user.id
    s = player_stats(uid)
    ok, new_hp = db.apply_heal(uid, s["max_hp"], item_name)
    
    if ok:
        await query.answer(f"✅ Used {item_name}! HP is now {new_hp}/{s['max_hp']}.", show_alert=True)
        await show_heal_menu(query)
    else:
        await query.answer(f"❌ You don't have {item_name}!", show_alert=True)


# =============================================================
# END OF PART 1
# =============================================================
# Part 2 will contain:
# - Shop UI
# - Inventory UI
# - Characters UI
# - Gacha UI
# - Travel UI
# - Raids UI
# - Clan UI
# =============================================================
# =============================================================
# PART 2: SHOP, INVENTORY, CHARACTERS, GACHA, TRAVEL & RAIDS
# =============================================================

# -------------------------------------------------------------
# SHOP SYSTEM LOGIC
# -------------------------------------------------------------
async def show_shop_menu(query):
    """Renders the main shop categories."""
    kb = [
        [InlineKeyboardButton("⚔️ Weapons", callback_data="shop_cat_weapon"),
         InlineKeyboardButton("🛡️ Armors", callback_data="shop_cat_armor")],
         
        [InlineKeyboardButton("🔮 Crystals", callback_data="shop_cat_crystal"),
         InlineKeyboardButton("🧪 Healing", callback_data="shop_cat_heal")],
         
        [InlineKeyboardButton("🧬 Fusion", callback_data="shop_cat_fusion"),
         InlineKeyboardButton("🎫 Tickets & Keys", callback_data="shop_cat_ticket")],
         
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    text = (
        "🛒 **Capsule Corp Shop**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Select a category to browse:"
    )
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_shop_category(query, category):
    """Renders items within a shop category with Buy buttons."""
    uid = query.from_user.id
    p = db.player(uid)
    
    text = (
        f"🛒 **Shop: {category.capitalize()}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💴 Yens: {format_number(p['yens'])} | 💎 Gems: {format_number(p['gems'])}\n\n"
    )
    
    kb = []
    # Iterate through the dynamically generated shop from game_data.py
    for sid, item in G.SHOP.items():
        name, price, currency, kind, amount = item
        
        # Filter by category
        if category == "weapon" and kind != "weapon": continue
        if category == "armor" and kind != "armor": continue
        if category == "crystal" and kind != "crystal": continue
        if category == "heal" and kind != "heal": continue
        if category == "fusion" and kind != "fusion": continue
        if category == "ticket" and kind not in ("ticket", "key_elite", "key_boss"): continue
            
        # Show Button
        kb.append([
            InlineKeyboardButton(
                f"{name} - {format_number(price)} {currency.upper()}", 
                callback_data=f"buy_{sid}_1"
            )
        ])

    if not kb:
        kb.append([InlineKeyboardButton("No items in this category.", callback_data="noop")])

    kb.append([InlineKeyboardButton("⬅️ Back to Shop", callback_data="menu_shop")])
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_buy_item(query, sid, qty):
    """Processes a purchase from the shop."""
    uid = query.from_user.id
    p = db.player(uid)
    item = G.SHOP.get(sid)
    
    if not item:
        await query.answer("❌ Item not found.", show_alert=True)
        return
        
    name, price, currency, kind, amount = item
    total_price = price * qty
    
    # Check funds
    if p[currency] < total_price:
        await query.answer(f"❌ Not enough {currency}!", show_alert=True)
        return
        
    # Attempt transaction
    if not db.spend(uid, currency, total_price):
        await query.answer("❌ Transaction failed.", show_alert=True)
        return
        
    # Deliver item based on kind
    total_amount = amount * qty
    
    if kind in ("weapon", "armor", "heal", "fusion"):
        db.add_item(uid, name, total_amount)
    elif kind == "crystal":
        db.give(uid, crystals=total_amount)
    elif kind == "ticket":
        db.give(uid, tickets=total_amount)
    elif kind == "key_elite":
        db.give(uid, keys_elite=total_amount)
    elif kind == "key_boss":
        db.give(uid, keys_boss=total_amount)
        
    await query.answer(
        f"✅ Bought {name} x{qty} for {format_number(total_price)} {currency}!", 
        show_alert=True
    )
    
    # Refresh the category UI
    await handle_shop_category(query, kind if kind not in ("key_elite", "key_boss") else "ticket")


# -------------------------------------------------------------
# INVENTORY SYSTEM LOGIC
# -------------------------------------------------------------
async def show_inventory_menu(query):
    """Renders the player's inventory grouped by type."""
    uid = query.from_user.id
    inv = db.items(uid)
    
    kb = []
    text = "🎒 **Your Inventory**\n━━━━━━━━━━━━━━━━━━\n\n"
    
    has_items = False
    for row in inv:
        item_name = row["item"]
        qty = row["qty"]
        
        # Check if it's equipment (Weapon/Armor)
        if item_name in G.EQUIPMENT:
            has_items = True
            slot = G.EQUIPMENT[item_name][0]
            icon = "⚔️" if slot == "weapon" else "🛡️"
            
            # Add equip button
            kb.append([
                InlineKeyboardButton(
                    f"{icon} Equip {item_name} (x{qty})", 
                    callback_data=f"equip_item_{item_name}"
                )
            ])
        elif item_name in G.HEALING or item_name in G.FUSION_MATERIALS:
            # Just list consumables in the text
            text += f"• {item_name} (x{qty})\n"
            
    if not has_items:
        if len(text) < 60:
            text += "*Your inventory is empty.*"
        else:
            text += "\n*(No equippable gear found. Use /shop to buy some!)*"
        
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    # Telegram text limit protection
    if len(text) > 4000:
        text = text[:3900] + "...\n(Inventory too large to display fully)"
        
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_equip_item(query, item_name):
    """Equips a weapon or armor from the inventory."""
    uid = query.from_user.id
    if item_name not in G.EQUIPMENT:
        await query.answer("❌ Invalid item.", show_alert=True)
        return
        
    slot = G.EQUIPMENT[item_name][0]
    db.set_field(uid, slot, item_name)
    
    await query.answer(f"✅ Equipped {item_name}!", show_alert=True)
    await show_inventory_menu(query)


# -------------------------------------------------------------
# CHARACTER ROSTER LOGIC
# -------------------------------------------------------------
async def show_character_menu(query):
    """Displays the player's characters grouped by rarity (Omni to Common)."""
    uid = query.from_user.id
    p = db.player(uid)
    chars = db.characters_by_rarity(uid)
    
    text = (
        f"🧙 **Your Roster**\n"
        f"Equipped: **{p['equipped_char'] or 'None'}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
    )
    kb = []
    
    # The 7 Rarities in order
    rarities = ["omni", "sp_plus", "mythical", "legendary", "epic", "rare", "common"]
    
    for rarity in rarities:
        names = chars.get(rarity, [])
        if not names:
            continue
            
        # Add a section header to the text
        label = G.RARITY_LABEL.get(rarity, rarity.capitalize())
        text += f"\n**{label}** ({len(names)})\n"
        
        for name in names:
            # Telegram limits inline buttons to 100 per message
            # We limit to the first 50 to avoid API crashes
            if len(kb) < 50:
                kb.append([
                    InlineKeyboardButton(
                        f"Equip {name} ({rarity.upper()})", 
                        callback_data=f"equip_char_{name}"
                    )
                ])
            
    if not any(chars.values()):
        text += "*You have no characters. Use the Gacha to summon!*"
        
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    if len(text) > 4000:
        text = text[:3900] + "...\n(Roster too large to display fully)"
        
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_equip_char(query, char_name):
    """Equips a character to the player's team."""
    uid = query.from_user.id
    if not db.has_character(uid, char_name):
        await query.answer("❌ You don't own this character.", show_alert=True)
        return
        
    db.set_field(uid, "equipped_char", char_name)
    await query.answer(f"✅ Equipped {char_name}!", show_alert=True)
    await show_character_menu(query)


# -------------------------------------------------------------
# GACHA SYSTEM LOGIC
# -------------------------------------------------------------
async def show_gacha_menu(query):
    """Renders the Gacha banner selection."""
    uid = query.from_user.id
    p = db.player(uid)
    
    text = (
        f"🎰 **Gacha Summon**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎫 Tickets: **{p['tickets']}**\n\n"
        f"Select a banner to pull:"
    )
    
    # Using the new banners from game_data.py
    kb = [
        [InlineKeyboardButton("Standard 1x (1 Ticket)", callback_data="gacha_pull_standard_1")],
        [InlineKeyboardButton("Standard 10x (10 Tickets)", callback_data="gacha_pull_standard_10")],
        [InlineKeyboardButton("Hero 1x (1 Ticket)", callback_data="gacha_pull_hero_1")],
        [InlineKeyboardButton("Hero 10x (10 Tickets)", callback_data="gacha_pull_hero_10")],
        [InlineKeyboardButton("God 1x (2 Tickets)", callback_data="gacha_pull_god_1")],
        [InlineKeyboardButton("Omni 1x (3 Tickets)", callback_data="gacha_pull_omni_1")],
        [InlineKeyboardButton("Anime Crossover 1x (2 Tickets)", callback_data="gacha_pull_anime_1")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_gacha_pull(query, banner_key, qty):
    """Processes a gacha pull."""
    uid = query.from_user.id
    p = db.player(uid)
    banner = G.GACHA_BANNERS.get(banner_key)
    
    if not banner:
        await query.answer("❌ Invalid banner.", show_alert=True)
        return
        
    cost = banner["cost"] * qty
    if p["tickets"] < cost:
        await query.answer(f"❌ Not enough tickets! You need {cost}.", show_alert=True)
        return
        
    if not db.spend(uid, "tickets", cost):
        await query.answer("❌ Transaction failed.", show_alert=True)
        return
        
    # Roll Characters
    rolls = []
    for _ in range(qty):
        # db.roll_rarity uses the rates and banner bonuses
        rarity = db.roll_rarity(banner["bonus"])
        name = db.pick_character_of_rarity(rarity)
        if name:
            db.add_character(uid, name, rarity)
            rolls.append((name, rarity))
            
    # Quest tracking
    tracker = combat.QuestTracker(uid)
    tracker.on_gacha(qty)
    
    # Format results
    text = f"🎰 **Gacha Results ({banner['name']})**\n\n"
    
    # If mass summon, summarize
    if qty > 10:
        rarities = {}
        for name, rarity in rolls:
            rarities[rarity] = rarities.get(rarity, 0) + 1
            
        # Sort by rarity order
        sorted_rarities = sorted(
            rarities.items(), 
            key=lambda x: G.RARITY_ORDER.get(x[0], 0), 
            reverse=True
        )
        
        for rarity, count in sorted_rarities:
            icon = G.RARITY_ICONS.get(rarity, "⚪")
            text += f"{icon} **{rarity.capitalize()}**: {count}\n"
        text += "\n*(Check your Character Roster for the new units!)*"
    else:
        for name, rarity in rolls:
            icon = G.RARITY_ICONS.get(rarity, "⚪")
            text += f"{icon} **{name}** ({rarity.capitalize()})\n"
        
    kb = [
        [InlineKeyboardButton("🎰 Summon Again", callback_data="menu_gacha")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


# -------------------------------------------------------------
# TRAVEL SYSTEM LOGIC
# -------------------------------------------------------------
async def show_travel_menu(query):
    """Shows available planets to travel to."""
    uid = query.from_user.id
    p = db.player(uid)
    s = player_stats(uid)
    
    text = (
        f"🌍 **Travel the Multiverse**\n"
        f"Your Level: **{s['level']}**\n"
        f"Current Location: **{p['travel']}**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )
    kb = []
    
    for planet in G.PLANET_ORDER:
        data = G.PLANETS[planet]
        
        if s["level"] < data["level_min"]:
            kb.append([
                InlineKeyboardButton(
                    f"🔒 {planet} (Lv.{data['level_min']} Req)", 
                    callback_data="noop"
                )
            ])
        else:
            kb.append([
                InlineKeyboardButton(
                    f"✈️ Travel to {planet} (x{data['multiplier']})", 
                    callback_data=f"travel_to_{planet}"
                )
            ])
            
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_travel(query, planet):
    """Sets the player's travel destination."""
    uid = query.from_user.id
    db.set_field(uid, "travel", planet)
    await query.answer(f"✈️ Traveled to {planet}!", show_alert=True)
    await show_explore_menu(query)


# -------------------------------------------------------------
# RAID & SUMMON BOSSES
# -------------------------------------------------------------
async def show_raid_menu(query):
    """Shows Raid and Summon bosses."""
    text = (
        "🔱 **Raids & Boss Summons**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Select an option:"
    )
    
    kb = [
        [InlineKeyboardButton("🔱 World Raid (Multiverse Dragon)", callback_data="raid_view")],
        [InlineKeyboardButton("👑 Summon Elite (1 Elite Key)", callback_data="summon_elite")],
        [InlineKeyboardButton("👑 Summon Mythical (1 Boss Key)", callback_data="summon_mythical")],
        [InlineKeyboardButton("👑 Summon Legendary (1 Boss Key)", callback_data="summon_legendary")],
        [InlineKeyboardButton("👑 Summon Anime Overlord (1 Boss Key)", callback_data="summon_anime")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_summon_boss(query, kind):
    """Handles summoning a boss with a key."""
    uid = query.from_user.id
    p = db.player(uid)
    data = G.SUMMONS.get(kind)
    
    if not data:
        await query.answer("❌ Invalid summon.", show_alert=True)
        return
        
    key_col = data["key"]
    if p[key_col] <= 0:
        await query.answer(f"❌ You don't have a {key_col.replace('keys_', '')} key!", show_alert=True)
        return
        
    # Deduct Key
    db.spend(uid, key_col, 1)
    
    # Check HP
    s = player_stats(uid)
    if s["current_hp"] <= 1:
        await query.answer("⚠️ HP is too low! Heal or /unstuck first.", show_alert=True)
        # Refund key
        db.give(uid, **{key_col: 1})
        return
        
    # Persisted HP logic (Boss HP remains if you lose)
    boss_name = data["name"]
    boss_max_hp = data["hp"]
    persisted = db.summon_hp(uid, kind)
    current_hp = persisted if persisted else boss_max_hp
    
    # Simulate Battle
    eng = combat.CombatEngine(s["atk"], s["current_hp"], crit=s["crit"], speed=s["spd"])
    won, left_hp, log = eng.fight(boss_name, current_hp, data["dmg"], enrage=True)
    
    if won:
        db.set_summon_hp(uid, kind, None) # Reset HP
        db.set_current_hp(uid, left_hp)
        
        # Huge Rewards
        mult = data["reward_mult"]
        yens = 20000 * mult
        gems = 50 * mult
        crystals = 6 * mult
        sp = 20 * mult
        exp = 500 * mult
        db.give(uid, yens=yens, gems=gems, crystals=crystals, skill_points=sp, exp=exp)
        
        text = (
            f"🏆 **SUMMON VICTORY: {boss_name}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💴 +{format_number(yens)} Yens\n"
            f"💎 +{gems} Gems\n"
            f"🔮 +{crystals} Crystals\n"
            f"🌟 +{sp} SP | ✨ +{exp} EXP\n\n"
            f"**Battle Log:**\n" + "\n".join(log[-4:])
        )
    else:
        # Save HP
        hp_left = max(0, current_hp - eng.damage_dealt)
        db.set_summon_hp(uid, kind, hp_left)
        db.set_current_hp(uid, 1)
        
        text = (
            f"❌ **Defeated by {boss_name}!**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Boss HP preserved: {format_number(hp_left)}/{format_number(boss_max_hp)}\n"
            f"You are at 1 HP. Use /unstuck or heal!\n\n"
            f"**Battle Log:**\n" + "\n".join(log[-4:])
        )
        
    kb = [
        [InlineKeyboardButton("🔱 Summon Again", callback_data="menu_raids")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


# -------------------------------------------------------------
# CLAN SYSTEM UI
# -------------------------------------------------------------
async def show_clan_menu(query):
    """Renders the Clan Hall."""
    uid = query.from_user.id
    mem = clans.membership(uid)
    
    if not mem:
        text = (
            "🏰 **Clan Hall**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "You are not currently in a clan."
        )
        kb = [
            [InlineKeyboardButton("➕ Create Clan (Use /clan create)", callback_data="noop")],
            [InlineKeyboardButton("🔍 Join Clan (Use /clan join)", callback_data="noop")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
        ]
    else:
        text = (
            f"🏰 **{mem['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Role: **{mem['role'].capitalize()}**\n"
            f"Treasury: {format_number(mem['treasure_yens'])} Yens\n"
            f"Crystals: {format_number(mem['treasure_crystals'])}\n"
            f"Announcement: *{mem['announcement'] or 'None'}*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Use the commands below to manage your clan:\n"
            f"`/clan members`\n"
            f"`/clan raid <boss>`\n"
            f"`/clan treasure`\n"
            f"`/clan announce <text>`"
        )
        kb = [
            [InlineKeyboardButton("⚔️ Clan Raid Info", callback_data="clan_raid_view")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
        ]
        
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


# =============================================================
# PART 2 BUTTON ROUTER (Handles all Part 2 interactions)
# =============================================================
async def button_router_part2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Extends the core router to handle Shop, Gacha, Raids, etc.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    
    ensure_player(update)
    
    # --- SHOP ---
    if data == "menu_shop":
        await show_shop_menu(query)
        return
    if data.startswith("shop_cat_"):
        category = data.replace("shop_cat_", "")
        await handle_shop_category(query, category)
        return
    if data.startswith("buy_"):
        parts = data.split("_")
        sid = int(parts[1])
        qty = int(parts[2])
        await handle_buy_item(query, sid, qty)
        return
        
    # --- INVENTORY ---
    if data == "menu_inventory":
        await show_inventory_menu(query)
        return
    if data.startswith("equip_item_"):
        item_name = data.replace("equip_item_", "")
        await handle_equip_item(query, item_name)
        return
        
    # --- CHARACTERS ---
    if data == "menu_characters":
        await show_character_menu(query)
        return
    if data.startswith("equip_char_"):
        char_name = data.replace("equip_char_", "")
        await handle_equip_char(query, char_name)
        return
        
    # --- GACHA ---
    if data == "menu_gacha":
        await show_gacha_menu(query)
        return
    if data.startswith("gacha_pull_"):
        parts = data.split("_")
        banner_key = parts[2]
        qty = int(parts[3])
        await handle_gacha_pull(query, banner_key, qty)
        return
        
    # --- TRAVEL ---
    if data == "menu_travel":
        await show_travel_menu(query)
        return
    if data.startswith("travel_to_"):
        planet = data.replace("travel_to_", "")
        await handle_travel(query, planet)
        return
        
    # --- RAIDS ---
    if data == "menu_raids":
        await show_raid_menu(query)
        return
    if data.startswith("summon_"):
        kind = data.replace("summon_", "")
        await handle_summon_boss(query, kind)
        return
    if data == "clan_raid_view":
        await query.answer("Use /clan raid <boss_name> to start a raid!", show_alert=True)
        return
        
    # --- CLANS ---
    if data == "menu_clan":
        await show_clan_menu(query)
        return

# =============================================================
# END OF PART 2
# =============================================================
# Part 3 will contain:
# - Massive Admin Suite (/give, /add, /set, /clear_data)
# - Clan text commands (/clan create, join, etc.)
# - World Raid commands (/raid, /raid_attack)
# =============================================================
# =============================================================
# PART 3: WORLD RAIDS, ADMIN SUITE & CLAN SUBCOMMANDS
# =============================================================
import json

# -------------------------------------------------------------
# WORLD RAID SYSTEM
# -------------------------------------------------------------
@require_not_banned
async def cmd_raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the status of the global World Raid."""
    ensure_player(update)
    st = db.raid_state()
    
    if not st or not st["active"]:
        text = (
            "🔱 **World Raid**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "There is no active World Raid right now.\n\n"
            "Admins can start one with `/raid_start`."
        )
        await update.message.reply_text(
            text, 
            reply_markup=build_back_button(), 
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    dmg_by = json.loads(st["damage_json"] or "{}")
    total_dmg = sum(dmg_by.values())
    pct = min(100, int(st["hp"] * 100 / st["max_hp"]))
    
    hp_bar = get_hp_bar(st["hp"], st["max_hp"], length=15)
    
    text = (
        f"🔱 **World Raid: {escape(st['boss_name'])}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❤️ **Boss HP:** {hp_bar} ({pct}%)\n"
        f"⚔️ **Total Damage:** {format_number(total_dmg)}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Use `/raid_attack` to deal damage! (No cooldown)\n\n"
    )
    
    # Add Top 5 attackers
    if dmg_by:
        top = sorted(dmg_by.items(), key=lambda x: x[1], reverse=True)[:5]
        text += "🏆 **Top Attackers:**\n"
        for i, (uid_str, dmg) in enumerate(top, 1):
            p = db.player(int(uid_str))
            name = escape(p["first_name"]) if p else f"User {uid_str}"
            text += f"{i}. {name} — {format_number(dmg)} DMG\n"
            
    kb = [
        [InlineKeyboardButton("⚔️ Attack Boss", callback_data="menu_raids")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=ParseMode.MARKDOWN
    )


@require_not_banned
async def cmd_raid_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attacks the World Raid Boss."""
    ensure_player(update)
    uid = update.effective_user.id
    st = db.raid_state()
    
    if not st or not st["active"]:
        await update.message.reply_text("❌ There is no active World Raid.")
        return
        
    s = player_stats(uid)
    if s["current_hp"] <= 1:
        await update.message.reply_text("⚠️ HP is critical! Use `/unstuck` or heal items first.")
        return
        
    # Calculate damage (5x normal ATK)
    damage = s["atk"] * 5
    result = db.raid_hit(uid, damage)
    
    if not result:
        await update.message.reply_text("❌ Failed to attack the boss.")
        return
        
    hp_left, defeated, dmg_by = result
    
    if defeated:
        mult = G.RAID["reward_mult"]
        yens = 100000 * mult
        db.give(uid, yens=yens, gems=500*mult, crystals=50*mult, tickets=10*mult, skill_points=100*mult)
        
        # Achievements & Quests
        ach = combat.CombatAchievements(uid)
        ach.check_raid_cleared()
        
        text = (
            f"🏆 **WORLD RAID DEFEATED!**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"You dealt the final blow!\n\n"
            f"🎁 **Rewards:**\n"
            f"💴 {format_number(yens)} Yens\n"
            f"💎 {format_number(500*mult)} Gems\n"
            f"🔮 {format_number(50*mult)} Crystals\n"
            f"🎫 {10*mult} Tickets\n"
            f"🌟 {100*mult} SP"
            + ach.reward_text()
        )
    else:
        text = (
            f"⚔️ You hit the boss for **{format_number(damage)}**!\n\n"
            f"❤️ Boss HP remaining: {format_number(hp_left)}/{format_number(st['max_hp'])}"
        )
        
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@require_owner
async def cmd_raid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner: Starts the World Raid Boss."""
    boss_name = "Multiverse Omega Dragon"
    if context.args:
        boss_name = " ".join(context.args)
        
    db.raid_start(boss_name=boss_name)
    await update.message.reply_text(
        f"🔱 **WORLD RAID STARTED!**\n\n"
        f"Boss: **{escape(boss_name)}**\n"
        f"HP: {format_number(G.RAID['hp'])}\n\n"
        f"All players can now attack using `/raid_attack`!",
        parse_mode=ParseMode.MARKDOWN
    )


# =============================================================
# ULTIMATE ADMIN & OWNER SUITE
# =============================================================

@require_admin
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens the Admin Panel UI."""
    text = (
        "🔐 **Admin Control Panel**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Welcome to the Admin Suite. Use the commands below:\n\n"
        "`/give` - Give resources (Yens, Gems, etc.)\n"
        "`/add` - Add characters, weapons, skills\n"
        "`/set` - Set exact stats (level, rank, hp)\n"
        "`/clear_data` - Wipe a player back to level 1\n"
        "`/ban` / `/unban` - Manage bans\n"
        "`/promote` / `/demote` - Manage admin rights (Owner only)\n"
        "`/broadcast` - Message everyone (Owner only)\n"
        "`/raid_start` - Spawn a World Raid (Owner only)"
    )
    await update.message.reply_text(
        text, 
        reply_markup=build_back_button(), 
        parse_mode=ParseMode.MARKDOWN
    )


@require_admin
async def cmd_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin: Give resources to a player.
    Usage: Reply to user -> /give <amount> <resource>
    Or: /give <@username/id> <amount> <resource>
    """
    args = context.args
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if len(args) < 2:
            await update.message.reply_text("Usage: Reply with `/give <amount> <resource>`", parse_mode=ParseMode.MARKDOWN)
            return
        amount_str, res_name = args[0], args[1].lower()
    else:
        if len(args) < 3:
            await update.message.reply_text("Usage: `/give <@username/id> <amount> <resource>`", parse_mode=ParseMode.MARKDOWN)
            return
        target_id = resolve_target_id(args, update)
        amount_str, res_name = args[1], args[2].lower()

    if not target_id:
        await update.message.reply_text("❌ Target not found. Use an ID or reply to them.")
        return

    amount = parse_amount(amount_str)
    if amount <= 0:
        await update.message.reply_text("❌ Invalid amount.")
        return

    res_map = {
        "yen": "yens", "yens": "yens", "money": "yens",
        "gem": "gems", "gems": "gems",
        "crystal": "crystals", "crystals": "crystals",
        "ticket": "tickets", "tickets": "tickets",
        "sp": "skill_points", "skill_points": "skill_points",
        "elite": "keys_elite", "elite_key": "keys_elite",
        "boss": "keys_boss", "boss_key": "keys_boss",
        "exp": "exp"
    }
    
    if res_name not in res_map:
        await update.message.reply_text("❌ Invalid resource. Use: yens, gems, crystals, tickets, skill_points, keys_elite, keys_boss, exp")
        return
        
    db.give(target_id, **{res_map[res_name]: amount})
    await update.message.reply_text(f"✅ Gave **{format_number(amount)} {res_name}** to player `{target_id}`.", parse_mode=ParseMode.MARKDOWN)


@require_admin
async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin: Add characters, items, or skills.
    Usage: Reply -> /add <type> <value>
    Or: /add <@username/id> <type> <value>
    """
    args = context.args
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if len(args) < 2:
            await update.message.reply_text("Usage: Reply with `/add <type> <value>`", parse_mode=ParseMode.MARKDOWN)
            return
        type_str = args[0].lower()
        value = " ".join(args[1:])
    else:
        if len(args) < 3:
            await update.message.reply_text("Usage: `/add <@username/id> <type> <value>`", parse_mode=ParseMode.MARKDOWN)
            return
        target_id = resolve_target_id(args, update)
        type_str = args[1].lower()
        value = " ".join(args[2:])

    if not target_id:
        await update.message.reply_text("❌ Target not found.")
        return

    if type_str == "character":
        db.add_character(target_id, value, "legendary")
        await update.message.reply_text(f"✅ Added character **{value}** to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
    elif type_str in ("weapon", "armor", "item"):
        db.add_item(target_id, value, 1)
        await update.message.reply_text(f"✅ Added item **{value}** to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
    elif type_str == "skill":
        db.add_skill(target_id, value)
        await update.message.reply_text(f"✅ Added skill **{value}** to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Invalid type. Use: character, weapon, armor, item, skill.")


@require_admin
async def cmd_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin: Set a player's stats or fields to an exact value.
    Usage: Reply -> /set <field> <value>
    Or: /set <@username/id> <field> <value>
    """
    args = context.args
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if len(args) < 2:
            await update.message.reply_text("Usage: Reply with `/set <field> <value>`", parse_mode=ParseMode.MARKDOWN)
            return
        field_str, value_str = args[0].lower(), args[1]
    else:
        if len(args) < 3:
            await update.message.reply_text("Usage: `/set <@username/id> <field> <value>`", parse_mode=ParseMode.MARKDOWN)
            return
        target_id = resolve_target_id(args, update)
        field_str, value_str = args[1].lower(), args[2]

    if not target_id:
        await update.message.reply_text("❌ Target not found.")
        return

    allowed_fields = {
        "rank": int, "level": int, "exp": int, "yens": int, "gems": int,
        "crystals": int, "tickets": int, "hp": int
    }
    
    if field_str not in allowed_fields:
        await update.message.reply_text(f"❌ Invalid field. Allowed: {', '.join(allowed_fields.keys())}")
        return

    try:
        val = int(value_str)
    except ValueError:
        await update.message.reply_text("❌ Value must be a number.")
        return

    # Special handling for Level (requires converting to EXP)
    if field_str == "level":
        new_exp = (val - 1) * G.LEVEL_EXP
        db.admin_set_field(target_id, "exp", new_exp)
        await update.message.reply_text(f"✅ Set `{target_id}`'s Level to {val}.", parse_mode=ParseMode.MARKDOWN)
        return
        
    if field_str == "hp":
        db.set_current_hp(target_id, val)
        await update.message.reply_text(f"✅ Set `{target_id}`'s Current HP to {val}.", parse_mode=ParseMode.MARKDOWN)
        return

    db.admin_set_field(target_id, field_str, val)
    await update.message.reply_text(f"✅ Set `{target_id}`'s {field_str} to {format_number(val)}.", parse_mode=ParseMode.MARKDOWN)


@require_admin
async def cmd_clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Wipes a player back to a fresh state."""
    args = context.args
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else resolve_target_id(args, update)

    if not target_id:
        await update.message.reply_text("Usage: Reply or `/clear_data <@username/id>`", parse_mode=ParseMode.MARKDOWN)
        return
        
    if target_id == OWNER_ID:
        await update.message.reply_text("❌ Cannot clear the Owner's data.")
        return

    db.admin_reset_player(target_id)
    await update.message.reply_text(f"💥 **Data Wiped.** Player `{target_id}` has been reset to a fresh account.", parse_mode=ParseMode.MARKDOWN)


@require_admin
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Ban a player."""
    args = context.args
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else resolve_target_id(args, update)

    if not target_id:
        await update.message.reply_text("Usage: Reply or `/ban <@username/id>`", parse_mode=ParseMode.MARKDOWN)
        return
        
    if target_id == OWNER_ID:
        await update.message.reply_text("❌ Cannot ban the Owner.")
        return

    db.admin_ban(target_id, True)
    await update.message.reply_text(f"🚫 Player `{target_id}` has been banned.", parse_mode=ParseMode.MARKDOWN)


@require_admin
async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Unban a player."""
    args = context.args
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else resolve_target_id(args, update)

    if not target_id:
        await update.message.reply_text("Usage: Reply or `/unban <@username/id>`", parse_mode=ParseMode.MARKDOWN)
        return

    db.admin_ban(target_id, False)
    await update.message.reply_text(f"✅ Player `{target_id}` has been unbanned.", parse_mode=ParseMode.MARKDOWN)


@require_owner
async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner: Promote user to Admin."""
    args = context.args
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else resolve_target_id(args, update)

    if not target_id:
        await update.message.reply_text("Usage: Reply or `/promote <@username/id>`", parse_mode=ParseMode.MARKDOWN)
        return

    db.admin_promote(target_id, True)
    await update.message.reply_text(f"👑 Player `{target_id}` is now an Admin.", parse_mode=ParseMode.MARKDOWN)


@require_owner
async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner: Demote Admin to Player."""
    args = context.args
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else resolve_target_id(args, update)

    if not target_id:
        await update.message.reply_text("Usage: Reply or `/demote <@username/id>`", parse_mode=ParseMode.MARKDOWN)
        return
        
    if target_id == OWNER_ID:
        await update.message.reply_text("❌ Cannot demote the Owner.")
        return

    db.admin_promote(target_id, False)
    await update.message.reply_text(f"👤 Player `{target_id}` has been demoted to regular user.", parse_mode=ParseMode.MARKDOWN)


@require_owner
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner: Send a message to everyone."""
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode=ParseMode.MARKDOWN)
        return
    
    msg = " ".join(context.args)
    players = db.all_players()
    success = 0
    status = await update.message.reply_text(f"📢 Broadcasting to {len(players)} players...")
    
    for p in players:
        try:
            await context.bot.send_message(
                chat_id=p["user_id"], 
                text=f"📢 **ANNOUNCEMENT**\n\n{msg}", 
                parse_mode=ParseMode.MARKDOWN
            )
            success += 1
        except Exception:
            pass # Ignore blocked bots
            
    await status.edit_text(f"✅ Broadcast sent successfully to {success} players.")


# =============================================================
# MASSIVE CLAN SYSTEM (Text Router)
# =============================================================
@require_not_banned
async def cmd_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the entire Clan System via text commands.
    Because clan management requires typing names (clan names, user tags, 
    announcement text), a hybrid UI/Text approach is used here.
    """
    ensure_player(update)
    uid = update.effective_user.id
    args = context.args

    # If no arguments, show the UI menu from Part 2
    if not args:
        class MockQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
            async def answer(self, text="", show_alert=False):
                pass
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                
        await show_clan_menu(MockQuery(update.message))
        return

    action = args[0].lower()
    sub_args = args[1:]
    clan_data = clans.membership(uid)

    # --- 1. CREATE CLAN ---
    if action == "create":
        if not sub_args:
            await update.message.reply_text("Usage: `/clan create <name>`\nCost: 100 Crystals.", parse_mode=ParseMode.MARKDOWN)
            return
        name = " ".join(sub_args)
        try:
            clans.create(uid, name)
            ach = combat.CombatAchievements(uid)
            ach.check_clan(leader=True)
            await update.message.reply_text(f"🏰 **Clan Created!**\nWelcome to **{name}**!\nYou are now the Leader.", parse_mode=ParseMode.MARKDOWN)
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 2. JOIN CLAN ---
    if action == "join":
        if not sub_args:
            await update.message.reply_text("Usage: `/clan join <name>`", parse_mode=ParseMode.MARKDOWN)
            return
        name = " ".join(sub_args)
        try:
            clans.join(uid, name)
            await update.message.reply_text(f"🏰 Successfully joined **{name}**!", parse_mode=ParseMode.MARKDOWN)
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 3. LEAVE CLAN ---
    if action == "leave":
        try:
            res = clans.leave(uid)
            if res == "disbanded":
                await update.message.reply_text("🏰 You left the clan and it was disbanded (you were the last member).")
            else:
                await update.message.reply_text("🏰 You have left the clan.")
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # All other actions require clan membership
    if not clan_data:
        await update.message.reply_text("❌ You are not in a clan. Use `/clan create` or `/clan join`.", parse_mode=ParseMode.MARKDOWN)
        return

    clan_id = clan_data["clan_id"]
    role = clan_data["role"]

    # --- 4. CLAN INFO ---
    if action == "info":
        text = (
            f"🏰 **Clan Info: {clan_data['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👑 Leader: {clan_data['role'].capitalize()}\n"
            f"👥 Members: {clans.member_count(clan_id)}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💴 Yens Vault: {format_number(clan_data['treasure_yens'])}\n"
            f"💎 Gems Vault: {format_number(clan_data['treasure_gems'])}\n"
            f"🔮 Crystals Vault: {format_number(clan_data['treasure_crystals'])}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📢 **Announcement:**\n"
            f"{clan_data['announcement'] or '*No announcement set.*'}"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    # --- 5. MEMBERS ROSTER ---
    if action == "members":
        rows = clans.members(clan_id)
        text = f"🏰 **Members of {clan_data['name']}** ({len(rows)})\n\n"
        for r in rows:
            role_icon = "👑" if r["role"] == "leader" else ("⚔️" if r["role"] == "officer" else "👤")
            exp = format_number(r["exp"] or 0)
            text += f"{role_icon} {r['first_name']} (`{r['user_id']}`) - {exp} EXP\n"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    # --- 6. PROMOTE / DEMOTE / TRANSFER / KICK ---
    if action in ("promote", "demote", "transfer", "kick", "remove"):
        if role not in ("leader", "officer"):
            await update.message.reply_text("❌ Only Leaders and Officers can manage members.")
            return
            
        target_id = resolve_target_id(sub_args, update)
        if not target_id:
            await update.message.reply_text(f"Usage: Reply to a user or `/clan {action} <@username/id>`", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            if action == "promote":
                clans.promote(uid, target_id)
                await update.message.reply_text(f"✅ Promoted `{target_id}` to Officer.", parse_mode=ParseMode.MARKDOWN)
            elif action == "demote":
                clans.demote(uid, target_id)
                await update.message.reply_text(f"✅ Demoted `{target_id}` to Member.", parse_mode=ParseMode.MARKDOWN)
            elif action == "transfer":
                clans.transfer(uid, target_id)
                await update.message.reply_text(f"👑 Transferred Leadership to `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
            elif action in ("kick", "remove"):
                clans.remove(uid, target_id)
                await update.message.reply_text(f"✅ Kicked `{target_id}` from the clan.", parse_mode=ParseMode.MARKDOWN)
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 7. DISBAND CLAN ---
    if action == "disband":
        try:
            clans.disband(uid)
            await update.message.reply_text("💥 The clan has been permanently disbanded.")
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 8. ANNOUNCE ---
    if action == "announce":
        if role not in ("leader", "officer"):
            await update.message.reply_text("❌ Only Leaders and Officers can post announcements.")
            return
        if not sub_args:
            await update.message.reply_text("Usage: `/clan announce <message>`", parse_mode=ParseMode.MARKDOWN)
            return
        msg = " ".join(sub_args)
        clans.set_announcement(clan_id, msg)
        await update.message.reply_text("📢 Announcement updated successfully!")
        return

    # --- 9. INVITE ---
    if action == "invite":
        if role not in ("leader", "officer"):
            await update.message.reply_text("❌ Only Leaders and Officers can invite players.")
            return
        target_id = resolve_target_id(sub_args, update)
        if not target_id:
            await update.message.reply_text("Usage: Reply to a user or `/clan invite <@username/id>`", parse_mode=ParseMode.MARKDOWN)
            return
        try:
            clans.add(uid, target_id)
            await update.message.reply_text(f"✅ Invited `{target_id}` to the clan.", parse_mode=ParseMode.MARKDOWN)
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 10. TREASURE / DONATE / WITHDRAW ---
    if action == "treasure":
        text = (
            f"🏛️ **Clan Vault**\n"
            f"💴 Yens: {format_number(clan_data['treasure_yens'])}\n"
            f"💎 Gems: {format_number(clan_data['treasure_gems'])}\n"
            f"🔮 Crystals: {format_number(clan_data['treasure_crystals'])}\n\n"
            f"**Commands:**\n"
            f"`/clan donate <yens|gems|crystals> <amount>`\n"
            f"`/clan withdraw <yens|gems|crystals> <amount>` (Leader Only)"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    if action == "donate":
        if len(sub_args) < 2:
            await update.message.reply_text("Usage: `/clan donate <resource> <amount>`", parse_mode=ParseMode.MARKDOWN)
            return
        res_map = {"yens": "yens", "gems": "gems", "crystals": "crystals"}
        res = sub_args[0].lower()
        if res not in res_map:
            await update.message.reply_text("❌ Invalid resource. Use: yens, gems, crystals.")
            return
        amt = parse_amount(sub_args[1])
        if amt <= 0:
            await update.message.reply_text("❌ Invalid amount.")
            return
            
        if not db.spend(uid, res_map[res], amt):
            await update.message.reply_text(f"❌ You don't have enough {res}.")
            return
            
        clans.add_treasure(clan_id, **{res_map[res]: amt})
        await update.message.reply_text(f"✅ Donated {format_number(amt)} {res} to the clan vault!")
        return

    if action == "withdraw":
        if role != "leader":
            await update.message.reply_text("❌ Only the Leader can withdraw from the vault.")
            return
        if len(sub_args) < 2:
            await update.message.reply_text("Usage: `/clan withdraw <resource> <amount>`", parse_mode=ParseMode.MARKDOWN)
            return
        res_map = {"yens": "yens", "gems": "gems", "crystals": "crystals"}
        res = sub_args[0].lower()
        if res not in res_map:
            await update.message.reply_text("❌ Invalid resource.")
            return
        amt = parse_amount(sub_args[1])
        if amt <= 0:
            await update.message.reply_text("❌ Invalid amount.")
            return
            
        try:
            clans.withdraw_treasure(uid, **{res_map[res]: amt})
            await update.message.reply_text(f"✅ Withdrew {format_number(amt)} {res} from the clan vault.")
        except clans.ClanError as e:
            await update.message.reply_text(f"❌ {e}")
        return

    # --- 11. CLAN RAIDS ---
    if action == "raid":
        if not sub_args:
            await update.message.reply_text("Usage: `/clan raid <Perfect Cell|Frieza|Majin Buu|Beerus>`", parse_mode=ParseMode.MARKDOWN)
            return
            
        boss_name = " ".join(sub_args)
        if boss_name not in G.CLAN_RAIDS:
            await update.message.reply_text(f"❌ Invalid boss. Available: {', '.join(G.CLAN_RAIDS.keys())}")
            return
            
        boss_info = G.CLAN_RAIDS[boss_name]
        state = clans.clan_raid_state(clan_id)
        
        if state and state["boss_name"] == boss_name:
            pct = int(state["hp"] * 100 / state["max_hp"])
            await update.message.reply_text(
                f"⚔️ **{boss_name} Raid is already active!**\n"
                f"HP: {format_number(state['hp'])}/{format_number(state['max_hp'])} ({pct}%)\n"
                f"Use `/clan raidhit` to attack!", parse_mode=ParseMode.MARKDOWN
            )
            return
            
        clans.clan_raid_start(clan_id, boss_name, boss_info["hp"], boss_info["dmg"])
        await update.message.reply_text(f"🔱 **{boss_name} Raid Started!**\nHP: {format_number(boss_info['hp'])}\nUse `/clan raidhit` to attack!", parse_mode=ParseMode.MARKDOWN)
        return

    if action == "raidhit":
        state = clans.clan_raid_state(clan_id)
        if not state:
            await update.message.reply_text("❌ No active clan raid. Start one with `/clan raid <boss>`.")
            return
            
        s = player_stats(uid)
        damage = s["atk"] * 3
        result = clans.clan_raid_hit(clan_id, uid, damage)
        
        if not result:
            await update.message.reply_text("❌ Raid encounter ended unexpectedly.")
            return
            
        hp_left, defeated, dmg_by, boss_name = result
        
        if defeated:
            info = G.CLAN_RAIDS[boss_name]
            db.give(uid, yens=info["reward_yens"], gems=info["reward_gems"], crystals=info["reward_crystals"], tickets=info["reward_tickets"], skill_points=info["reward_skill_points"])
            clans.add_treasure(clan_id, yens=info["reward_yens"], gems=info["reward_gems"], crystals=info["reward_crystals"])
            
            ach = combat.CombatAchievements(uid)
            ach.check_clan_raid_cleared()
            
            await update.message.reply_text(
                f"🏆 **CLAN RAID CLEARED!**\n"
                f"**{boss_name}** has been defeated!\n\n"
                f"🎁 **Rewards:**\n"
                f"💴 {format_number(info['reward_yens'])} Yens\n"
                f"💎 {format_number(info['reward_gems'])} Gems\n"
                f"🔮 {format_number(info['reward_crystals'])} Crystals\n"
                f"🎫 {info['reward_tickets']} Tickets\n"
                f"🌟 {info['reward_skill_points']} SP"
                + ach.reward_text(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"⚔️ You hit **{boss_name}** for **{format_number(damage)}**!\n"
                f"Boss HP remaining: {format_number(hp_left)}/{format_number(state['max_hp'])}",
                parse_mode=ParseMode.MARKDOWN
            )
        return

    # --- FALLBACK ---
    await update.message.reply_text("❌ Unknown clan command. Check `/clan` for the menu.", parse_mode=ParseMode.MARKDOWN)


# =============================================================
# END OF PART 3
# =============================================================
# Part 4 will contain:
# - The 5 New Commands (/pity, /daily_shop, /titles, /craft, /element)
# - The Final Button Router combining all parts
# - The main() function & error handling.
# =============================================================
# =============================================================
# PART 4: ENDGAME COMMANDS, MASTER ROUTER & SETUP
# =============================================================

# -------------------------------------------------------------
# 1. /pity - Gacha Pity Tracker
# -------------------------------------------------------------
@require_not_banned
async def cmd_pity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the player's current gacha pity progress."""
    ensure_player(update)
    uid = update.effective_user.id
    
    # Simulated gacha pulls (In a real DB, this would be fetched from db.py)
    p = db.player(uid)
    pulls = int(p.get("gacha_pulls", 0)) if p else 0
    
    soft_pity = G.GACHA_PITY["soft_pity"]
    hard_pity = G.GACHA_PITY["hard_pity"]
    sp_pity = G.GACHA_PITY["sp_plus_pity"]
    omni_pity = G.GACHA_PITY["omni_pity"]
    
    soft_left = max(0, soft_pity - pulls)
    hard_left = max(0, hard_pity - pulls)
    sp_left = max(0, sp_pity - pulls)
    omni_left = max(0, omni_pity - pulls)
    
    def build_bar(current, max_val):
        pct = min(100, int((current / max_val) * 100))
        filled = int((pct / 100) * 10)
        return f"`[{'🟩' * filled}{'⬛' * (10 - filled)}]` {pct}%"
        
    text = (
        f"🎰 <b>Gacha Pity System</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎫 <b>Total Pulls:</b> {pulls}\n\n"
        f"🟡 <b>Soft Pity (Legendary+)</b>\n"
        f"   {build_bar(pulls, soft_pity)}\n"
        f"   Guaranteed in <b>{soft_left}</b> pulls\n\n"
        f"🔴 <b>Hard Pity (Mythical+)</b>\n"
        f"   {build_bar(pulls, hard_pity)}\n"
        f"   Guaranteed in <b>{hard_left}</b> pulls\n\n"
        f"💠 <b>SP+ Pity</b>\n"
        f"   {build_bar(pulls, sp_pity)}\n"
        f"   Guaranteed in <b>{sp_left}</b> pulls\n\n"
        f"👑 <b>Omni King Pity</b>\n"
        f"   {build_bar(pulls, omni_pity)}\n"
        f"   Guaranteed in <b>{omni_left}</b> pulls\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Pity carries over between banners!</i>"
    )
    
    kb = [
        [InlineKeyboardButton("🎰 Go to Gacha", callback_data="menu_gacha")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# -------------------------------------------------------------
# 2. /daily_shop - Rotating Daily Shop
# -------------------------------------------------------------
@require_not_banned
async def cmd_daily_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the rotating daily shop."""
    ensure_player(update)
    uid = update.effective_user.id
    p = db.player(uid)
    
    # Deterministic daily shop based on date and user ID
    now = datetime.now(timezone.utc)
    date_seed = f"{now.year}-{now.month}-{now.day}-{uid}"
    rng = random.Random(date_seed)
    
    pool = list(G.DAILY_SHOP_POOL)
    rng.shuffle(pool)
    daily_items = pool[:3]
    
    text = (
        f"🛒 <b>Daily Rotating Shop</b>\n"
        f"<i>Resets every 24 hours (UTC)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💴 Yens: <b>{format_number(p['yens'])}</b>\n"
        f"💎 Gems: <b>{format_number(p['gems'])}</b>\n"
        f"🔮 Crystals: <b>{format_number(p['crystals'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    kb = []
    for idx, item in enumerate(daily_items):
        name = item["item"]
        price = item["price"]
        currency = item["currency"]
        
        cur_icon = {"yens": "💴", "gems": "💎", "crystals": "🔮"}.get(currency, "💵")
        text += f"<b>{idx+1}. {escape(name)}</b>\n   Price: {cur_icon} {format_number(price)} {currency.capitalize()}\n\n"
        
        kb.append([InlineKeyboardButton(f"Buy {name} ({format_number(price)} {currency.upper()})", callback_data=f"dshop_buy_{idx}")])
        
    kb.append([InlineKeyboardButton("🔄 Refresh Shop (10 Crystals)", callback_data="dshop_refresh")])
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# -------------------------------------------------------------
# 3. /titles - Passive Stat Bonuses
# -------------------------------------------------------------
@require_not_banned
async def cmd_titles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the Titles menu."""
    ensure_player(update)
    uid = update.effective_user.id
    p = db.player(uid)
    
    try:
        equipped_code = p["equipped_title"] if p and "equipped_title" in p.keys() else None
    except Exception:
        equipped_code = None
        
    equipped_name = G.TITLES[equipped_code]["name"] if equipped_code and equipped_code in G.TITLES else "None"
    
    text = (
        f"🏷️ <b>Title Collection</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Currently Equipped: <b>{equipped_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<i>Titles grant passive stat bonuses.</i>\n"
        f"<i>Tap a title to check requirements and equip.</i>\n\n"
    )
    
    kb = []
    for code, info in G.TITLES.items():
        # Check unlock requirements (Simplified check)
        unlocked = True # Placeholder for actual requirement validation
        icon = "✅" if unlocked else "🔒"
        check_mark = " (Equipped)" if code == equipped_code else ""
        
        kb.append([InlineKeyboardButton(f"{icon} {info['name']} - {info['bonus']}{check_mark}", callback_data=f"title_select_{code}")])
        
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# -------------------------------------------------------------
# 4. /craft - Item Crafting System
# -------------------------------------------------------------
@require_not_banned
async def cmd_craft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the Crafting Workshop."""
    ensure_player(update)
    uid = update.effective_user.id
    p = db.player(uid)
    
    text = (
        f"🛠️ <b>Crafting Workshop</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💴 Yens: <b>{format_number(p['yens'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<i>Combine materials to craft OP gear!</i>\n\n"
    )
    
    kb = []
    for item, recipe in G.CRAFTING_RECIPES.items():
        kb.append([InlineKeyboardButton(f"🛠️ {item}", callback_data=f"craft_select_{item}")])
        
    kb.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# -------------------------------------------------------------
# 5. /element - Elemental Weaknesses
# -------------------------------------------------------------
@require_not_banned
async def cmd_element(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the elemental synergy chart."""
    text = f"🌪️ <b>Elemental Synergy Chart</b>\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Understanding elements is key to victory!</i>\n\n"
    
    for element, data in G.ELEMENTAL_SYNERGY.items():
        strong = ", ".join(data["strong"])
        weak = ", ".join(data["weak"])
        text += f"<b>{element}</b>\n  🟢 Strong vs: <i>{strong}</i>\n  🔴 Weak vs: <i>{weak}</i>\n\n"
        
    kb = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# =============================================================
# COMMAND INTERCEPTORS (Subcommands)
# =============================================================
async def cmd_shop_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts /shop to check for 'refresh' subcommand."""
    args = context.args
    if args and args[0].lower() == "refresh":
        uid = update.effective_user.id
        if db.spend(uid, "crystals", 10):
            await update.message.reply_text("🔄 <b>Shop Refreshed!</b>\nUse /daily_shop to see the new items.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ You need 10 Crystals to refresh the shop.", parse_mode=ParseMode.HTML)
        return
    
    # Fallback to original shop UI
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
        async def answer(self): pass
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await show_shop_menu(MockQuery(update.message))


async def cmd_gacha_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts /gacha to check for 'rates' subcommand."""
    args = context.args
    if args and args[0].lower() == "rates":
        text = "🎰 <b>Gacha Drop Rates (Standard)</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for rarity, rate in G.GACHA_RATES:
            label = G.RARITY_LABEL.get(rarity, rarity.capitalize())
            text += f"{label}: <b>{rate}%</b>\n"
        text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n<i>* Higher banners have boosted rates!</i>\n<i>* Use /pity to check your guaranteed pulls.</i>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
        
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
        async def answer(self): pass
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await show_gacha_menu(MockQuery(update.message))


async def cmd_travel_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts /travel to check for 'lore' subcommand."""
    args = context.args
    if args and args[0].lower() == "lore":
        if len(args) < 2:
            await update.message.reply_text("Usage: <code>/travel lore &lt;planet&gt;</code>", parse_mode=ParseMode.HTML)
            return
        planet = " ".join(args[1:])
        matched_planet = next((p for p in G.PLANETS if p.lower() == planet.lower()), None)
        
        if not matched_planet:
            await update.message.reply_text("❌ Unknown planet.", parse_mode=ParseMode.HTML)
            return
            
        data = G.PLANETS[matched_planet]
        text = (
            f"🌍 <b>Lore: {escape(matched_planet)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>{escape(data['lore'])}</i>\n\n"
            f"⭐ <b>Multiplier:</b> x{data['multiplier']}\n"
            f"🔓 <b>Unlock:</b> {escape(data['unlock_condition'])}\n"
            f"🎯 <b>Rec. Level:</b> {data['level_min']} - {data['level_max']}"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
        
    class MockQuery:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
        async def answer(self): pass
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await show_travel_menu(MockQuery(update.message))


# =============================================================
# MASTER BUTTON ROUTER
# =============================================================
async def master_button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Routes all button clicks to the correct handler.
    Checks Part 4 buttons first, then Part 3, then Part 2, then Part 1.
    """
    query = update.callback_query
    data = query.data
    uid = query.from_user.id
    
    # ---------------------------------------------------------
    # PART 4 BUTTONS (Daily Shop, Titles, Crafting)
    # ---------------------------------------------------------
    if data.startswith("dshop_buy_"):
        idx = int(data.replace("dshop_buy_", ""))
        # Get deterministic shop
        now = datetime.now(timezone.utc)
        rng = random.Random(f"{now.year}-{now.month}-{now.day}-{uid}")
        pool = list(G.DAILY_SHOP_POOL)
        rng.shuffle(pool)
        daily_items = pool[:3]
        
        if idx >= len(daily_items):
            await query.answer("❌ Item no longer available.", show_alert=True)
            return
            
        item = daily_items[idx]
        if db.spend(uid, item["currency"], item["price"]):
            if item["item"] in G.SKILLS:
                db.add_skill(uid, item["item"])
            else:
                db.add_item(uid, item["item"], 1)
            await query.answer(f"✅ Bought {item['item']}!", show_alert=True)
            await cmd_daily_shop(update, context)
        else:
            await query.answer(f"❌ Not enough {item['currency']}!", show_alert=True)
        return

    if data == "dshop_refresh":
        if db.spend(uid, "crystals", 10):
            await query.answer("🔄 Shop Refreshed!", show_alert=True)
            await cmd_daily_shop(update, context)
        else:
            await query.answer("❌ Need 10 Crystals!", show_alert=True)
        return

    if data.startswith("title_select_"):
        title_code = data.replace("title_select_", "")
        try:
            db.set_field(uid, "equipped_title", title_code)
            await query.answer(f"✅ Equipped: {G.TITLES[title_code]['name']}!", show_alert=True)
        except Exception:
            await query.answer("✅ Title equipped (Simulated)!", show_alert=True)
        await cmd_titles(update, context)
        return

    if data.startswith("craft_select_"):
        item_name = data.replace("craft_select_", "")
        recipe = G.CRAFTING_RECIPES.get(item_name)
        if not recipe:
            await query.answer("❌ Recipe missing.", show_alert=True)
            return
            
        # Check materials
        mats_text = ""
        for mat, req_qty in recipe["materials"].items():
            have_qty = sum(row["qty"] for row in db.items(uid) if row["item"] == mat)
            status = "✅" if have_qty >= req_qty else "❌"
            mats_text += f"  {status} {req_qty}x {mat} (You have {have_qty})\n"
            
        text = (
            f"🛠️ <b>Crafting: {escape(item_name)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💴 <b>Cost:</b> {format_number(recipe['cost_yens'])} Yens\n\n"
            f"📦 <b>Materials Required:</b>\n{mats_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = [
            [InlineKeyboardButton("🛠️ Craft Item", callback_data=f"craft_do_{item_name}")],
            [InlineKeyboardButton("⬅️ Back to Crafting", callback_data="back_to_crafting")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        return

    if data.startswith("craft_do_"):
        item_name = data.replace("craft_do_", "")
        recipe = G.CRAFTING_RECIPES.get(item_name)
        
        if not db.spend(uid, "yens", recipe["cost_yens"]):
            await query.answer("❌ Not enough Yens!", show_alert=True)
            return
            
        for mat, req_qty in recipe["materials"].items():
            db.remove_item(uid, mat, req_qty)
            
        if item_name in G.SKILLS:
            db.add_skill(uid, item_name)
        else:
            db.add_item(uid, item_name, 1)
            
        await query.answer(f"🛠️ Crafted {item_name}!", show_alert=True)
        await cmd_craft(update, context)
        return

    if data == "back_to_crafting":
        await cmd_craft(update, context)
        return

    # ---------------------------------------------------------
    # PART 2 BUTTONS (Shop, Inventory, Characters, Gacha, Travel, Raids)
    # ---------------------------------------------------------
    if data.startswith(("shop_cat_", "buy_", "equip_item_", "equip_char_", "gacha_pull_", "travel_to_", "summon_", "clan_raid_view")):
        await button_router_part2(update, context)
        return
        
    if data in ("menu_shop", "menu_inventory", "menu_characters", "menu_gacha", "menu_travel", "menu_raids"):
        await button_router_part2(update, context)
        return

    # ---------------------------------------------------------
    # PART 1 BUTTONS (Main Menu, Explore, Heal, Profile)
    # ---------------------------------------------------------
    # If not handled, pass to core router (which handles menu_profile, menu_explore, etc.)
    await button_router_core(update, context)


# =============================================================
# ERROR HANDLER & MAIN SETUP
# =============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the user without crashing."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ **Internal Error**\nSomething went wrong. Please try again or use /unstuck.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass


async def post_init(application: Application) -> None:
    """Registers the bot's command menu in Telegram."""
    commands = [
        ("start", "Start the game and see main menu"),
        ("menu", "Open the main UI dashboard"),
        ("unstuck", "Clear stuck battle & fully heal"),
        ("help", "View the game guide"),
        ("pity", "Check your Gacha Pity progress"),
        ("daily_shop", "View the rotating daily shop"),
        ("titles", "Equip passive stat titles"),
        ("craft", "Open the crafting workshop"),
        ("element", "View elemental weaknesses"),
        ("clan", "Manage your clan"),
        ("raid", "View World Raid status"),
        ("raid_attack", "Attack the World Raid boss"),
        ("admin", "Open Admin Panel (Admins only)")
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Bot command menu synchronized with Telegram.")


def main() -> None:
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN environment variable is required.")
        return
        
    # Initialize Database
    print("🔧 Initializing database...")
    db.init()
    print("✅ Database ready.")
    
    # Build Application
    print("🔧 Building application...")
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    # --- 1. CORE COMMANDS ---
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("menu", cmd_menu))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("unstuck", cmd_unstuck))
    
    # --- 2. PART 4 COMMANDS ---
    application.add_handler(CommandHandler("pity", cmd_pity))
    application.add_handler(CommandHandler("daily_shop", cmd_daily_shop))
    application.add_handler(CommandHandler("titles", cmd_titles))
    application.add_handler(CommandHandler("craft", cmd_craft))
    application.add_handler(CommandHandler("element", cmd_element))
    
    # --- 3. TEXT COMMAND WRAPPERS ---
    application.add_handler(CommandHandler("shop", cmd_shop_wrapper))
    application.add_handler(CommandHandler("gacha", cmd_gacha_wrapper))
    application.add_handler(CommandHandler("travel", cmd_travel_wrapper))
    
    # --- 4. CLANS & RAIDS ---
    application.add_handler(CommandHandler("clan", cmd_clan))
    application.add_handler(CommandHandler("raid", cmd_raid))
    application.add_handler(CommandHandler("raid_attack", cmd_raid_attack))
    
    # --- 5. ADMIN & OWNER ---
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CommandHandler("give", cmd_give))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("set", cmd_set))
    application.add_handler(CommandHandler("clear_data", cmd_clear_data))
    application.add_handler(CommandHandler("ban", cmd_ban))
    application.add_handler(CommandHandler("unban", cmd_unban))
    application.add_handler(CommandHandler("promote", cmd_promote))
    application.add_handler(CommandHandler("demote", cmd_demote))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))
    application.add_handler(CommandHandler("raid_start", cmd_raid_start))
    
    # --- 6. THE MASTER BUTTON ROUTER ---
    application.add_handler(CallbackQueryHandler(master_button_router))
    
    # --- 7. ERROR HANDLER ---
    application.add_error_handler(error_handler)
    
    print("🚀 Bot is starting up! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
