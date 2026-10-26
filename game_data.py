from __future__ import annotations

# =============================================================
# DRAGON BALL / ANIME CROSSOVER RPG — MASTER GAME DATA (PART 1)
# =============================================================
# This file is the SINGLE source of truth for all game data.
# It is divided into 2 parts to prevent message truncation and
# to allow for massive, detailed expansion.
#
# PART 1 CONTAINS:
#   - Core Game Configuration & Settings
#   - Planet Realms & Travel Logic
#   - NPCs & World Bosses
#   - Factions & Elemental Affinities
#   - MASSIVE Character Roster (275+ Characters)
#
# PART 2 WILL CONTAIN:
#   - Rarity Configurations & Gacha Rates
#   - Weapons, Armors, & Shop Inventory
#   - Skills, Titles, & Crafting Systems
#   - Raid Bosses, Clan Perks, & Summons
#   - Progression, Achievements, & Quests
# =============================================================

# -------------------------------------------------------------
# 1. CORE GAME CONFIGURATION
# -------------------------------------------------------------
# These are the default values applied to a brand-new player
# when they first run the /start command.

STARTING_RESOURCES = {
    "yens":         500000,     # Primary currency for basic gear
    "gems":         20000,      # Premium currency for gacha and rare gear
    "crystals":     5555,       # Endgame currency for rank-ups and clans
    "tickets":      130,        # Used for summoning characters
    "skill_points": 120,        # Used for unlocking combat skills
    "keys_elite":   10,         # Used for Elite Boss Summons
    "keys_boss":    10,         # Used for Mythical/Legendary Boss Summons
    "exp":          0,          # Experience points (starts at 0)
}

# The amount of EXP required to level up. 
# Formula: Level = 1 + (Total EXP // LEVEL_EXP)
LEVEL_EXP = 100

# The maximum level a player can reach
MAX_PLAYER_LEVEL = 1000

# The number of NPC wins required to spawn a World Boss.
# Once this streak is hit, the next battle will be a Boss.
NPC_STREAK_FOR_BOSS = 15

# The maximum amount of stamina a player can hold
MAX_STAMINA = 100

# The time (in seconds) it takes to regenerate 1 stamina point
STAMINA_REGEN_TIME = 300  # 5 minutes


# -------------------------------------------------------------
# 2. PLANET REALMS & TRAVEL LOGIC
# -------------------------------------------------------------
# The game features 7 distinct realms. Each realm has a level
# gate, a reward multiplier, and unique lore.

PLANETS = {
    "Earth": {
        "id": 1,
        "level_min": 1,
        "level_max": 20,
        "multiplier": 1.0,
        "stamina_cost": 5,
        "desc": "Starter planet — balanced encounters for beginners.",
        "lore": "The blue planet where the journey begins. Goku, Naruto, Ichigo, and Luffy all hail from worlds similar to this.",
        "bg_color": "#4A90E2",
        "unlock_condition": "None (Default)",
    },
    "Hell": {
        "id": 2,
        "level_min": 21,
        "level_max": 39,
        "multiplier": 2.0,
        "stamina_cost": 10,
        "desc": "Underworld abyss — demonic foes yield 2x rewards.",
        "lore": "A realm of eternal fire and torment. Here, you will face demons, hollows, and the damned souls of fallen warriors.",
        "bg_color": "#D0021B",
        "unlock_condition": "Reach Level 21",
    },
    "Kai Planet": {
        "id": 3,
        "level_min": 40,
        "level_max": 59,
        "multiplier": 3.0,
        "stamina_cost": 15,
        "desc": "North King Kai's sacred orb — 10x gravity, 3x rewards.",
        "lore": "A tiny planet with intense gravity. The training grounds of the gods, where only the strongest can stand.",
        "bg_color": "#F5A623",
        "unlock_condition": "Reach Level 40",
    },
    "Supreme Kai Planet": {
        "id": 4,
        "level_min": 60,
        "level_max": 79,
        "multiplier": 4.0,
        "stamina_cost": 20,
        "desc": "Holy sanctum of the Supreme Kais — 4x rewards.",
        "lore": "A divine realm hidden outside the flow of time. The home of the Supreme Kais and the sacred Z-Sword.",
        "bg_color": "#9013FE",
        "unlock_condition": "Reach Level 60",
    },
    "Lord Beerus Planet": {
        "id": 5,
        "level_min": 80,
        "level_max": 99,
        "multiplier": 5.0,
        "stamina_cost": 25,
        "desc": "Domain of Lord Beerus and Whis — God Ki, 5x rewards.",
        "lore": "The tranquil home of the God of Destruction. Here, the laws of physics are mere suggestions.",
        "bg_color": "#50E3C2",
        "unlock_condition": "Reach Level 80",
    },
    "Omniverse": {
        "id": 6,
        "level_min": 100,
        "level_max": 199,
        "multiplier": 7.0,
        "stamina_cost": 35,
        "desc": "Multiversal pinnacle — 7x rewards, ultimate challenge.",
        "lore": "The realm of Zeno and the Omni-Kings. Entire universes are erased on a whim here. Only the absolute strongest survive.",
        "bg_color": "#F8E71C",
        "unlock_condition": "Reach Level 100",
    },
    "Anime Multiverse": {
        "id": 7,
        "level_min": 200,
        "level_max": 999,
        "multiplier": 10.0,
        "stamina_cost": 50,
        "desc": "The Nexus of all Anime realities — 10x rewards.",
        "lore": "A tear in the fabric of reality where the Dragon Ball, Naruto, Bleach, and One Piece universes collide. Legends from all worlds fight for supremacy.",
        "bg_color": "#BD10E0",
        "unlock_condition": "Reach Level 200",
    },
}

PLANET_ORDER = [
    "Earth", 
    "Hell", 
    "Kai Planet", 
    "Supreme Kai Planet", 
    "Lord Beerus Planet", 
    "Omniverse",
    "Anime Multiverse"
]


# -------------------------------------------------------------
# 3. NPCS & WORLD BOSSES
# -------------------------------------------------------------
# NPCS are the standard enemies found while exploring. 
# They scale in difficulty based on the planet's multiplier.
# 
# BOSSES spawn automatically after 15 NPC kills.

NPCS = [
    # --- Earth Tier (Levels 1-20) ---
    {"id": 1, "name": "Bandit Rookie", "hp": 70, "dmg": 8, "reward": 220, "exp": 10, "tier": 1},
    {"id": 2, "name": "Wild Wolf", "hp": 100, "dmg": 12, "reward": 340, "exp": 15, "tier": 1},
    {"id": 3, "name": "Rogue Ninja", "hp": 150, "dmg": 16, "reward": 520, "exp": 25, "tier": 1},
    {"id": 4, "name": "Red Ribbon Soldier", "hp": 180, "dmg": 18, "reward": 640, "exp": 30, "tier": 1},
    {"id": 5, "name": "Hollow (Base)", "hp": 210, "dmg": 20, "reward": 740, "exp": 35, "tier": 1},
    {"id": 6, "name": "Marine Grunt", "hp": 240, "dmg": 22, "reward": 850, "exp": 40, "tier": 1},
    
    # --- Hell Tier (Levels 21-39) ---
    {"id": 7, "name": "Shadow Sorcerer", "hp": 270, "dmg": 24, "reward": 980, "exp": 50, "tier": 2},
    {"id": 8, "name": "Dark Knight", "hp": 350, "dmg": 30, "reward": 1200, "exp": 60, "tier": 2},
    {"id": 9, "name": "Storm Samurai", "hp": 420, "dmg": 36, "reward": 1650, "exp": 75, "tier": 2},
    {"id": 10, "name": "Void Hunter", "hp": 500, "dmg": 44, "reward": 2100, "exp": 90, "tier": 2},
    {"id": 11, "name": "Demon Clan Warrior", "hp": 580, "dmg": 50, "reward": 2400, "exp": 105, "tier": 2},
    {"id": 12, "name": "Arrancar Scout", "hp": 650, "dmg": 55, "reward": 2700, "exp": 120, "tier": 2},
    
    # --- Kai Tier (Levels 40-59) ---
    {"id": 13, "name": "Planetary Raider", "hp": 620, "dmg": 52, "reward": 2600, "exp": 150, "tier": 3},
    {"id": 14, "name": "Cosmic Assassin", "hp": 760, "dmg": 62, "reward": 3200, "exp": 180, "tier": 3},
    {"id": 15, "name": "Galaxy Thug", "hp": 860, "dmg": 70, "reward": 3900, "exp": 220, "tier": 3},
    {"id": 16, "name": "Planet Breaker", "hp": 980, "dmg": 80, "reward": 4700, "exp": 260, "tier": 3},
    {"id": 17, "name": "Saiyan Elite", "hp": 1350, "dmg": 105, "reward": 6800, "exp": 350, "tier": 3},
    
    # --- Supreme Kai Tier (Levels 60-79) ---
    {"id": 18, "name": "Hell Warden", "hp": 1550, "dmg": 120, "reward": 8100, "exp": 450, "tier": 4},
    {"id": 19, "name": "Kai Apprentice", "hp": 1800, "dmg": 140, "reward": 9600, "exp": 550, "tier": 4},
    {"id": 20, "name": "God of Destruction Adept", "hp": 2200, "dmg": 175, "reward": 12500, "exp": 700, "tier": 4},
    
    # --- Lord Beerus Tier (Levels 80-99) ---
    {"id": 21, "name": "Angel Warrior", "hp": 2700, "dmg": 215, "reward": 15500, "exp": 900, "tier": 5},
    {"id": 22, "name": "Omniversal Sentinel", "hp": 3300, "dmg": 265, "reward": 19500, "exp": 1200, "tier": 5},
    
    # --- Omniverse Tier (Levels 100+) ---
    {"id": 23, "name": "Timeline Devourer", "hp": 4100, "dmg": 325, "reward": 24500, "exp": 1500, "tier": 6},
    {"id": 24, "name": "Multiversal Paradox", "hp": 5200, "dmg": 400, "reward": 31000, "exp": 2000, "tier": 6},
]

BOSSES = [
    # --- Tier 1 Bosses ---
    {
        "name": "Frieza Force Commander",
        "hp": 1800, "dmg": 60,
        "yens": 9000, "gems": 900, "crystals": 60,
        "tickets": 5, "skill_points": 20, "exp": 150,
        "drops": ["Saiyan Armor", "Frieza Soldier"],
    },
    {
        "name": "Zabuza Momochi",
        "hp": 2600, "dmg": 90,
        "yens": 14000, "gems": 1200, "crystals": 80,
        "tickets": 6, "skill_points": 25, "exp": 200,
        "drops": ["Kunai", "Chunin Flak Jacket"],
    },
    {
        "name": "Renji Abarai",
        "hp": 3600, "dmg": 130,
        "yens": 21000, "gems": 1700, "crystals": 110,
        "tickets": 8, "skill_points": 30, "exp": 280,
        "drops": ["Zanpakuto (Shikai)", "Shihakusho"],
    },
    
    # --- Tier 2 Bosses ---
    {
        "name": "Beerus Avatar",
        "hp": 5200, "dmg": 180,
        "yens": 32000, "gems": 2600, "crystals": 170,
        "tickets": 10, "skill_points": 40, "exp": 400,
        "drops": ["God Armor", "Hakai Orb"],
    },
    {
        "name": "Goku Black Rift",
        "hp": 7400, "dmg": 240,
        "yens": 47000, "gems": 3800, "crystals": 240,
        "tickets": 12, "skill_points": 55, "exp": 550,
        "drops": ["Black Kamehameha Blade", "Time Ring"],
    },
    
    # --- Tier 3 Bosses ---
    {
        "name": "Zamasu Infinite",
        "hp": 9800, "dmg": 310,
        "yens": 62000, "gems": 4900, "crystals": 310,
        "tickets": 15, "skill_points": 70, "exp": 800,
        "drops": ["Fusion Zamasu", "Divine Robes"],
    },
    {
        "name": "Jiren Full Power",
        "hp": 13500, "dmg": 400,
        "yens": 88000, "gems": 6700, "crystals": 410,
        "tickets": 18, "skill_points": 90, "exp": 1100,
        "drops": ["Pride Trooper Armor", "Power Impact Scroll"],
    },
    
    # --- Tier 4 Bosses ---
    {
        "name": "Yhwach (Almighty)",
        "hp": 18000, "dmg": 520,
        "yens": 120000, "gems": 9000, "crystals": 600,
        "tickets": 25, "skill_points": 120, "exp": 1500,
        "drops": ["Quincy Cross", "Almighty Eye"],
    },
    {
        "name": "Kaido (Hybrid)",
        "hp": 24000, "dmg": 680,
        "yens": 160000, "gems": 12000, "crystals": 800,
        "tickets": 30, "skill_points": 150, "exp": 2000,
        "drops": ["Kanabo Club", "Uo Uo no Mi"],
    },
]


# -------------------------------------------------------------
# 4. FACTIONS & ELEMENTAL AFFINITIES
# -------------------------------------------------------------
# Used for character tags and future synergy bonuses.

FACTIONS = {
    "Z_FIGHTER": {"name": "Z-Fighter", "bonus": "None"},
    "SAIYAN": {"name": "Saiyan", "bonus": "+5% HP"},
    "NAMEKIAN": {"name": "Namekian", "bonus": "+5% HP Regen"},
    "NINJA": {"name": "Shinobi", "bonus": "+5% SPD"},
    "SOUL_REAPER": {"name": "Soul Reaper", "bonus": "+5% ATK"},
    "PIRATE": {"name": "Pirate", "bonus": "+5% Crit"},
    "MARINE": {"name": "Marine", "bonus": "+5% DEF"},
    "GOD": {"name": "Divine", "bonus": "+10% All Stats"},
}

