"""
Py4GWCoreLib - Core library for Guild Wars automation.

This module provides the main API for interacting with the Guild Wars client.
"""

import traceback
import math
from enum import Enum
import time
from time import sleep
import inspect
import sys
from dataclasses import dataclass, field

# Native bindings
import Py4GW
import PyScanner
import PyImGui
import PyMap
import PyMissionMap
import PyAgent
import PyPlayer
import PyParty
import PyItem
import PyInventory
import PySkill
import PySkillbar
import PyMerchant
import PyEffects
import PyKeystroke
import PyOverlay
import PyQuest
import PyPathing
import PyUIManager
import PyCamera
import Py2DRenderer

# Enums - explicit imports for commonly used enums
from .enums import (
    # Game data
    Ailment, Allegiance, Attribute, DamageType, DyeColor,
    FactionAllegiance, FactionType, Inscription, Profession,
    ProfessionShort, Range, Reduced_Ailment, SkillType, Weapon,
    WeaporReq, CAP_EXPERIENCE, CAP_STEP, EXPERIENCE_PROGRESSION,
    # Heroes
    HeroType, PetBehavior,
    # IO
    Key, MouseButton, CHAR_MAP,
    # Items
    Bags, IdentifyAllType, ItemType, Rarity, SalvageAllType,
    # Maps
    explorable_name_to_id, explorables, name_to_map_id,
    outpost_name_to_id, outposts, InstanceType, InstanceTypeName,
    # Models
    AgentModelID, ModelID, PetModelID, SPIRIT_BUFF_MAP, SpiritModelID,
    # Multiboxing
    CombatPrepSkillsType, SharedCommandType,
    # Console
    Console,
    # Regions
    Campaign, CampaignName, Continent, ContinentName, District,
    Language, RegionType, RegionTypeName, ServerLanguage,
    ServerLanguageName, ServerRegionName, DistrictName,
)

# Icons
from .ImGui_src.IconsFontAwesome5 import IconsFontAwesome5

# Core modules - explicit imports
from .Map import Map
from .ImGui import ImGui
from .model_data import ModelData
from .Agent import Agent, AgentName, ItemOwnerCache
from .Player import Player
from .AgentArray import AgentArray, RawAgentArray
from .Party import Party
from .Item import Item, Bag
from .ItemArray import ItemArray
from .Inventory import Inventory
from .Skill import Skill
from .Skillbar import SkillBar
from .Effect import Effects
from .Merchant import Trading
from .Quest import Quest
from .Camera import Camera
from .Scanner import Scanner

# Core utilities
from .Py4GWcorelib import (
    ConsoleLog, ThrottledTimer, Timer, ActionQueueManager,
)
from .Overlay import Overlay, OverlayUtils
from .DXOverlay import DXOverlay
from .UIManager import UIManager, FrameInfo, WindowFrames
from .Routines import Routines
from .SkillManager import SkillManager
from .GlobalCache import GLOBAL_CACHE
from .Pathing import AutoPathing
from .BuildMgr import BuildMgr
from .Botting import BottingClass as Botting
from .Context import GWContext

# New utilities
from .exceptions import (
    Py4GWError, AgentError, InvalidAgentError, PartyError,
    InventoryError, ItemError, SkillError, MapError, UIError,
    CacheError, ConfigError, ThreadingError, ValidationError,
)

traceback = traceback
math = math
Enum = Enum
time = time
sleep = sleep
inspect = inspect
dataclass = dataclass
field = field

Py4Gw = Py4GW
Py4GW = Py4GW
PyScanner = PyScanner
PyImGui = PyImGui
PyMap = PyMap
PyMissionMap = PyMissionMap
PyAgent = PyAgent
PyPlayer = PyPlayer
PyParty = PyParty
PyItem = PyItem
PyInventory = PyInventory
PySkill = PySkill
PySkillbar = PySkillbar
PyMerchant = PyMerchant
PyEffects = PyEffects
PyPathing = PyPathing
PyOverlay = PyOverlay
PyQuest = PyQuest
PyUIManager = PyUIManager
PyCamera = PyCamera
Py2DRenderer = Py2DRenderer
GLOBAL_CACHE = GLOBAL_CACHE
AutoPathing = AutoPathing
IconsFontAwesome5 = IconsFontAwesome5


#redirect print output to Py4GW Console
class Py4GWLogger:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Info)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing
    
class Py4GWLoggerError:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Error)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing

# Redirect Python's print output to Py4GW Console
sys.stdout = Py4GWLogger()
sys.stderr = Py4GWLoggerError()