ELEMENTS = {
    "FIRE": {"name": "Fire", "color": "#FF0000", "strong_against": "WIND"},
    "WATER": {"name": "Water", "color": "#0000FF", "strong_against": "FIRE"},
    "WIND": {"name": "Wind", "color": "#00FF00", "strong_against": "EARTH"},
    "EARTH": {"name": "Earth", "color": "#8B4513", "strong_against": "LIGHTNING"},
    "LIGHTNING": {"name": "Lightning", "color": "#FFFF00", "strong_against": "WATER"},
    "LIGHT": {"name": "Light", "color": "#FFFFFF", "strong_against": "DARK"},
    "DARK": {"name": "Dark", "color": "#000000", "strong_against": "LIGHT"},
}


# -------------------------------------------------------------
# 5. MASSIVE CHARACTER ROSTER (275+ Total)
# -------------------------------------------------------------
# This massive list contains all characters across the 7 rarities.
# We use the dictionary format for maximum detail.

CHARACTERS = []

# =============================================================
# OMNI KINGS & MULTIVERSAL GODS (33 Characters)
# The absolute pinnacle of power. Drop rate: 1%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (12) ---
    {"name": "Omni King Zeno", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1800, "atk": 520, "spd": 100, "crit": 35, "desc": "The supreme ruler of all 12 universes. He can erase anything with a thought."},
    {"name": "Omni King Future Zeno", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1750, "atk": 510, "spd": 98, "crit": 34, "desc": "The Zeno from the erased Future Trunks timeline. Equally as terrifying."},
    {"name": "Omni King Zalama", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1900, "atk": 540, "spd": 95, "crit": 38, "desc": "The legendary Dragon God who created the Super Dragon Balls."},
    {"name": "Omni King Super Shenron", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 2000, "atk": 550, "spd": 90, "crit": 40, "desc": "The golden cosmic dragon that spans entire galaxies."},
    {"name": "Omni King Vegeks", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1850, "atk": 525, "spd": 96, "crit": 36, "desc": "A fusion of the Omni King and a Saiyan, wielding absolute power."},
    {"name": "Omni King Cereal", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1780, "atk": 515, "spd": 97, "crit": 34, "desc": "The Omni King of Universe 7, hidden away on Planet Cereal."},
    {"name": "Omni King Yemma", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1720, "atk": 505, "spd": 99, "crit": 32, "desc": "The judge of the dead, wielding the power of the Omni King."},
    {"name": "Omni King Constellation", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1880, "atk": 535, "spd": 94, "crit": 37, "desc": "A cosmic entity made of pure starlight and divine energy."},
    {"name": "Omni King Universe 11", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1820, "atk": 522, "spd": 93, "crit": 35, "desc": "The Omni King who presides over the Pride Troopers' universe."},
    {"name": "Omni King Time", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 1860, "atk": 528, "spd": 101, "crit": 36, "desc": "The Omni King who controls the flow of time itself."},
    {"name": "Omni King Grand Priest", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 2050, "atk": 560, "spd": 105, "crit": 42, "desc": "The father of all Angels and the strongest attendant to Zeno."},
    {"name": "Super Shenron True Form", "rarity": "omni", "faction": "GOD", "element": "LIGHT", "hp": 2200, "atk": 575, "spd": 98, "crit": 45, "desc": "The true, unrestrained form of the divine dragon."},

    # --- Naruto (7) ---
    {"name": "Hagoromo Otsutsuki", "rarity": "omni", "faction": "NINJA", "element": "LIGHT", "hp": 1950, "atk": 545, "spd": 105, "crit": 42, "desc": "The Sage of Six Paths. The father of modern ninjutsu and the Jinchuriki."},
    {"name": "Kaguya Otsutsuki", "rarity": "omni", "faction": "NINJA", "element": "DARK", "hp": 2100, "atk": 560, "spd": 102, "crit": 40, "desc": "The Rabbit Goddess. The progenitor of all chakra and the final villain of Shippuden."},
    {"name": "Naruto (Baryon Mode)", "rarity": "omni", "faction": "NINJA", "element": "LIGHT", "hp": 1880, "atk": 555, "spd": 110, "crit": 45, "desc": "The Seventh Hokage, burning his own life force to create a new form of energy."},
    {"name": "Sasuke (Indra's Arrow)", "rarity": "omni", "faction": "NINJA", "element": "LIGHTNING", "hp": 1850, "atk": 570, "spd": 108, "crit": 44, "desc": "The shadow Hokage, channeling the full power of Indra into a single devastating arrow."},
    {"name": "Isshiki Otsutsuki", "rarity": "omni", "faction": "NINJA", "element": "DARK", "hp": 2000, "atk": 580, "spd": 100, "crit": 41, "desc": "The strongest Otsutsuki to ever exist. His Sukunahikona shrinks anything in an instant."},
    {"name": "Naruto (Six Paths Baryon)", "rarity": "omni", "faction": "NINJA", "element": "LIGHT", "hp": 1950, "atk": 570, "spd": 115, "crit": 46, "desc": "Naruto combining Six Paths Sage Mode with Baryon chakra."},
    {"name": "Sasuke (Rinnegan Mastered)", "rarity": "omni", "faction": "NINJA", "element": "LIGHTNING", "hp": 1900, "atk": 565, "spd": 112, "crit": 44, "desc": "Sasuke mastering all six paths of the Rinnegan."},

    # --- Bleach (7) ---
    {"name": "Soul King", "rarity": "omni", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 2200, "atk": 590, "spd": 95, "crit": 45, "desc": "The linchpin of the three worlds. His power stabilizes the flow of souls."},
    {"name": "Yhwach (Almighty)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "DARK", "hp": 2050, "atk": 600, "spd": 100, "crit": 46, "desc": "The Quincy King. He can see and rewrite every possible future."},
    {"name": "Ichigo (True Bankai)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 1900, "atk": 565, "spd": 112, "crit": 42, "desc": "The hybrid Shinigami/Quincy/Hollow, wielding the true power of Zangetsu."},
    {"name": "Aizen (Hogyoku)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1980, "atk": 575, "spd": 105, "crit": 44, "desc": "The traitor captain, fused with the Hogyoku and reaching the limits of godhood."},
    {"name": "Yamamoto (Bankai)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 1850, "atk": 585, "spd": 102, "crit": 43, "desc": "The Captain-Commander. His Zanka no Tachi can incinerate all of Soul Society."},
    {"name": "Ichigo (True Bankai Horn)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "DARK", "hp": 2000, "atk": 580, "spd": 110, "crit": 43, "desc": "Ichigo unleashing the full power of his Hollow and Quincy heritage."},
    {"name": "Aizen (Final Fusion)", "rarity": "omni", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1980, "atk": 585, "spd": 108, "crit": 45, "desc": "Aizen fully transcending Shinigami and Hollow limits."},

    # --- One Piece (7) ---
    {"name": "Joyboy", "rarity": "omni", "faction": "PIRATE", "element": "LIGHT", "hp": 2100, "atk": 580, "spd": 108, "crit": 44, "desc": "The legendary figure from the Void Century. The first pirate and the original Gear 5 user."},
    {"name": "Imu", "rarity": "omni", "faction": "MARINE", "element": "DARK", "hp": 2150, "atk": 590, "spd": 105, "crit": 45, "desc": "The hidden ruler of the World Government. Sitting on the Empty Throne, dictating history."},
    {"name": "Gol D. Roger", "rarity": "omni", "faction": "PIRATE", "element": "LIGHT", "hp": 1950, "atk": 570, "spd": 110, "crit": 42, "desc": "The King of the Pirates. He conquered the Grand Line and started the Great Pirate Era."},
    {"name": "Whitebeard (Prime)", "rarity": "omni", "faction": "PIRATE", "element": "EARTH", "hp": 2300, "atk": 600, "spd": 95, "crit": 43, "desc": "Edward Newgate. The man who could destroy the world with the Gura Gura no Mi."},
    {"name": "Luffy (Gear 5)", "rarity": "omni", "faction": "PIRATE", "element": "LIGHT", "hp": 2000, "atk": 575, "spd": 115, "crit": 46, "desc": "The Warrior of Liberation. The Nika fruit awakens, giving him rubberhose reality-bending powers."},
    {"name": "Luffy (Joyboy Awakened)", "rarity": "omni", "faction": "PIRATE", "element": "LIGHT", "hp": 2050, "atk": 590, "spd": 118, "crit": 48, "desc": "The true Nika, bringing liberation and laughter to the world."},
    {"name": "Blackbeard (Three Fruits)", "rarity": "omni", "faction": "PIRATE", "element": "DARK", "hp": 2150, "atk": 595, "spd": 100, "crit": 44, "desc": "Marshall D. Teach, having stolen a third Devil Fruit."},
])

# =============================================================
# SP+ (SUPER POWERFUL) (27 Characters)
# Transcendent characters just below Omni tier. Drop rate: 3%
# =============================================================
CHARACTERS.extend([
    # --- Naruto (8) ---
    {"name": "Madara (Six Paths)", "rarity": "sp_plus", "faction": "NINJA", "element": "DARK", "hp": 1650, "atk": 490, "spd": 98, "crit": 35, "desc": "The ghost of the Uchiha, wielding the Ten-Tails and the Rinnegan."},
    {"name": "Obito (Ten-Tails)", "rarity": "sp_plus", "faction": "NINJA", "element": "DARK", "hp": 1700, "atk": 485, "spd": 95, "crit": 34, "desc": "The masked man, becoming the Jinchuriki of the Ten-Tails."},
    {"name": "Might Guy (8th Gate)", "rarity": "sp_plus", "faction": "NINJA", "element": "FIRE", "hp": 1500, "atk": 550, "spd": 105, "crit": 38, "desc": "The Blue Beast of Konoha, opening the final gate of death to unleash Night Guy."},
    {"name": "Kakashi (DMS)", "rarity": "sp_plus", "faction": "NINJA", "element": "LIGHTNING", "hp": 1600, "atk": 495, "spd": 100, "crit": 36, "desc": "The Copy Ninja, temporarily wielding both of Obito's Mangekyou Sharingan."},
    {"name": "Hashirama (Sage)", "rarity": "sp_plus", "faction": "NINJA", "element": "EARTH", "hp": 1750, "atk": 475, "spd": 92, "crit": 33, "desc": "The God of Shinobi, entering Sage Mode with his massive Wood Release."},
    {"name": "Madara (Dual Rinnegan)", "rarity": "sp_plus", "faction": "NINJA", "element": "DARK", "hp": 1750, "atk": 495, "spd": 96, "crit": 35, "desc": "Madara with both Rinnegan restored."},
    {"name": "Obito (Six Paths)", "rarity": "sp_plus", "faction": "NINJA", "element": "DARK", "hp": 1720, "atk": 485, "spd": 98, "crit": 34, "desc": "Obito wielding the full power of the Ten-Tails."},
    {"name": "Kaguya (True Form)", "rarity": "sp_plus", "faction": "NINJA", "element": "DARK", "hp": 1800, "atk": 515, "spd": 94, "crit": 38, "desc": "The Rabbit Goddess at her absolute peak."},

    # --- Bleach (7) ---
    {"name": "Ichibe Hyosube", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 1680, "atk": 500, "spd": 96, "crit": 35, "desc": "The Monk Who Calls the Real Name. Leader of the Royal Guard."},
    {"name": "Kenpachi (Bankai)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 1800, "atk": 520, "spd": 90, "crit": 37, "desc": "The Kenpachi. A pure powerhouse whose Bankai turns him into a red-skinned demon."},
    {"name": "Toshiro (Mature)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "WATER", "hp": 1550, "atk": 490, "spd": 102, "crit": 36, "desc": "The ice prodigy, using his matured Bankai to freeze concepts themselves."},
    {"name": "Urahara (Bankai)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "WIND", "hp": 1580, "atk": 485, "spd": 104, "crit": 35, "desc": "The shopkeeper, a genius whose Bankai can restructure anything it touches."},
    {"name": "Shunsui (Bankai)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1620, "atk": 480, "spd": 98, "crit": 34, "desc": "The new Captain-Commander, his Bankai forces everyone into a tragic play."},
    {"name": "Yhwach (Soul King Absorbed)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1850, "atk": 530, "spd": 100, "crit": 39, "desc": "Yhwach after absorbing the Soul King."},
    {"name": "Ichibe (True Power)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 1700, "atk": 510, "spd": 102, "crit": 36, "desc": "The Monk Who Calls the Real Name."},

    # --- One Piece (7) ---
    {"name": "Kaido (Hybrid)", "rarity": "sp_plus", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1900, "atk": 510, "spd": 95, "crit": 36, "desc": "The Strongest Creature. The Azure Dragon of Wano."},
    {"name": "Big Mom", "rarity": "sp_plus", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1950, "atk": 500, "spd": 88, "crit": 35, "desc": "The Soul Queen. She can steal lifespans with Prometheus and Zeus."},
    {"name": "Shanks", "rarity": "sp_plus", "faction": "PIRATE", "element": "LIGHT", "hp": 1600, "atk": 530, "spd": 108, "crit": 38, "desc": "The Red-Haired Emperor. His Conqueror's Haki can damage physical ships."},
    {"name": "Mihawk", "rarity": "sp_plus", "faction": "PIRATE", "element": "WIND", "hp": 1550, "atk": 540, "spd": 105, "crit": 39, "desc": "The World's Strongest Swordsman. Wields the Black Blade Yoru."},
    {"name": "Blackbeard (Gura)", "rarity": "sp_plus", "faction": "PIRATE", "element": "DARK", "hp": 1850, "atk": 495, "spd": 92, "crit": 34, "desc": "Marshall D. Teach. The only man in history with two Devil Fruits."},
    {"name": "Kaido (Awakened Dragon)", "rarity": "sp_plus", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1950, "atk": 515, "spd": 96, "crit": 36, "desc": "Kaido's awakened Azure Dragon form."},
    {"name": "Big Mom (Awakened Soul)", "rarity": "sp_plus", "faction": "PIRATE", "element": "FIRE", "hp": 2000, "atk": 505, "spd": 90, "crit": 35, "desc": "Big Mom with all her Homies combined."},

    # --- Dragon Ball (5) ---
    {"name": "Vegeta (Ultra Ego Mastered)", "rarity": "sp_plus", "faction": "SAIYAN", "element": "DARK", "hp": 1700, "atk": 505, "spd": 98, "crit": 36, "desc": "Vegeta fully embracing the power of destruction."},
    {"name": "Frieza (Black Final Form)", "rarity": "sp_plus", "faction": "PIRATE", "element": "DARK", "hp": 1650, "atk": 520, "spd": 102, "crit": 38, "desc": "Frieza's true ultimate form."},
    {"name": "Goku (Omni Instinct)", "rarity": "sp_plus", "faction": "SAIYAN", "element": "LIGHT", "hp": 1680, "atk": 510, "spd": 105, "crit": 37, "desc": "A hypothetical form beyond Mastered Ultra Instinct."},
    {"name": "Kenpachi (Bankai Unsealed)", "rarity": "sp_plus", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 1820, "atk": 525, "spd": 92, "crit": 38, "desc": "Kenpachi Zaraki at maximum power."},
    {"name": "Shanks (Divine Haki)", "rarity": "sp_plus", "faction": "PIRATE", "element": "LIGHT", "hp": 1650, "atk": 540, "spd": 110, "crit": 40, "desc": "Shanks utilizing the highest level of Conqueror's Haki."},
])

# =============================================================
# MYTHICAL (55 Characters)
# Top tier fighters who can destroy islands. Drop rate: 7%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (25) ---
    {"name": "Ultra Instinct Goku", "rarity": "mythical", "faction": "SAIYAN", "element": "LIGHT", "hp": 1280, "atk": 410, "spd": 98, "crit": 32, "desc": "Goku's body reacting autonomously without conscious thought."},
    {"name": "Ultra Ego Vegeta", "rarity": "mythical", "faction": "SAIYAN", "element": "DARK", "hp": 1350, "atk": 420, "spd": 85, "crit": 30, "desc": "Vegeta's God of Destruction form, fueled by damage taken."},
    {"name": "Gohan Beast", "rarity": "mythical", "faction": "SAIYAN", "element": "LIGHT", "hp": 1260, "atk": 405, "spd": 92, "crit": 31, "desc": "Gohan's ultimate awakened form, unleashing a massive Special Beam Cannon."},
    {"name": "Orange Piccolo", "rarity": "mythical", "faction": "NAMEKIAN", "element": "EARTH", "hp": 1230, "atk": 395, "spd": 90, "crit": 29, "desc": "Piccolo's potential unlocked by Shenron, turning him orange."},
    {"name": "Black Frieza", "rarity": "mythical", "faction": "PIRATE", "element": "DARK", "hp": 1420, "atk": 430, "spd": 96, "crit": 35, "desc": "Frieza after 10 years of training in the Hyperbolic Time Chamber."},
    {"name": "Beerus", "rarity": "mythical", "faction": "GOD", "element": "DARK", "hp": 1200, "atk": 360, "spd": 85, "crit": 26, "desc": "The God of Destruction of Universe 7."},
    {"name": "Whis", "rarity": "mythical", "faction": "GOD", "element": "LIGHT", "hp": 1300, "atk": 370, "spd": 95, "crit": 28, "desc": "Beerus's angel attendant and Ultra Instinct master."},
    {"name": "Vados", "rarity": "mythical", "faction": "GOD", "element": "LIGHT", "hp": 1290, "atk": 372, "spd": 94, "crit": 29, "desc": "Champa's angel attendant and Whis's sister."},
    {"name": "Broly Full Power", "rarity": "mythical", "faction": "SAIYAN", "element": "WIND", "hp": 1500, "atk": 445, "spd": 82, "crit": 33, "desc": "The Legendary Super Saiyan, overflowing with uncontrollable rage."},
    {"name": "Vegito Blue", "rarity": "mythical", "faction": "SAIYAN", "element": "LIGHT", "hp": 1380, "atk": 425, "spd": 94, "crit": 32, "desc": "The Potara fusion of Goku and Vegeta in Super Saiyan Blue."},
    {"name": "SSJ4 Gogeta", "rarity": "mythical", "faction": "SAIYAN", "element": "FIRE", "hp": 1400, "atk": 435, "spd": 92, "crit": 34, "desc": "The Fusion Dance of Goku and Vegeta in Super Saiyan 4."},
    {"name": "Grand Minister", "rarity": "mythical", "faction": "GOD", "element": "LIGHT", "hp": 1350, "atk": 415, "spd": 97, "crit": 30, "desc": "The highest-ranking angel, attendant to Zeno."},
    {"name": "Janemba", "rarity": "mythical", "faction": "DARK", "element": "DARK", "hp": 1240, "atk": 385, "spd": 88, "crit": 28, "desc": "A demon made of pure evil, capable of warping dimensions."},
    {"name": "Golden Cooler", "rarity": "mythical", "faction": "PIRATE", "element": "LIGHT", "hp": 1310, "atk": 405, "spd": 90, "crit": 31, "desc": "Frieza's brother, achieving a golden form stronger than Frieza's."},
    {"name": "Fusion Zamasu", "rarity": "mythical", "faction": "GOD", "element": "LIGHT", "hp": 1420, "atk": 428, "spd": 89, "crit": 32, "desc": "The fusion of Goku Black and Future Zamasu, becoming immortal."},
    {"name": "Omega Shenron", "rarity": "mythical", "faction": "DARK", "element": "DARK", "hp": 1390, "atk": 420, "spd": 87, "crit": 33, "desc": "The fusion of all 7 Shadow Dragons, threatening the universe."},
    {"name": "Kefla SSJ2", "rarity": "mythical", "faction": "SAIYAN", "element": "FIRE", "hp": 1250, "atk": 395, "spd": 93, "crit": 30, "desc": "The Potara fusion of Caulifla and Kale, in Super Saiyan 2."},
    {"name": "Moro (Full Power)", "rarity": "mythical", "faction": "DARK", "element": "EARTH", "hp": 1360, "atk": 415, "spd": 88, "crit": 31, "desc": "The planet-eating sorcerer, merging with the Earth."},
    {"name": "Goku Black Rosé", "rarity": "mythical", "faction": "GOD", "element": "DARK", "hp": 1270, "atk": 400, "spd": 91, "crit": 32, "desc": "Zamasu in Goku's body, wielding Super Saiyan Rosé."},
    {"name": "Dark Broly", "rarity": "mythical", "faction": "SAIYAN", "element": "DARK", "hp": 1480, "atk": 442, "spd": 84, "crit": 34, "desc": "A corrupted version of Broly from a dark timeline."},
    {"name": "Broly (LSSJ2)", "rarity": "mythical", "faction": "SAIYAN", "element": "WIND", "hp": 1550, "atk": 450, "spd": 85, "crit": 34, "desc": "Broly ascending beyond Legendary Super Saiyan."},
    {"name": "Gogeta (SSJ4 Limit Breaker)", "rarity": "mythical", "faction": "SAIYAN", "element": "FIRE", "hp": 1480, "atk": 460, "spd": 96, "crit": 35, "desc": "The ultimate fusion, breaking all Saiyan limits."},
    {"name": "Vegito (Super Saiyan God)", "rarity": "mythical", "faction": "SAIYAN", "element": "LIGHT", "hp": 1450, "atk": 445, "spd": 98, "crit": 33, "desc": "Vegito wielding God Ki."},
    {"name": "Gohan (Beast Ultimate)", "rarity": "mythical", "faction": "SAIYAN", "element": "LIGHT", "hp": 1400, "atk": 435, "spd": 95, "crit": 34, "desc": "Gohan Beast unleashing the full power of his rage."},
    {"name": "Cell Max", "rarity": "mythical", "faction": "DARK", "element": "EARTH", "hp": 1600, "atk": 455, "spd": 82, "crit": 30, "desc": "The monstrous, uncontrollable bio-android."},

    # --- Naruto (10) ---
    {"name": "Pain (Six Paths)", "rarity": "mythical", "faction": "NINJA", "element": "DARK", "hp": 1220, "atk": 385, "spd": 90, "crit": 30, "desc": "Nagato controlling six corpses with the Rinnegan."},
    {"name": "Itachi Uchiha", "rarity": "mythical", "faction": "NINJA", "element": "FIRE", "hp": 1180, "atk": 390, "spd": 96, "crit": 32, "desc": "The Uchiha prodigy, master of genjutsu and Amaterasu."},
    {"name": "Minato Namikaze", "rarity": "mythical", "faction": "NINJA", "element": "WIND", "hp": 1200, "atk": 380, "spd": 102, "crit": 31, "desc": "The Yellow Flash of the Leaf, master of the Flying Raijin."},
    {"name": "Jiraiya (Sage)", "rarity": "mythical", "faction": "NINJA", "element": "EARTH", "hp": 1250, "atk": 375, "spd": 88, "crit": 29, "desc": "The Pervy Sage, using Sage Mode with the Toads."},
    {"name": "Tsunade (Byakugou)", "rarity": "mythical", "faction": "NINJA", "element": "EARTH", "hp": 1350, "atk": 370, "spd": 85, "crit": 28, "desc": "The Fifth Hokage, releasing her 100 Healings Seal."},
    {"name": "Itachi (Edo Tensei)", "rarity": "mythical", "faction": "NINJA", "element": "FIRE", "hp": 1320, "atk": 410, "spd": 96, "crit": 33, "desc": "Itachi with infinite chakra and immortality."},
    {"name": "Nagato (Full Power)", "rarity": "mythical", "faction": "NINJA", "element": "DARK", "hp": 1380, "atk": 425, "spd": 88, "crit": 31, "desc": "The original wielder of the Rinnegan."},
    {"name": "Hashirama (Sage Mastered)", "rarity": "mythical", "faction": "NINJA", "element": "EARTH", "hp": 1450, "atk": 400, "spd": 90, "crit": 30, "desc": "The God of Shinobi at his absolute peak."},
    {"name": "Tobirama (Edo)", "rarity": "mythical", "faction": "NINJA", "element": "WATER", "hp": 1300, "atk": 405, "spd": 98, "crit": 32, "desc": "The fastest ninja of his era."},
    {"name": "Minato (Edo KCM)", "rarity": "mythical", "faction": "NINJA", "element": "LIGHT", "hp": 1350, "atk": 415, "spd": 105, "crit": 34, "desc": "The Yellow Flash, empowered by Kurama."},

    # --- Bleach (10) ---
    {"name": "Ulquiorra (Segunda)", "rarity": "mythical", "faction": "DARK", "element": "DARK", "hp": 1240, "atk": 400, "spd": 94, "crit": 32, "desc": "The Cuatro Espada, using his Segunda Etapa form."},
    {"name": "Grimmjow (Pantera)", "rarity": "mythical", "faction": "DARK", "element": "WIND", "hp": 1280, "atk": 395, "spd": 90, "crit": 30, "desc": "The Sexta Espada, releasing his Panther Resurreccion."},
    {"name": "Byakuya (Bankai)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "WIND", "hp": 1190, "atk": 385, "spd": 98, "crit": 31, "desc": "The Captain of Squad 6, using Senbonzakura Kageyoshi."},
    {"name": "Toshiro (Bankai)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "WATER", "hp": 1210, "atk": 380, "spd": 92, "crit": 29, "desc": "The Captain of Squad 10, using Daiguren Hyorinmaru."},
    {"name": "Renji (Bankai)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 1260, "atk": 390, "spd": 88, "crit": 28, "desc": "The Lieutenant of Squad 6, using Soo Zabimaru."},
    {"name": "Uryu (Antithesis)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 1280, "atk": 420, "spd": 94, "crit": 33, "desc": "Uryu using his Schrift to reverse events."},
    {"name": "Haschwalth (Balance)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1350, "atk": 430, "spd": 92, "crit": 35, "desc": "Yhwach's other half, redirecting misfortune."},
    {"name": "Shunsui (Bankai Full)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1310, "atk": 415, "spd": 95, "crit": 31, "desc": "The Captain-Commander using Katen Kyokotsu Karamatsu Shinju."},
    {"name": "Ukitake (Mimihagi)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 1400, "atk": 400, "spd": 88, "crit": 29, "desc": "Ukitake infused with the power of the Soul King's right hand."},
    {"name": "Unohana (Yachiru)", "rarity": "mythical", "faction": "SOUL_REAPER", "element": "DARK", "hp": 1380, "atk": 440, "spd": 90, "crit": 32, "desc": "The first Kenpachi, master of all sword styles."},

    # --- One Piece (10) ---
    {"name": "Roronoa Zoro", "rarity": "mythical", "faction": "PIRATE", "element": "WIND", "hp": 1300, "atk": 405, "spd": 95, "crit": 33, "desc": "The Pirate Hunter, using Advanced Conqueror's Haki."},
    {"name": "Vinsmoke Sanji", "rarity": "mythical", "faction": "PIRATE", "element": "FIRE", "hp": 1250, "atk": 395, "spd": 98, "crit": 32, "desc": "Black Leg Sanji, using Ifrit Jambe."},
    {"name": "Trafalgar Law", "rarity": "mythical", "faction": "PIRATE", "element": "DARK", "hp": 1200, "atk": 380, "spd": 94, "crit": 30, "desc": "The Surgeon of Death, master of the Ope Ope no Mi."},
    {"name": "Eustass Kid", "rarity": "mythical", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1280, "atk": 400, "spd": 88, "crit": 31, "desc": "The Captain of the Kid Pirates, using his Magnet Fruit."},
    {"name": "Sabo (Flame)", "rarity": "mythical", "faction": "PIRATE", "element": "FIRE", "hp": 1240, "atk": 390, "spd": 92, "crit": 30, "desc": "The Chief of Staff of the Revolutionary Army, inheriting Ace's fruit."},
    {"name": "Zoro (King of Hell)", "rarity": "mythical", "faction": "PIRATE", "element": "DARK", "hp": 1360, "atk": 435, "spd": 94, "crit": 36, "desc": "Zoro wielding Advanced Conqueror's Haki."},
    {"name": "Sanji (Ifrit Jambe)", "rarity": "mythical", "faction": "PIRATE", "element": "FIRE", "hp": 1300, "atk": 420, "spd": 102, "crit": 34, "desc": "Sanji's ultimate flame technique."},
    {"name": "Law (Awakening)", "rarity": "mythical", "faction": "PIRATE", "element": "LIGHT", "hp": 1280, "atk": 410, "spd": 96, "crit": 33, "desc": "Trafalgar Law using K-Room."},
    {"name": "Kidd (Assign)", "rarity": "mythical", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1340, "atk": 425, "spd": 90, "crit": 32, "desc": "Eustass Kid using his awakened magnetic powers."},
    {"name": "Sabo (Flame Emperor)", "rarity": "mythical", "faction": "PIRATE", "element": "FIRE", "hp": 1320, "atk": 415, "spd": 95, "crit": 33, "desc": "Sabo, master of the Mera Mera no Mi."},
])

# =============================================================
# LEGENDARY (55 Characters)
# Highly skilled captains and heroes. Drop rate: 14%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (25) ---
    {"name": "Super Saiyan Blue Goku", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 980, "atk": 340, "spd": 88, "crit": 25, "desc": "Goku combining God Ki with Super Saiyan."},
    {"name": "SSJ3 Goku", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 950, "atk": 330, "spd": 82, "crit": 24, "desc": "Goku pushing Super Saiyan to its limits."},
    {"name": "Majin Vegeta", "rarity": "legendary", "faction": "SAIYAN", "element": "DARK", "hp": 970, "atk": 335, "spd": 84, "crit": 25, "desc": "Vegeta allowing himself to be controlled by Babidi."},
    {"name": "Future Gohan", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 920, "atk": 320, "spd": 80, "crit": 23, "desc": "The one-armed warrior of the future timeline."},
    {"name": "Jiren Beyond Limits", "rarity": "legendary", "faction": "MARINE", "element": "LIGHT", "hp": 1050, "atk": 355, "spd": 86, "crit": 26, "desc": "Jiren breaking his limits against MUI Goku."},
    {"name": "Super Buu", "rarity": "legendary", "faction": "DARK", "element": "DARK", "hp": 940, "atk": 325, "spd": 79, "crit": 24, "desc": "Majin Buu after absorbing Gotenks and Piccolo."},
    {"name": "Android 17 MVP", "rarity": "legendary", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 910, "atk": 315, "spd": 90, "crit": 23, "desc": "Android 17, the MVP of the Tournament of Power."},
    {"name": "Hit", "rarity": "legendary", "faction": "DARK", "element": "LIGHT", "hp": 930, "atk": 322, "spd": 92, "crit": 24, "desc": "The Legendary Assassin of Universe 6, master of Time Skip."},
    {"name": "Toppo Destroyer", "rarity": "legendary", "faction": "MARINE", "element": "DARK", "hp": 960, "atk": 330, "spd": 82, "crit": 25, "desc": "Toppo abandoning justice to become a God of Destruction."},
    {"name": "Metal Cooler", "rarity": "legendary", "faction": "PIRATE", "element": "LIGHT", "hp": 900, "atk": 312, "spd": 80, "crit": 22, "desc": "Cooler's metal form, connected to the Big Gete Star."},
    {"name": "Broly DBZ", "rarity": "legendary", "faction": "SAIYAN", "element": "WIND", "hp": 1000, "atk": 345, "spd": 78, "crit": 26, "desc": "The original Legendary Super Saiyan from Movie 8."},
    {"name": "Gogeta Blue", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 990, "atk": 342, "spd": 87, "crit": 26, "desc": "The Fusion Dance fusion of Goku and Vegeta in Blue."},
    {"name": "Vegeta SSJ2", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 940, "atk": 322, "spd": 83, "crit": 24, "desc": "Vegeta during the Majin Buu saga."},
    {"name": "Goku SSJ God", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 970, "atk": 328, "spd": 85, "crit": 25, "desc": "Goku tapping into the power of the gods."},
    {"name": "Super Saiyan 4 Goku", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 985, "atk": 335, "spd": 84, "crit": 25, "desc": "Goku combining Super Saiyan and Great Ape power."},
    {"name": "Super Saiyan 4 Vegeta", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 975, "atk": 332, "spd": 83, "crit": 25, "desc": "Vegeta's SSJ4 form from GT."},
    {"name": "Golden Frieza", "rarity": "legendary", "faction": "PIRATE", "element": "DARK", "hp": 945, "atk": 328, "spd": 85, "crit": 24, "desc": "Frieza's new form in Resurrection F."},
    {"name": "Mystic Gohan", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 955, "atk": 330, "spd": 82, "crit": 24, "desc": "Gohan with his potential unlocked by Elder Kai."},
    {"name": "Gotenks SSJ3", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 930, "atk": 320, "spd": 86, "crit": 24, "desc": "The fusion of Goten and Trunks in SSJ3."},
    {"name": "Kale SSJ Berserk", "rarity": "legendary", "faction": "SAIYAN", "element": "DARK", "hp": 920, "atk": 318, "spd": 81, "crit": 23, "desc": "Kale's out-of-control Legendary Super Saiyan form."},
    {"name": "Goku (Kaioken x100)", "rarity": "legendary", "faction": "SAIYAN", "element": "FIRE", "hp": 1050, "atk": 360, "spd": 92, "crit": 27, "desc": "Goku pushing Kaioken to its absolute limit."},
    {"name": "Vegeta (Super Saiyan 3)", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 1080, "atk": 355, "spd": 88, "crit": 26, "desc": "Vegeta achieving SSJ3 in the anime."},
    {"name": "Future Trunks (SSJ Rage)", "rarity": "legendary", "faction": "SAIYAN", "element": "LIGHT", "hp": 1020, "atk": 365, "spd": 90, "crit": 28, "desc": "Trunks' rage awakening a new form."},
    {"name": "Piccolo (Orange Power)", "rarity": "legendary", "faction": "NAMEKIAN", "element": "EARTH", "hp": 1150, "atk": 345, "spd": 84, "crit": 25, "desc": "Piccolo's enhanced form."},
    {"name": "Android 21 (Transformed)", "rarity": "legendary", "faction": "Z_FIGHTER", "element": "DARK", "hp": 1000, "atk": 370, "spd": 86, "crit": 27, "desc": "The hunger-driven bio-android."},

    # --- Naruto (10) ---
    {"name": "Kakashi Hatake", "rarity": "legendary", "faction": "NINJA", "element": "LIGHTNING", "hp": 890, "atk": 305, "spd": 88, "crit": 23, "desc": "The Copy Ninja, wielder of the Sharingan."},
    {"name": "Sakura Haruno", "rarity": "legendary", "faction": "NINJA", "element": "EARTH", "hp": 920, "atk": 300, "spd": 85, "crit": 22, "desc": "The strongest kunoichi, mastering the Hundred Healings."},
    {"name": "Gaara (Kazekage)", "rarity": "legendary", "faction": "NINJA", "element": "EARTH", "hp": 950, "atk": 310, "spd": 80, "crit": 24, "desc": "The Fifth Kazekage, master of Sand."},
    {"name": "Rock Lee (8 Gates)", "rarity": "legendary", "faction": "NINJA", "element": "WIND", "hp": 880, "atk": 320, "spd": 95, "crit": 25, "desc": "The taijutsu master, opening the inner gates."},
    {"name": "Hinata Hyuga", "rarity": "legendary", "faction": "NINJA", "element": "LIGHT", "hp": 870, "atk": 295, "spd": 86, "crit": 23, "desc": "The Byakugan princess, using Twin Lion Fists."},
    {"name": "Kakashi (Six Paths)", "rarity": "legendary", "faction": "NINJA", "element": "LIGHTNING", "hp": 980, "atk": 340, "spd": 94, "crit": 26, "desc": "Kakashi with dual Kamui."},
    {"name": "Guy (8th Gate Full)", "rarity": "legendary", "faction": "NINJA", "element": "FIRE", "hp": 950, "atk": 380, "spd": 98, "crit": 29, "desc": "Might Guy opening the Gate of Death."},
    {"name": "Sakura (Byakugou Mastered)", "rarity": "legendary", "faction": "NINJA", "element": "EARTH", "hp": 1050, "atk": 330, "spd": 88, "crit": 24, "desc": "Sakura unleashing her full seal."},
    {"name": "Hinata (Hamura Chakra)", "rarity": "legendary", "faction": "NINJA", "element": "LIGHT", "hp": 970, "atk": 335, "spd": 92, "crit": 25, "desc": "Hinata with Hamura's chakra."},
    {"name": "Gaara (Shukaku Form)", "rarity": "legendary", "faction": "NINJA", "element": "EARTH", "hp": 1100, "atk": 325, "spd": 82, "crit": 23, "desc": "Gaara using his tailed beast."},

    # --- Bleach (10) ---
    {"name": "Rukia (Bankai)", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "WATER", "hp": 880, "atk": 310, "spd": 84, "crit": 24, "desc": "The Captain of Squad 13, using Hakka no Togame."},
    {"name": "Yasutora Sado", "rarity": "legendary", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 930, "atk": 315, "spd": 78, "crit": 22, "desc": "Chad, using his Fullbring powers."},
    {"name": "Orihime Inoue", "rarity": "legendary", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 860, "atk": 290, "spd": 88, "crit": 21, "desc": "The healer, rejecting reality with her Shun Shun Rikka."},
    {"name": "Uryu Ishida", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 890, "atk": 305, "spd": 86, "crit": 23, "desc": "The Last Quincy, using Antithesis."},
    {"name": "Rangiku Matsumoto", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "WIND", "hp": 870, "atk": 295, "spd": 82, "crit": 22, "desc": "The Lieutenant of Squad 10, using Haineko."},
    {"name": "Byakuya (True Bankai)", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "WIND", "hp": 1000, "atk": 350, "spd": 96, "crit": 26, "desc": "Byakuya's Senbonzakura perfected."},
    {"name": "Hitsugaya (Daiguren)", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "WATER", "hp": 990, "atk": 345, "spd": 94, "crit": 25, "desc": "The full power of Hyorinmaru."},
    {"name": "Renji (True Bankai)", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 1020, "atk": 355, "spd": 88, "crit": 24, "desc": "Renji's completed Soo Zabimaru."},
    {"name": "Rukia (Hakka no Togame)", "rarity": "legendary", "faction": "SOUL_REAPER", "element": "WATER", "hp": 960, "atk": 340, "spd": 90, "crit": 25, "desc": "Rukia's absolute zero Bankai."},
    {"name": "Grimmjow (Segunda)", "rarity": "legendary", "faction": "DARK", "element": "WIND", "hp": 1040, "atk": 360, "spd": 92, "crit": 27, "desc": "Grimmjow's secondary release."},

    # --- One Piece (10) ---
    {"name": "Nami", "rarity": "legendary", "faction": "PIRATE", "element": "LIGHTNING", "hp": 850, "atk": 285, "spd": 90, "crit": 22, "desc": "The Cat Burglar, wielding Zeus and the Clima-Tact."},
    {"name": "Nico Robin", "rarity": "legendary", "faction": "PIRATE", "element": "DARK", "hp": 880, "atk": 300, "spd": 84, "crit": 23, "desc": "The Devil Child, using Demonio Fleur."},
    {"name": "Franky", "rarity": "legendary", "faction": "PIRATE", "element": "LIGHTNING", "hp": 940, "atk": 310, "spd": 76, "crit": 22, "desc": "The Cyborg Shipwright, using Radical Beam."},
    {"name": "Brook", "rarity": "legendary", "faction": "PIRATE", "element": "WATER", "hp": 860, "atk": 295, "spd": 88, "crit": 24, "desc": "The Soul King, using freezing sword techniques."},
    {"name": "Jinbe", "rarity": "legendary", "faction": "PIRATE", "element": "WATER", "hp": 910, "atk": 305, "spd": 80, "crit": 23, "desc": "The Knight of the Sea, master of Fishman Karate."},
    {"name": "Yamato (Okuchi)", "rarity": "legendary", "faction": "PIRATE", "element": "WATER", "hp": 1080, "atk": 350, "spd": 86, "crit": 25, "desc": "Yamato using Kaido's fruit."},
    {"name": "Marco (Phoenix Awakened)", "rarity": "legendary", "faction": "PIRATE", "element": "FIRE", "hp": 1050, "atk": 335, "spd": 94, "crit": 24, "desc": "Marco's awakened phoenix flames."},
    {"name": "Katakuri (Mochi Awakened)", "rarity": "legendary", "faction": "PIRATE", "element": "EARTH", "hp": 1000, "atk": 345, "spd": 96, "crit": 28, "desc": "Katakuri's future sight."},
    {"name": "King (Lunarian)", "rarity": "legendary", "faction": "PIRATE", "element": "FIRE", "hp": 1020, "atk": 355, "spd": 90, "crit": 26, "desc": "The fire of the Lunarian race."},
    {"name": "Queen (Ancient Zoan)", "rarity": "legendary", "faction": "PIRATE", "element": "LIGHTNING", "hp": 1060, "atk": 340, "spd": 84, "crit": 23, "desc": "Queen's cyborg enhancements."},
])

# =============================================================
# END OF PART 1
# =============================================================
# Part 2 will contain:
# - Epic, Rare, Common Characters (Total 120 more characters)
# - Rarity Configurations & Gacha Rates
# - Weapons, Armors, & Shop Inventory
# - Skills, Titles, & Crafting Systems
# - Raid Bosses, Clan Perks, & Summons
# - Progression, Achievements, & Quests
# =============================================================
# =============================================================
# DRAGON BALL / ANIME CROSSOVER RPG — MASTER GAME DATA (PART 2)
# =============================================================

# =============================================================
# EPIC (55 Characters)
# Strong fighters, capable of destroying buildings. Drop rate: 20%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (20) ---
    {"name": "Gohan SSJ2", "rarity": "epic", "faction": "SAIYAN", "element": "LIGHT", "hp": 890, "atk": 250, "spd": 78, "crit": 20, "desc": "The teenage Gohan unleashing his hidden rage against Cell."},
    {"name": "Piccolo (Kami fused)", "rarity": "epic", "faction": "NAMEKIAN", "element": "EARTH", "hp": 860, "atk": 245, "spd": 76, "crit": 19, "desc": "Piccolo after merging with Kami."},
    {"name": "Perfect Cell", "rarity": "epic", "faction": "DARK", "element": "LIGHT", "hp": 900, "atk": 252, "spd": 77, "crit": 20, "desc": "Cell in his perfect form, having absorbed Android 17 and 18."},
    {"name": "Frieza 100%", "rarity": "epic", "faction": "PIRATE", "element": "DARK", "hp": 880, "atk": 248, "spd": 75, "crit": 19, "desc": "Frieza using his full power on Namek."},
    {"name": "Future Trunks SSJ", "rarity": "epic", "faction": "SAIYAN", "element": "LIGHT", "hp": 850, "atk": 242, "spd": 79, "crit": 20, "desc": "The time-traveling warrior from the apocalyptic future."},
    {"name": "Ultimate Gohan", "rarity": "epic", "faction": "SAIYAN", "element": "LIGHT", "hp": 895, "atk": 250, "spd": 76, "crit": 20, "desc": "Gohan with his potential unlocked by Old Kai."},
    {"name": "King Piccolo", "rarity": "epic", "faction": "NAMEKIAN", "element": "DARK", "hp": 830, "atk": 235, "spd": 74, "crit": 18, "desc": "The Demon King who terrorized Earth centuries ago."},
    {"name": "Android 16", "rarity": "epic", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 870, "atk": 244, "spd": 72, "crit": 19, "desc": "The gentle giant android programmed to kill Goku."},
    {"name": "Android 18", "rarity": "epic", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 840, "atk": 240, "spd": 80, "crit": 20, "desc": "The infinite energy android, now a member of the Z-Fighters."},
    {"name": "Master Roshi Max", "rarity": "epic", "faction": "Z_FIGHTER", "element": "WIND", "hp": 810, "atk": 232, "spd": 78, "crit": 18, "desc": "The Turtle Hermit using his Max Power form."},
    {"name": "Tien Shinhan Neo", "rarity": "epic", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 820, "atk": 235, "spd": 76, "crit": 19, "desc": "The three-eyed warrior using the Neo Tri-Beam."},
    {"name": "Raditz", "rarity": "epic", "faction": "SAIYAN", "element": "DARK", "hp": 800, "atk": 228, "spd": 74, "crit": 18, "desc": "Goku's ruthless older brother."},
    {"name": "Nappa", "rarity": "epic", "faction": "SAIYAN", "element": "EARTH", "hp": 810, "atk": 232, "spd": 72, "crit": 17, "desc": "The bald Saiyan elite who destroyed East City."},
    {"name": "Zarbon", "rarity": "epic", "faction": "PIRATE", "element": "LIGHT", "hp": 800, "atk": 228, "spd": 75, "crit": 18, "desc": "Frieza's handsome right-hand man."},
    {"name": "Dodoria", "rarity": "epic", "faction": "PIRATE", "element": "FIRE", "hp": 815, "atk": 232, "spd": 70, "crit": 17, "desc": "Frieza's brutal enforcer."},
    {"name": "Dabura", "rarity": "epic", "faction": "DARK", "element": "DARK", "hp": 860, "atk": 242, "spd": 76, "crit": 19, "desc": "The King of the Demon Realm."},
    {"name": "Supreme Kai", "rarity": "epic", "faction": "GOD", "element": "LIGHT", "hp": 835, "atk": 238, "spd": 78, "crit": 19, "desc": "Shin, the Supreme Kai of Universe 7."},
    {"name": "Kibito", "rarity": "epic", "faction": "GOD", "element": "LIGHT", "hp": 820, "atk": 234, "spd": 77, "crit": 18, "desc": "Supreme Kai's loyal attendant."},
    {"name": "Android 19", "rarity": "epic", "faction": "DARK", "element": "LIGHT", "hp": 825, "atk": 236, "spd": 73, "crit": 18, "desc": "The energy-absorbing android."},
    {"name": "Dr. Gero", "rarity": "epic", "faction": "DARK", "element": "LIGHT", "hp": 815, "atk": 232, "spd": 74, "crit": 18, "desc": "The mad scientist of the Red Ribbon Army."},

    # --- Naruto (15) ---
    {"name": "Shikamaru Nara", "rarity": "epic", "faction": "NINJA", "element": "DARK", "hp": 780, "atk": 220, "spd": 82, "crit": 18, "desc": "The genius tactician, master of Shadow Possession."},
    {"name": "Choji Akimichi", "rarity": "epic", "faction": "NINJA", "element": "EARTH", "hp": 850, "atk": 230, "spd": 68, "crit": 17, "desc": "The Akimichi clan heir, using Butterfly Mode."},
    {"name": "Kiba Inuzuka", "rarity": "epic", "faction": "NINJA", "element": "WIND", "hp": 790, "atk": 225, "spd": 80, "crit": 18, "desc": "The beast mimicry ninja, fighting alongside Akamaru."},
    {"name": "Neji Hyuga", "rarity": "epic", "faction": "NINJA", "element": "LIGHT", "hp": 800, "atk": 228, "spd": 78, "crit": 19, "desc": "The Byakugan prodigy, master of the Eight Trigrams."},
    {"name": "Temari", "rarity": "epic", "faction": "NINJA", "element": "WIND", "hp": 785, "atk": 222, "spd": 76, "crit": 18, "desc": "The Wind Style user from the Sand Village."},
    {"name": "Rock Lee (6th Gate)", "rarity": "epic", "faction": "NINJA", "element": "WIND", "hp": 850, "atk": 245, "spd": 88, "crit": 21, "desc": "Lee opening the gates."},
    {"name": "Neji (Byakugan Master)", "rarity": "epic", "faction": "NINJA", "element": "LIGHT", "hp": 820, "atk": 235, "spd": 80, "crit": 19, "desc": "The Hyuga prodigy."},
    {"name": "Temari (Wind Scythe)", "rarity": "epic", "faction": "NINJA", "element": "WIND", "hp": 810, "atk": 230, "spd": 82, "crit": 18, "desc": "Temari's devastating wind attacks."},
    {"name": "Kankuro (Puppet Master)", "rarity": "epic", "faction": "NINJA", "element": "DARK", "hp": 840, "atk": 240, "spd": 76, "crit": 17, "desc": "Kankuro and his puppets."},
    {"name": "Darui (Storm Release)", "rarity": "epic", "faction": "NINJA", "element": "LIGHTNING", "hp": 830, "atk": 238, "spd": 78, "crit": 18, "desc": "Darui's laser circus."},
    {"name": "Karin Uzumaki", "rarity": "epic", "faction": "NINJA", "element": "LIGHT", "hp": 760, "atk": 205, "spd": 84, "crit": 16, "desc": "The Uzumaki healer."},
    {"name": "Suigetsu Hozuki", "rarity": "epic", "faction": "NINJA", "element": "WATER", "hp": 810, "atk": 235, "spd": 79, "crit": 18, "desc": "The water transformation ninja."},
    {"name": "Jugo", "rarity": "epic", "faction": "NINJA", "element": "EARTH", "hp": 860, "atk": 242, "spd": 74, "crit": 19, "desc": "The origin of the curse mark."},
    {"name": "Killer Bee", "rarity": "epic", "faction": "NINJA", "element": "LIGHTNING", "hp": 870, "atk": 248, "spd": 80, "crit": 20, "desc": "The Eight-Tails Jinchuriki."},
    {"name": "Mei Terumi", "rarity": "epic", "faction": "NINJA", "element": "FIRE", "hp": 820, "atk": 232, "spd": 76, "crit": 18, "desc": "The Mizukage with Boil Release."},

    # --- Bleach (10) ---
    {"name": "Shuhei Hisagi", "rarity": "epic", "faction": "SOUL_REAPER", "element": "DARK", "hp": 795, "atk": 225, "spd": 75, "crit": 18, "desc": "The Lieutenant of Squad 9, using Kazeshini."},
    {"name": "Izuru Kira", "rarity": "epic", "faction": "SOUL_REAPER", "element": "DARK", "hp": 780, "atk": 220, "spd": 74, "crit": 17, "desc": "The Lieutenant of Squad 3, using Wabisuke."},
    {"name": "Momo Hinamori", "rarity": "epic", "faction": "SOUL_REAPER", "element": "FIRE", "hp": 770, "atk": 215, "spd": 78, "crit": 18, "desc": "The Lieutenant of Squad 5, using Tobiume."},
    {"name": "Yumichika Ayasegawa", "rarity": "epic", "faction": "SOUL_REAPER", "element": "WIND", "hp": 785, "atk": 222, "spd": 76, "crit": 18, "desc": "The 5th seat of Squad 11, using Fuji Kujaku."},
    {"name": "Ikkaku Madarame", "rarity": "epic", "faction": "SOUL_REAPER", "element": "LIGHTNING", "hp": 810, "atk": 230, "spd": 72, "crit": 17, "desc": "The 3rd seat of Squad 11, using Ryumon Hozukimaru."},
    {"name": "Chad (Fullbring)", "rarity": "epic", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 900, "atk": 250, "spd": 70, "crit": 18, "desc": "Chad's Brazo Derecha de Gigante."},
    {"name": "Orihime (Shun Shun Rikka)", "rarity": "epic", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 860, "atk": 220, "spd": 76, "crit": 16, "desc": "Orihime's reality rejection."},
    {"name": "Urahara (Shikai)", "rarity": "epic", "faction": "SOUL_REAPER", "element": "WIND", "hp": 840, "atk": 240, "spd": 80, "crit": 19, "desc": "Urahara's Benihime."},
    {"name": "Yoruichi (Thunder God)", "rarity": "epic", "faction": "SOUL_REAPER", "element": "LIGHTNING", "hp": 820, "atk": 242, "spd": 88, "crit": 20, "desc": "Yoruichi's Shunko."},
    {"name": "Nel (Adult Form)", "rarity": "epic", "faction": "DARK", "element": "WATER", "hp": 850, "atk": 238, "spd": 82, "crit": 18, "desc": "Nel's true Arrancar form."},

    # --- One Piece (10) ---
    {"name": "Tony Tony Chopper", "rarity": "epic", "faction": "PIRATE", "element": "EARTH", "hp": 775, "atk": 218, "spd": 78, "crit": 18, "desc": "The Straw Hat doctor, using Monster Point."},
    {"name": "Usopp", "rarity": "epic", "faction": "PIRATE", "element": "WIND", "hp": 760, "atk": 210, "spd": 80, "crit": 19, "desc": "The sniper of the Straw Hats, using Observation Haki."},
    {"name": "Nefertari Vivi", "rarity": "epic", "faction": "MARINE", "element": "WIND", "hp": 765, "atk": 212, "spd": 77, "crit": 18, "desc": "The princess of Alabasta."},
    {"name": "Carrot", "rarity": "epic", "faction": "PIRATE", "element": "LIGHTNING", "hp": 780, "atk": 220, "spd": 82, "crit": 19, "desc": "The Mink warrior, using Sulong form."},
    {"name": "Yamato", "rarity": "epic", "faction": "PIRATE", "element": "WATER", "hp": 840, "atk": 238, "spd": 75, "crit": 18, "desc": "The self-proclaimed Kozuki Oden, using the Okuchi no Makami."},
    {"name": "Franky (General Cannon)", "rarity": "epic", "faction": "PIRATE", "element": "FIRE", "hp": 920, "atk": 245, "spd": 72, "crit": 17, "desc": "Franky's ultimate weapon."},
    {"name": "Brook (Soul Solid)", "rarity": "epic", "faction": "PIRATE", "element": "WATER", "hp": 830, "atk": 230, "spd": 86, "crit": 19, "desc": "Brook's freezing sword."},
    {"name": "Robin (Demonio)", "rarity": "epic", "faction": "PIRATE", "element": "DARK", "hp": 850, "atk": 235, "spd": 78, "crit": 18, "desc": "Robin's demonic form."},
    {"name": "Chopper (Monster Point)", "rarity": "epic", "faction": "PIRATE", "element": "EARTH", "hp": 940, "atk": 255, "spd": 68, "crit": 16, "desc": "Chopper's monstrous form."},
    {"name": "Jinbe (Ocean Current)", "rarity": "epic", "faction": "PIRATE", "element": "WATER", "hp": 880, "atk": 240, "spd": 76, "crit": 18, "desc": "Jinbe's Fishman Karate."},
])

# =============================================================
# RARE (30 Characters)
# Reliable fighters, capable of defeating small armies. Drop rate: 25%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (12) ---
    {"name": "Trunks (youth)", "rarity": "rare", "faction": "SAIYAN", "element": "LIGHT", "hp": 590, "atk": 67, "spd": 60, "crit": 12, "desc": "The young Trunks from the main timeline."},
    {"name": "Krillin", "rarity": "rare", "faction": "Z_FIGHTER", "element": "WIND", "hp": 580, "atk": 65, "spd": 62, "crit": 12, "desc": "Goku's best friend, using the Destructo Disk."},
    {"name": "Yamcha", "rarity": "rare", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 570, "atk": 63, "spd": 65, "crit": 11, "desc": "The desert bandit, using the Wolf Fang Fist."},
    {"name": "Chiaotzu", "rarity": "rare", "faction": "Z_FIGHTER", "element": "LIGHT", "hp": 550, "atk": 60, "spd": 68, "crit": 10, "desc": "The small psychic warrior."},
    {"name": "Pan", "rarity": "rare", "faction": "SAIYAN", "element": "LIGHT", "hp": 560, "atk": 62, "spd": 66, "crit": 11, "desc": "Gohan's daughter, possessing immense potential."},
    {"name": "Videl", "rarity": "rare", "faction": "Z_FIGHTER", "element": "WIND", "hp": 570, "atk": 63, "spd": 64, "crit": 11, "desc": "The daughter of Mr. Satan, trained in martial arts."},
    {"name": "Recoome", "rarity": "rare", "faction": "PIRATE", "element": "EARTH", "hp": 610, "atk": 70, "spd": 55, "crit": 11, "desc": "The powerhouse of the Ginyu Force."},
    {"name": "Burter", "rarity": "rare", "faction": "PIRATE", "element": "WIND", "hp": 590, "atk": 67, "spd": 72, "crit": 12, "desc": "The fastest member of the Ginyu Force."},
    {"name": "Jeice", "rarity": "rare", "faction": "PIRATE", "element": "FIRE", "hp": 580, "atk": 65, "spd": 70, "crit": 12, "desc": "The red magent of the Ginyu Force."},
    {"name": "Goten", "rarity": "rare", "faction": "SAIYAN", "element": "LIGHT", "hp": 575, "atk": 64, "spd": 65, "crit": 11, "desc": "Goku's youngest son."},
    {"name": "Kid Trunks", "rarity": "rare", "faction": "SAIYAN", "element": "LIGHT", "hp": 575, "atk": 64, "spd": 66, "crit": 11, "desc": "Vegeta's son."},
    {"name": "Mr. Satan", "rarity": "rare", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 550, "atk": 60, "spd": 55, "crit": 8, "desc": "The World Champion, though he can't use Ki."},
    
    # --- Naruto (6) ---
    {"name": "Iruka Umino", "rarity": "rare", "faction": "NINJA", "element": "EARTH", "hp": 520, "atk": 55, "spd": 58, "crit": 9, "desc": "The Academy teacher who believed in Naruto."},
    {"name": "Konohamaru", "rarity": "rare", "faction": "NINJA", "element": "FIRE", "hp": 510, "atk": 52, "spd": 60, "crit": 10, "desc": "The Third Hokage's grandson, using the Rasengan."},
    {"name": "Anko Mitarashi", "rarity": "rare", "faction": "NINJA", "element": "DARK", "hp": 540, "atk": 58, "spd": 62, "crit": 10, "desc": "Orochimaru's former student, master of snakes."},
    {"name": "Kurenai Yuhi", "rarity": "rare", "faction": "NINJA", "element": "DARK", "hp": 515, "atk": 54, "spd": 64, "crit": 10, "desc": "The genjutsu specialist of the Leaf."},
    {"name": "Shino Aburame", "rarity": "rare", "faction": "NINJA", "element": "EARTH", "hp": 530, "atk": 56, "spd": 59, "crit": 9, "desc": "The bug user of the Aburame clan."},
    {"name": "Tenten", "rarity": "rare", "faction": "NINJA", "element": "WIND", "hp": 525, "atk": 57, "spd": 61, "crit": 10, "desc": "The weapons specialist."},

    # --- Bleach (6) ---
    {"name": "Hanataro Yamada", "rarity": "rare", "faction": "SOUL_REAPER", "element": "WATER", "hp": 500, "atk": 48, "spd": 55, "crit": 8, "desc": "The timid healer of Squad 4."},
    {"name": "Ganju Shiba", "rarity": "rare", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 550, "atk": 60, "spd": 54, "crit": 9, "desc": "The street fighter from the Soul Society."},
    {"name": "Tatsuki Arisawa", "rarity": "rare", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 525, "atk": 56, "spd": 61, "crit": 10, "desc": "Ichigo's childhood friend and karate champion."},
    {"name": "Keigo Asano", "rarity": "rare", "faction": "Z_FIGHTER", "element": "WIND", "hp": 490, "atk": 45, "spd": 62, "crit": 8, "desc": "Ichigo's loud classmate."},
    {"name": "Mizuiro Kojima", "rarity": "rare", "faction": "Z_FIGHTER", "element": "WATER", "hp": 495, "atk": 46, "spd": 60, "crit": 8, "desc": "Ichigo's calm classmate."},
    {"name": "Rukia (Shikai)", "rarity": "rare", "faction": "SOUL_REAPER", "element": "WATER", "hp": 540, "atk": 58, "spd": 60, "crit": 10, "desc": "Rukia using Sode no Shirayuki."},

    # --- One Piece (6) ---
    {"name": "Coby", "rarity": "rare", "faction": "MARINE", "element": "LIGHT", "hp": 505, "atk": 50, "spd": 58, "crit": 9, "desc": "The Marine captain trained by Garp."},
    {"name": "Helmeppo", "rarity": "rare", "faction": "MARINE", "element": "WIND", "hp": 515, "atk": 54, "spd": 56, "crit": 9, "desc": "Coby's friend and rival in the Marines."},
    {"name": "Buggy", "rarity": "rare", "faction": "PIRATE", "element": "LIGHT", "hp": 530, "atk": 56, "spd": 57, "crit": 10, "desc": "The Star Clown, a former Roger Pirate."},
    {"name": "Alvida", "rarity": "rare", "faction": "PIRATE", "element": "EARTH", "hp": 520, "atk": 55, "spd": 55, "crit": 9, "desc": "The Iron Club user, formerly known as 'Lady Alvida'."},
    {"name": "Smoker", "rarity": "rare", "faction": "MARINE", "element": "WIND", "hp": 560, "atk": 62, "spd": 60, "crit": 10, "desc": "The White Hunter, a Vice Admiral in the Marines."},
    {"name": "Tashigi", "rarity": "rare", "faction": "MARINE", "element": "WATER", "hp": 535, "atk": 57, "spd": 59, "crit": 9, "desc": "The swordswoman of the Marines."},
])

# =============================================================
# COMMON (20 Characters)
# Basic units, food for EXP and drops. Drop rate: 30%
# =============================================================
CHARACTERS.extend([
    # --- Dragon Ball (8) ---
    {"name": "Saibaman", "rarity": "common", "faction": "SAIYAN", "element": "EARTH", "hp": 380, "atk": 42, "spd": 45, "crit": 6, "desc": "The disposable bio-warriors of the Saiyans."},
    {"name": "Frieza Soldier", "rarity": "common", "faction": "PIRATE", "element": "DARK", "hp": 370, "atk": 40, "spd": 45, "crit": 5, "desc": "The standard grunts of the Frieza Force."},
    {"name": "Red Ribbon Soldier", "rarity": "common", "faction": "DARK", "element": "EARTH", "hp": 360, "atk": 38, "spd": 44, "crit": 5, "desc": "The foot soldiers of the Red Ribbon Army."},
    {"name": "Cell Junior", "rarity": "common", "faction": "DARK", "element": "LIGHT", "hp": 390, "atk": 44, "spd": 48, "crit": 6, "desc": "The miniature spawn of Perfect Cell."},
    {"name": "World Tournament Rookie", "rarity": "common", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 350, "atk": 36, "spd": 42, "crit": 4, "desc": "An amateur martial artist."},
    {"name": "Saiyan Recruit", "rarity": "common", "faction": "SAIYAN", "element": "EARTH", "hp": 380, "atk": 42, "spd": 46, "crit": 5, "desc": "A low-class Saiyan infant sent to conquer a planet."},
    {"name": "Galactic Patrol Cadet", "rarity": "common", "faction": "MARINE", "element": "LIGHT", "hp": 370, "atk": 40, "spd": 45, "crit": 5, "desc": "A rookie member of the Galactic Patrol."},
    {"name": "Capsule Corp Guard", "rarity": "common", "faction": "Z_FIGHTER", "element": "EARTH", "hp": 360, "atk": 38, "spd": 43, "crit": 4, "desc": "A security guard for Bulma's company."},
    
    # --- Naruto (4) ---
    {"name": "Academy Student", "rarity": "common", "faction": "NINJA", "element": "WIND", "hp": 340, "atk": 35, "spd": 50, "crit": 5, "desc": "A young ninja still learning the basics."},
    {"name": "Anbu Black Ops", "rarity": "common", "faction": "NINJA", "element": "DARK", "hp": 370, "atk": 40, "spd": 52, "crit": 6, "desc": "The masked elite ninja of the Hokage."},
    {"name": "Chunin Exam Finalist", "rarity": "common", "faction": "NINJA", "element": "FIRE", "hp": 380, "atk": 42, "spd": 48, "crit": 5, "desc": "A skilled genin participating in the exams."},
    {"name": "Sand Ninja", "rarity": "common", "faction": "NINJA", "element": "EARTH", "hp": 360, "atk": 38, "spd": 46, "crit": 5, "desc": "A ninja from the Hidden Sand Village."},
    
    # --- Bleach (4) ---
    {"name": "Soul Reaper", "rarity": "common", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 365, "atk": 39, "spd": 46, "crit": 5, "desc": "A standard Shinigami tasked with purifying Hollows."},
    {"name": "Hollow", "rarity": "common", "faction": "DARK", "element": "DARK", "hp": 400, "atk": 45, "spd": 42, "crit": 6, "desc": "A fallen soul consumed by despair."},
    {"name": "Quincy", "rarity": "common", "faction": "SOUL_REAPER", "element": "LIGHT", "hp": 350, "atk": 37, "spd": 49, "crit": 5, "desc": "A human with the power to destroy Hollows using bows."},
    {"name": "Arrancar", "rarity": "common", "faction": "DARK", "element": "DARK", "hp": 385, "atk": 43, "spd": 45, "crit": 6, "desc": "A Hollow that has torn off its mask to gain Shinigami powers."},
    
    # --- One Piece (4) ---
    {"name": "Marine Recruit", "rarity": "common", "faction": "MARINE", "element": "LIGHT", "hp": 355, "atk": 38, "spd": 44, "crit": 5, "desc": "A fresh face in the Marines."},
    {"name": "Pirate Grunt", "rarity": "common", "faction": "PIRATE", "element": "EARTH", "hp": 375, "atk": 41, "spd": 45, "crit": 5, "desc": "A low-level crewmate on a pirate ship."},
    {"name": "Bandit", "rarity": "common", "faction": "DARK", "element": "EARTH", "hp": 345, "atk": 36, "spd": 47, "crit": 4, "desc": "A common mountain bandit."},
    {"name": "Revolutionary Soldier", "rarity": "common", "faction": "PIRATE", "element": "WIND", "hp": 380, "atk": 42, "spd": 46, "crit": 6, "desc": "A fighter in the Revolutionary Army."},
])


# -------------------------------------------------------------
# 6. RARITY CONFIGURATIONS
# -------------------------------------------------------------
# These dictionaries dictate how characters of each rarity are
# processed, displayed, and statted (if not explicitly defined).

RARITY_ORDER = {
    "common": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
    "mythical": 5,
    "sp_plus": 6,
    "omni": 7,
}

RARITY_LABEL = {
    "common": "⚪ Common",
    "rare": "🔵 Rare",
    "epic": "🟣 Epic",
    "legendary": "🟡 Legendary",
    "mythical": "🔴 Mythical",
    "sp_plus": "💠 SP+",
    "omni": "👑 Omni King",
}

RARITY_ICONS = {
    "common": "⚪", "rare": "🔵", "epic": "🟣",
    "legendary": "🟡", "mythical": "🔴", "sp_plus": "💠", "omni": "👑",
}

RARITY_COLORS = {
    "common": "#A9A9A9",     # Gray
    "rare": "#1E90FF",       # Dodger Blue
    "epic": "#8A2BE2",       # Blue Violet
    "legendary": "#FFD700",  # Gold
    "mythical": "#FF4500",   # Orange Red
    "sp_plus": "#00FFFF",    # Cyan
    "omni": "#FF1493",       # Deep Pink
}

# Fallback Stats
RARITY_ATK  = {"common": 40,  "rare": 65,  "epic": 240, "legendary": 330, "mythical": 410, "sp_plus": 490, "omni": 560}
RARITY_HP   = {"common": 370, "rare": 580, "epic": 850, "legendary": 950, "mythical": 1300, "sp_plus": 1650, "omni": 1950}
RARITY_SPD  = {"common": 44,  "rare": 62,  "epic": 76,  "legendary": 84,  "mythical": 90,  "sp_plus": 96,  "omni": 100}
RARITY_CRIT = {"common": 5,   "rare": 11,  "epic": 19,  "legendary": 24,  "mythical": 30,  "sp_plus": 35,  "omni": 40}

RARITY_LEVEL_CAP = {
    "common": 30, "rare": 50, "epic": 70, "legendary": 90,
    "mythical": 110, "sp_plus": 130, "omni": 150,
}


# -------------------------------------------------------------
# 7. GACHA SYSTEM & PITY RATES
# -------------------------------------------------------------
GACHA_RATES = [
    ("common",    30),
    ("rare",      25),
    ("epic",      20),
    ("legendary", 14),
    ("mythical",  7),
    ("sp_plus",   3),
    ("omni",      1),
]

GACHA_PITY = {
    "soft_pity": 50,       # At 50 pulls without Legendary+
    "hard_pity": 90,       # At 90 pulls, guaranteed Mythical+
    "sp_plus_pity": 150,   # At 150 pulls, guaranteed SP+
    "omni_pity": 300,      # At 300 pulls, guaranteed Omni King
}

GACHA_BANNERS = {
    "standard": {"name": "Standard Banner", "cost": 1, "bonus": {}, "description": "Standard rates for all characters."},
    "hero": {"name": "Hero Banner", "cost": 1, "bonus": {"legendary": 1.5, "mythical": 1.5}, "description": "Boosted Legendary and Mythical rates."},
    "god": {"name": "God Banner", "cost": 2, "bonus": {"mythical": 2.0, "sp_plus": 1.5}, "description": "Boosted Mythical & SP+ rates."},
    "omni": {"name": "Omniverse Banner", "cost": 3, "bonus": {"sp_plus": 2.0, "omni": 3.0}, "description": "Massive boost to SP+ and Omni rates."},
    "anime": {"name": "Anime Crossover Banner", "cost": 2, "bonus": {"mythical": 1.5, "sp_plus": 1.5, "omni": 2.0}, "description": "Naruto, Bleach, and One Piece characters heavily boosted."},
}

GACHA_BANNER_DESCRIPTIONS = {
    "standard": "Normal rates for all rarities.",
    "hero": "Boosted Legendary & Mythical rates.",
    "god": "Boosted Mythical & SP+ rates (costs 2 tickets).",
    "omni": "3× Omni rate, 2x SP+ rate (costs 3 tickets).",
    "anime": "Anime Crossover rates (costs 2 tickets).",
}


# -------------------------------------------------------------
# 8. EQUIPMENT (WEAPONS & ARMORS)
# -------------------------------------------------------------
WEAPONS = {
    # DBZ
    "Wooden Sword": 20, "Power Pole": 55, "Saiyan Blade": 140, "Kamehameha Blade": 260,
    "Z Sword": 520, "Destructo Blade": 720, "Deadly Divine Sword": 1950, "Vegito Spirit Sword": 2200,
    "Black Kamehameha Blade": 2300, "Hakai Orb": 2500, "Time Ring": 2600, "Power Impact Scroll": 2700,
    # Naruto
    "Kunai": 80, "Asuma's Chakra Blades": 450, "Sasuke's Kusanagi": 950, "Madara's Gunbai": 1600,
    "Truth-Seeking Orb Staff": 2100, "Kakashi's White Fang": 2400, "Indra's Arrow": 2800,
    "Seven Swords of the Mist": 3100, "Totsuka Blade": 3400,
    # Bleach
    "Zanpakuto (Shikai)": 120, "Zangetsu": 580, "Hyorinmaru": 980, "Ryujin Jakka": 1750,
    "Ichimonji": 2150, "Quincy Cross": 2800, "Almighty Eye": 3000, "Zanka no Tachi": 3600,
    "Benihime (Bankai)": 3900, "True Tensa Zangetsu": 4500,
    # One Piece
    "Cutlass": 60, "Yubashiri": 380, "Sandai Kitetsu": 850, "Enma": 1500,
    "Gryphon (Shanks Sword)": 2050, "Kanabo Club": 3100, "Ame no Habakiri": 3500,
    "Murakumogiri (Whitebeard)": 4000, "Nika's Fist": 5000,
}

ARMORS = {
    # DBZ
    "Turtle School Gi": 40, "Saiyan Armor": 160, "God Armor": 360, "Whis Symbol Gi": 720,
    "Grand Priest Suit": 1650, "Heavenly Guardian Suit": 2700, "Pride Trooper Armor": 2800, "Divine Robes": 2900,
    # Naruto
    "Shihakusho": 50, "Chunin Flak Jacket": 110, "Anbu Armor": 480, "Sage Mode Cloak": 900,
    "Six Paths Robe": 1600, "Baryon Mode Aura": 2400, "Kage Battle Armor": 3200, "Susanoo Ribcage": 3800,
    # Bleach
    "Captain Haori": 520, "Arrancar Uniform": 950, "Quincy Vollstandig": 1700, "Soul King's Weave": 2500,
    "Vasto Lorde Armor": 3300, "Bankai Coat": 4200,
    # One Piece
    "Marine Coat": 90, "Raid Suit": 920, "Beast Pirate Coat": 1550, "Joyboy's Armament": 2600,
    "Uo Uo no Mi": 3000, "Sea Stone Armor": 3400, "Emperor's Cloak": 4600,
}

EQUIPMENT = {}
for _w, _b in WEAPONS.items(): EQUIPMENT[_w] = ("weapon", _b)
for _a, _b in ARMORS.items(): EQUIPMENT[_a] = ("armor", _b)


# -------------------------------------------------------------
# 9. CRAFTING & SKILLS
# -------------------------------------------------------------
CRAFTING_RECIPES = {
    # Weapon Crafting
    "Saiyan Blade": {"materials": {"Iron Sword": 2, "Fusion Core": 1}, "cost_yens": 5000},
    "Destructo Blade": {"materials": {"Saiyan Blade": 1, "Fusion Crystal": 2}, "cost_yens": 25000},
    "Vegito Spirit Sword": {"materials": {"Destructo Blade": 1, "Fusion Catalyst": 3}, "cost_yens": 100000},
    "True Tensa Zangetsu": {"materials": {"Zangetsu": 1, "Fusion Catalyst": 5, "Hollow Mask": 1}, "cost_yens": 500000},
    "Nika's Fist": {"materials": {"Joyboy's Armament": 1, "Fusion Catalyst": 10}, "cost_yens": 1000000},
    # Armor Crafting
    "God Armor": {"materials": {"Saiyan Armor": 2, "Fusion Core": 2}, "cost_yens": 15000},
    "Grand Priest Suit": {"materials": {"God Armor": 1, "Fusion Crystal": 4}, "cost_yens": 80000},
    "Baryon Mode Aura": {"materials": {"Sage Mode Cloak": 1, "Fusion Catalyst": 5}, "cost_yens": 300000},
}

SKILLS = {
    # DBZ
    "Ki Blast": 9, "Kaioken": 6, "Instant Transmission": 10, "Solar Flare": 12,
    "Destructo Disk": 16, "Spirit Bomb": 18, "Final Flash": 20, "Ultra Instinct": 22,
    "God Kamehameha": 25, "Big Bang Attack": 28, "Black Hole Attack": 32, "Final Explosion": 35,
    "Kamehameha Wave": 38, "Heavenly Rush": 42, "Universe Breaker": 48, "Halo Blast": 50,
    "Godly Burst": 54, "Zenkai Boost": 60, "Hakai (Destruction)": 75, "Soul Punisher": 80,
    # Naruto
    "Substitution Jutsu": 8, "Shadow Clone Jutsu": 14, "Rasengan": 15, "Chidori": 16,
    "Sage Mode": 22, "Amaterasu": 28, "Susanoo": 40, "Truth-Seeking Orb": 50,
    "Baryon Mode": 60, "Rasenshuriken": 45, "Chibaku Tensei (Planetary Devastation)": 55,
    "Kirin": 48, "Kotoamatsukami": 65, "Edo Tensei": 70, "Infinite Tsukuyomi": 85,
    # Bleach
    "Flash Step": 10, "Getsuga Tensho": 18, "Cero Oscuras": 26, "Bankai": 35,
    "Mugetsu": 55, "Almighty": 65, "Hado 99: Goryutenmetsu": 58, "Kurohitsugi (Black Coffin)": 52,
    "Rikujokoro": 30, "Zanka no Tachi (North)": 72, "Kyoka Suigetsu (Complete Hypnosis)": 80,
    # One Piece
    "Gum-Gum Pistol": 10, "Diable Jambe": 20, "Three-Sword Style": 22, "Conqueror's Haki": 45,
    "Gear 5": 60, "Bajrang Gun": 75, "King Kong Gun": 65, "Asura (Nine Sword Style)": 58,
    "Ifrit Jambe": 55, "R-room (Awakening)": 62, "Divine Departure": 70,
}

SKILL_ATK = {
    "Ki Blast": 100, "Kaioken": 116, "Instant Transmission": 114, "Solar Flare": 171,
    "Destructo Disk": 190, "Spirit Bomb": 192, "Final Flash": 128, "Ultra Instinct": 215,
    "God Kamehameha": 222, "Big Bang Attack": 214, "Black Hole Attack": 224, "Final Explosion": 292,
    "Kamehameha Wave": 225, "Heavenly Rush": 390, "Universe Breaker": 344, "Halo Blast": 368,
    "Godly Burst": 465, "Zenkai Boost": 550, "Hakai (Destruction)": 800, "Soul Punisher": 900,
    "Substitution Jutsu": 80, "Shadow Clone Jutsu": 150, "Rasengan": 160, "Chidori": 170,
    "Sage Mode": 240, "Amaterasu": 250, "Susanoo": 380, "Truth-Seeking Orb": 450,
    "Baryon Mode": 600, "Rasenshuriken": 420, "Chibaku Tensei (Planetary Devastation)": 520,
    "Kirin": 400, "Kotoamatsukami": 700, "Edo Tensei": 750, "Infinite Tsukuyomi": 950,
    "Flash Step": 95, "Getsuga Tensho": 180, "Cero Oscuras": 240, "Bankai": 350,
    "Mugetsu": 520, "Almighty": 650, "Hado 99: Goryutenmetsu": 580, "Kurohitsugi (Black Coffin)": 500,
    "Rikujokoro": 220, "Zanka no Tachi (North)": 820, "Kyoka Suigetsu (Complete Hypnosis)": 880,
    "Gum-Gum Pistol": 110, "Diable Jambe": 190, "Three-Sword Style": 210, "Conqueror's Haki": 400,
    "Gear 5": 580, "Bajrang Gun": 850, "King Kong Gun": 620, "Asura (Nine Sword Style)": 560,
    "Ifrit Jambe": 530, "R-room (Awakening)": 600, "Divine Departure": 780,
}

SKILL_DESCRIPTIONS = {
    "Hakai (Destruction)": "Erases the target from existence. Cannot be blocked.",
    "Soul Punisher": "A massive green energy blast that destroys the soul.",
    "Rasenshuriken": "A giant spinning shuriken of wind chakra.",
    "Chibaku Tensei (Planetary Devastation)": "Creates a massive black orb that pulls the earth into a meteor.",
    "Kirin": "Uses natural lightning to strike the target in 1/1000th of a second.",
    "Kotoamatsukami": "The ultimate genjutsu. Manipulates the target without them knowing.",
    "Infinite Tsukuyomi": "Traps the entire world in an eternal, perfect dream.",
    "Hado 99: Goryutenmetsu": "Summons massive dragons made of spiritual energy.",
    "Kurohitsugi (Black Coffin)": "Traps the target in a black box where gravity crushes them.",
    "Zanka no Tachi (North)": "A sword strike that erases everything it touches from existence.",
    "Kyoka Suigetsu (Complete Hypnosis)": "Complete control of the five senses. Reality becomes an illusion.",
    "Bajrang Gun": "A massive fist the size of an island, imbued with Conqueror's Haki.",
    "Asura (Nine Sword Style)": "Manifests 3 heads and 6 arms to use 9 swords at once.",
    "Divine Departure": "A powerful Haki-infused sword slash that can split the sky.",
}


# -------------------------------------------------------------
# 10. SHOP, TITLES & DAILY POOL
# -------------------------------------------------------------
SHOP = {}
_shop_id = 1
def _register(name, price, currency, kind, amount=1):
    global _shop_id
    SHOP[_shop_id] = (name, price, currency, kind, amount)
    _shop_id += 1

for _wname, _wval in WEAPONS.items(): _register(_wname, _wval * 800, "yens", "weapon")
for _aname, _aval in ARMORS.items(): _register(_aname, _aval * 900, "yens", "armor")

_register("Crystal x1",   30,   "gems", "crystal", 1)
_register("Crystal x10",  280,  "gems", "crystal", 10)
_register("Crystal x50",  1300, "gems", "crystal", 50)
_register("Crystal x100", 2400, "gems", "crystal", 100)
_register("Potion",             100,  "yens", "heal", 1)
_register("Mega Potion",        250,  "yens", "heal", 1)
_register("Revive",             350,  "yens", "heal", 1)
_register("Senzu Bean",         800,  "yens", "heal", 1)
_register("Senzu Bean Pouch x5", 3800, "yens", "heal", 5)
_register("Divine Senzu Bean",  8000, "yens", "heal", 1)
_register("Fusion Material",  250,  "gems", "fusion", 1)
_register("Fusion Core",      500,  "gems", "fusion", 1)
_register("Fusion Crystal",   1200, "gems", "fusion", 1)
_register("Fusion Catalyst",  2500, "gems", "fusion", 1)
_register("Potara Earrings",  4000, "gems", "fusion", 1)
_register("Gacha Ticket",      60,   "gems", "ticket", 1)
_register("Gacha Ticket x10",  560,  "gems", "ticket", 10)
_register("Gacha Ticket x50",  2700, "gems", "ticket", 50)
_register("Gacha Ticket x100", 5200, "gems", "ticket", 100)
_register("Elite Key",         1200, "yens", "key_elite", 1)
_register("Boss Key",          2600, "yens", "key_boss", 1)

SHOP_CATEGORY_ORDER = [
    ("weapon", "⚔️ Weapons"), ("armor", "🛡️ Armors"),
    ("crystal", "🔮 Crystals"), ("heal", "🧪 Healing"),
    ("fusion", "🧬 Fusion Materials"), ("ticket", "🎫 Tickets & Keys"),
]
BULK_DISCOUNTS = [(50, 0.15), (10, 0.10), (5, 0.05)]

TITLES = {
    "rookie": {"name": "🌱 Rookie", "desc": "Reach Level 10", "req": "level_10", "bonus": "+2% ATK"},
    "veteran": {"name": "⚔️ Veteran", "desc": "Reach Level 50", "req": "level_50", "bonus": "+5% ATK"},
    "master": {"name": "🥋 Master", "desc": "Reach Level 100", "req": "level_100", "bonus": "+10% ATK"},
    "hokage": {"name": "🔥 Hokage", "desc": "Win 100 battles", "req": "wins_100", "bonus": "+8% HP"},
    "soul_reaper": {"name": "💀 Soul Reaper", "desc": "Reach Rank 5", "req": "rank_5", "bonus": "+8% CRIT"},
    "pirate_king": {"name": "☠️ Pirate King", "desc": "Travel to Anime Multiverse", "req": "travel_anime", "bonus": "+12% ATK"},
    "god_of_destruction": {"name": "🔱 God of Destruction", "desc": "Reach Rank 10", "req": "rank_10", "bonus": "+20% All Stats"},
    "collector": {"name": "📚 Collector", "desc": "Own 50 Characters", "req": "chars_50", "bonus": "+5% Gacha Luck"},
}

DAILY_SHOP_POOL = [
    {"item": "Senzu Bean Pouch x5", "price": 1000, "currency": "yens"},
    {"item": "Fusion Catalyst", "price": 1500, "currency": "gems"},
    {"item": "Potara Earrings", "price": 3000, "currency": "gems"},
    {"item": "Gacha Ticket x10", "price": 400, "currency": "gems"},
    {"item": "Elite Key", "price": 800, "currency": "yens"},
    {"item": "Boss Key", "price": 1800, "currency": "yens"},
    {"item": "Soul Punisher", "price": 5000, "currency": "crystals"},
    {"item": "Hakai Orb", "price": 10000, "currency": "crystals"},
    {"item": "Nika's Fist", "price": 15000, "currency": "crystals"},
    {"item": "True Tensa Zangetsu", "price": 12000, "currency": "crystals"},
    {"item": "Emperor's Cloak", "price": 10000, "currency": "crystals"},
]


# -------------------------------------------------------------
# 11. SUMMONS, CLAN RAIDS & PROGRESSION
# -------------------------------------------------------------
SUMMONS = {
    "elite": {"name": "Elite Ginyu Force", "hp": 260000, "dmg": 11000, "reward_mult": 5, "key": "keys_elite", "drops": ["Fusion Material", "God Armor", "Senzu Bean"]},
    "mythical": {"name": "Mythical Perfect Cell", "hp": 700000, "dmg": 18000, "reward_mult": 5, "key": "keys_boss", "drops": ["Fusion Core", "Whis Symbol Gi", "Divine Senzu Bean"]},
    "legendary": {"name": "God of Destruction Beerus", "hp": 1100000, "dmg": 26000, "reward_mult": 5, "key": "keys_boss", "drops": ["Fusion Crystal", "Grand Priest Suit", "Omni Focus"]},
    "anime": {"name": "Anime Multiverse Overlord", "hp": 2500000, "dmg": 45000, "reward_mult": 10, "key": "keys_boss", "drops": ["Potara Earrings", "Joyboy's Armament", "Baryon Mode"]},
}

CLAN_RAIDS = {
    "Perfect Cell": {"hp": 40000, "dmg": 399, "reward_yens": 25000000, "reward_gems": 50000, "reward_crystals": 3000, "reward_tickets": 50, "reward_skill_points": 100},
    "Frieza": {"hp": 70000, "dmg": 1200, "reward_yens": 50000000, "reward_gems": 90000, "reward_crystals": 6000, "reward_tickets": 70, "reward_skill_points": 120},
    "Majin Buu": {"hp": 95000, "dmg": 1700, "reward_yens": 80000000, "reward_gems": 120000, "reward_crystals": 8000, "reward_tickets": 100, "reward_skill_points": 150},
    "Beerus": {"hp": 140000, "dmg": 2400, "reward_yens": 120000000, "reward_gems": 180000, "reward_crystals": 10000, "reward_tickets": 150, "reward_skill_points": 190},
    "Soul King": {"hp": 350000, "dmg": 5500, "reward_yens": 500000000, "reward_gems": 500000, "reward_crystals": 25000, "reward_tickets": 300, "reward_skill_points": 500},
}

CLAN_CREATE_CRYSTALS = 100
CLAN_PERKS = {
    "war_drums":     {"name": "War Drums",     "cost": 200,  "desc": "+5% ATK for all members"},
    "iron_wall":     {"name": "Iron Wall",     "cost": 200,  "desc": "+5% HP for all members"},
    "ki_reserves":   {"name": "Ki Reserves",   "cost": 300,  "desc": "+10% skill points on wins"},
    "greedy_vault":  {"name": "Greedy Vault",  "cost": 400,  "desc": "+10% yens on wins"},
    "crit_focus":    {"name": "Crit Focus",    "cost": 500,  "desc": "+3% crit chance"},
    "kai_blessing":  {"name": "Kai Blessing",  "cost": 600,  "desc": "+1 extra daily reward"},
    "raid_lust":     {"name": "Raid Lust",     "cost": 700,  "desc": "+15% raid damage"},
    "senzu_stock":   {"name": "Senzu Stock",   "cost": 800,  "desc": "Free Senzu every 24h"},
    "treasure_lord": {"name": "Treasure Lord", "cost": 900,  "desc": "+20% clan treasure"},
    "mystic_forge":  {"name": "Mystic Forge",  "cost": 1000, "desc": "Fusion drop rate x2"},
    "omni_focus":    {"name": "Omni Focus",    "cost": 1500, "desc": "+1% omni gacha rate"},
    "dragon_aura":   {"name": "Dragon Aura",   "cost": 2000, "desc": "+10% dragon ball drop"},
}

RAID = {"name": "Multiverse Omega Dragon", "hp": 120000, "dmg": 500, "reward_mult": 10, "attack_cooldown_s": 0}
RAID_FLAVOR_TEXT = {"started": "A massive shadow darkens the sky. The Multiverse Omega Dragon has appeared!", "defeated": "The dragon roars and crumbles into particles. The multiverse is safe... for now.", "attacked": "Your Ki-blast streaks through the void and strikes the dragon."}

RANKS = {1: "Beginner", 2: "Novice", 3: "King", 4: "Emperor", 5: "Demigod", 6: "Immortal", 7: "Titan", 8: "Oracle", 9: "Celestial", 10: "God"}
RANKUP_CRYSTALS = {1: 500, 2: 4000, 3: 20000, 4: 70000, 5: 150000, 6: 300000, 7: 600000, 8: 1000000, 9: 2000000}
RANK_BONUS = 0.15

STARTER_PACK = {"pool": ["rare", "epic", "legendary"], "bonus_yens": 1000, "bonus_gems": 50, "bonus_tickets": 3}
FUSION_MATERIALS = {"Fusion Material": 1, "Fusion Core": 2, "Fusion Crystal": 3, "Fusion Catalyst": 4, "Potara Earrings": 5}
FUSION_CRYSTAL_COST = 25
HEALING = {"Potion": 0.30, "Mega Potion": 0.60, "Revive": 0.80, "Senzu Bean": 1.00, "Senzu Bean Pouch x5": 1.00, "Divine Senzu Bean": 1.00}
HEAL_DESCRIPTIONS = {"Potion": "Restores 30% of max HP", "Mega Potion": "Restores 60% of max HP", "Revive": "Restores 80% of max HP", "Senzu Bean": "Fully restores HP (100%)", "Senzu Bean Pouch x5": "Contains 5 Senzu Beans", "Divine Senzu Bean": "Fully restores HP + stamina"}

ACHIEVEMENTS = {
    "first_blood": {"name": "First Blood", "desc": "Win your first battle", "yens": 1000, "gems": 10, "crystals": 0},
    "battle_10": {"name": "Rookie Fighter", "desc": "Complete 10 battles", "yens": 5000, "gems": 25, "crystals": 1},
    "battle_50": {"name": "Veteran", "desc": "Complete 50 battles", "yens": 25000, "gems": 100, "crystals": 3},
    "battle_100": {"name": "100th Battle", "desc": "Complete 100 battles", "yens": 100000, "gems": 400, "crystals": 10},
    "battle_500": {"name": "Warlord", "desc": "Complete 500 battles", "yens": 500000, "gems": 2000, "crystals": 50},
    "flawless": {"name": "Flawless Victory", "desc": "Win without taking damage", "yens": 20000, "gems": 100, "crystals": 5},
    "explore_vet": {"name": "Explorer", "desc": "Defeat 100 NPCs", "yens": 30000, "gems": 150, "crystals": 8},
    "boss_slayer": {"name": "Boss Slayer", "desc": "Defeat a world boss", "yens": 50000, "gems": 300, "crystals": 15},
    "summon_hunter": {"name": "Summon Hunter", "desc": "Defeat a summon boss", "yens": 80000, "gems": 500, "crystals": 20},
    "raid_warrior": {"name": "Raid Warrior", "desc": "Help defeat the world raid", "yens": 100000, "gems": 500, "crystals": 20},
    "clan_raid_clear": {"name": "Clan Champion", "desc": "Clear a clan raid boss", "yens": 200000, "gems": 800, "crystals": 30},
    "clan_founder": {"name": "Clan Founder", "desc": "Create a clan", "yens": 20000, "gems": 100, "crystals": 3},
    "clan_leader": {"name": "Clan Leader", "desc": "Become a clan leader", "yens": 10000, "gems": 50, "crystals": 2},
    "dragon_collector": {"name": "Dragon Collector", "desc": "Collect all 7 dragon balls", "yens": 150000, "gems": 600, "crystals": 30},
    "mythical_owner": {"name": "Mythical Owner", "desc": "Obtain a mythical character", "yens": 50000, "gems": 250, "crystals": 15},
    "omni_owner": {"name": "Omni Owner", "desc": "Obtain an omni character", "yens": 500000, "gems": 2000, "crystals": 100},
    "rich": {"name": "Millionaire", "desc": "Have 1,000,000 yens", "yens": 50000, "gems": 100, "crystals": 5},
    "gem_hoarder": {"name": "Gem Hoarder", "desc": "Have 1,000 gems", "yens": 20000, "gems": 100, "crystals": 3},
    "rank_5": {"name": "Demigod", "desc": "Reach rank 5", "yens": 50000, "gems": 250, "crystals": 15},
    "rank_10": {"name": "God", "desc": "Reach rank 10", "yens": 1000000, "gems": 5000, "crystals": 200},
    "fusion_master": {"name": "Fusion Master", "desc": "Complete a fusion", "yens": 30000, "gems": 150, "crystals": 8},
    "traveler": {"name": "Traveler", "desc": "Travel to Omniverse", "yens": 50000, "gems": 200, "crystals": 10},
    "anime_weeb": {"name": "Multiversal Traveler", "desc": "Travel to Anime Multiverse", "yens": 100000, "gems": 500, "crystals": 25},
}

DAILY_QUESTS = {
    "daily_npc_10": {"name": "Fight 10 NPCs", "target": 10, "yens": 5000, "gems": 25, "crystals": 1},
    "daily_win_5": {"name": "Win 5 battles", "target": 5, "yens": 4000, "gems": 20, "crystals": 1},
    "daily_earn_5000": {"name": "Earn 5,000 yens", "target": 5000, "yens": 3000, "gems": 15, "crystals": 0},
    "daily_gacha_1": {"name": "Roll gacha once", "target": 1, "yens": 2000, "gems": 30, "crystals": 0},
}

WEEKLY_QUESTS = {
    "weekly_npc_100": {"name": "Fight 100 NPCs", "target": 100, "yens": 50000, "gems": 250, "crystals": 10},
    "weekly_boss_3": {"name": "Defeat 3 bosses", "target": 3, "yens": 30000, "gems": 150, "crystals": 5},
    "weekly_earn_50k": {"name": "Earn 50,000 yens", "target": 50000, "yens": 25000, "gems": 100, "crystals": 3},
    "weekly_gacha_10": {"name": "Roll gacha 10 times", "target": 10, "yens": 20000, "gems": 200, "crystals": 5},
}

MONTHLY_QUESTS = {
    "monthly_npc_500": {"name": "Fight 500 NPCs", "target": 500, "yens": 500000, "gems": 2000, "crystals": 50},
    "monthly_win_250": {"name": "Win 250 battles", "target": 250, "yens": 400000, "gems": 1500, "crystals": 40},
    "monthly_earn_500k": {"name": "Earn 500,000 yens", "target": 500000, "yens": 300000, "gems": 1000, "crystals": 30},
    "monthly_summon_5": {"name": "Defeat 5 summons", "target": 5, "yens": 350000, "gems": 1200, "crystals": 35},
}

QUEST_RESET_INFO = {"daily": "Resets at midnight UTC", "weekly": "Resets Monday at 00:00 UTC", "monthly": "Resets on the 1st of each month"}

DROP_RATES = {
    "npc": {"equipment": 0.15, "dragon_ball": 0.10, "ticket": 0.05, "skill": 0.02, "fusion_material": 0.00},
    "boss": {"equipment": 0.35, "dragon_ball": 0.45, "ticket": 0.30, "skill": 0.20, "fusion_material": 0.25},
    "summon": {"equipment": 0.35, "dragon_ball": 0.60, "ticket": 0.30, "skill": 0.40, "fusion_material": 0.25},
}

ELEMENTAL_SYNERGY = {
    "Fire": {"strong": ["Wind", "Ice"], "weak": ["Water", "Earth"]},
    "Water": {"strong": ["Fire", "Earth"], "weak": ["Lightning", "Wind"]},
    "Wind": {"strong": ["Earth", "Lightning"], "weak": ["Fire", "Ice"]},
    "Earth": {"strong": ["Lightning", "Fire"], "weak": ["Water", "Wind"]},
    "Lightning": {"strong": ["Water", "Wind"], "weak": ["Earth"]},
    "Light": {"strong": ["Dark"], "weak": ["Dark"]},
    "Dark": {"strong": ["Light"], "weak": ["Light"]},
}

NEW_COMMANDS = {
    "/pity": "Check your Gacha Pity progress toward guaranteed top-tier characters.",
    "/daily_shop": "View the rotating shop that resets every 24 hours with rare items.",
    "/titles": "View and equip Titles that grant passive stat bonuses.",
    "/craft": "Combine materials and gear to craft ultra-powerful items.",
    "/element": "View the elemental weakness chart and faction synergies.",
}

NEW_SUBCOMMANDS = {
    "shop refresh": "Force refresh the daily shop (costs 10 crystals).",
    "travel lore <planet>": "Read the deep lore and history of a specific planet.",
    "gacha rates": "View the exact drop rates and pity system.",
    "clan perks list": "View all clan perks and their costs in a clean list.",
}

# =============================================================
# END OF MASTER GAME DATA (PART 2)
# =============================================================
