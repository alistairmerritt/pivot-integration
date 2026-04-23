"""Constants for the Pivot integration."""

DOMAIN = "pivot"

# Config entry data keys
CONF_DEVICE_ID = "device_id"           # HA device registry UUID
CONF_ESPHOME_DEVICE_NAME = "esphome_device_name"  # e.g. "home-assistant-voice-092e7d"
CONF_DEVICE_SUFFIX = "device_suffix"   # slugified ESPHome name, e.g. "home_assistant_voice_092e7d"
CONF_FRIENDLY_NAME = "friendly_name"   # HA display name, e.g. "Living Room VPE"
CONF_ANNOUNCEMENTS = "announcements"   # bool — enable/disable all spoken announcements
CONF_TTS_ENTITY = "tts_entity"         # kept for migration compat
CONF_MEDIA_PLAYER_ENTITY = "media_player_entity"  # kept for migration compat
CONF_MANAGEMENT_MODE = "management_mode"  # "managed" | "blueprints" | "neither"

# Management mode values
MANAGEMENT_BLUEPRINTS = "blueprints"
MANAGEMENT_NEITHER = "neither"

NUM_BANKS = 4

# Domains where the knob has no meaningful continuous value to control.
# Single press toggles/fires them; the LED gauge is zeroed when one is assigned.
PASSIVE_DOMAINS: frozenset[str] = frozenset({"scene", "script", "switch", "input_boolean"})

# RGB tuples matching the firmware LED colours — used for UI hints
BANK_COLORS_RGB = {
    0: (40, 137, 255),
    1: (255, 125, 25),
    2: (151, 255, 61),
    3: (200, 0, 255),
}

# Default hex colours per bank — used to restore when mirror is turned off
BANK_COLORS_HEX = {
    0: "#2889FF",  # Blue
    1: "#FF7D19",  # Orange
    2: "#97FF3D",  # Green
    3: "#C800FF",  # Purple
}


def make_suffix(esphome_device_name: str) -> str:
    """
    Convert an ESPHome device name into a safe entity ID suffix.
    e.g. "home-assistant-voice-092e7d" -> "home_assistant_voice_092e7d"
    """
    slug = esphome_device_name.lower().replace("-", "_").replace(" ", "_")
    return "".join(c for c in slug if c.isalnum() or c == "_")


def entity_unique_id(suffix: str, key: str) -> str:
    """Build a unique_id. e.g. "pivot_home_assistant_voice_092e7d_bank_1_value" """
    return f"pivot_{suffix}_{key}"


def entity_id(platform: str, suffix: str, key: str) -> str:
    """
    Build the explicit entity ID to match what the firmware expects.
    e.g. "number.home_assistant_pivot_test_bank_1_value"
    Must be set explicitly — otherwise HA auto-generates from device+entity
    name which produces the wrong result (uses friendly name not ESPHome slug).
    """
    return f"{platform}.{suffix}_{key}"


def get_number_definitions(suffix: str) -> list[dict]:
    """All number entities for one Pivot device."""
    defs = []

    for bank in range(NUM_BANKS):
        defs.append({
            "platform": "number",
            "key": f"bank_{bank + 1}_value",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_value"),
            "entity_id": entity_id("number", suffix, f"bank_{bank + 1}_value"),
            "name": f"Bank {bank + 1} Value",
            "icon": "mdi:brightness-6",
            "min": 0.0,
            "max": 100.0,
            "step": 1.0,
            "unit": "%",
            "initial": 0.0,
        })

    defs.append({
        "platform": "number",
        "key": "active_bank",
        "unique_id": entity_unique_id(suffix, "active_bank"),
        "entity_id": entity_id("number", suffix, "active_bank"),
        "name": "Active Bank",
        "icon": "mdi:layers",
        "min": 1.0,
        "max": 4.0,
        "step": 1.0,
        "unit": None,
        "initial": 1.0,
        "mode": "box",
    })

    return defs


def get_switch_definitions(suffix: str) -> list[dict]:
    """All switch entities for one Pivot device."""
    switches = [
        {
            "platform": "switch",
            "key": "control_mode",
            "unique_id": entity_unique_id(suffix, "control_mode"),
            "entity_id": entity_id("switch", suffix, "control_mode"),
            "name": "Control Mode",
            "icon": "mdi:knob",
            "initial": False,
        },
        {
            "platform": "switch",
            "key": "show_control_value",
            "unique_id": entity_unique_id(suffix, "show_control_value"),
            "entity_id": entity_id("switch", suffix, "show_control_value"),
            "name": "Show Control Value",
            "icon": "mdi:led-on",
            "initial": False,
        },
        {
            "platform": "switch",
            "key": "dim_when_idle",
            "unique_id": entity_unique_id(suffix, "dim_when_idle"),
            "entity_id": entity_id("switch", suffix, "dim_when_idle"),
            "name": "Dim LEDs When Idle",
            "icon": "mdi:brightness-4",
            "initial": False,
        },
        {
            "platform": "switch",
            "key": "announcements",
            "unique_id": entity_unique_id(suffix, "announcements"),
            "entity_id": entity_id("switch", suffix, "announcements"),
            "name": "System Announcements",
            "icon": "mdi:bullhorn",
            "initial": True,
        },
        {
            "platform": "switch",
            "key": "mute_announcements",
            "unique_id": entity_unique_id(suffix, "mute_announcements"),
            "entity_id": entity_id("switch", suffix, "mute_announcements"),
            "name": "Mute Announcements",
            "icon": "mdi:volume-off",
            "initial": False,
        },
    ]
    # Per-bank mirror light and announce value switches
    for bank in range(NUM_BANKS):
        switches.append({
            "platform": "switch",
            "key": f"bank_{bank + 1}_mirror_light",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_mirror_light"),
            "entity_id": entity_id("switch", suffix, f"bank_{bank + 1}_mirror_light"),
            "name": f"Bank {bank + 1} Mirror Light",
            "icon": "mdi:lightbulb-on",
            "initial": False,
        })
    for bank in range(NUM_BANKS):
        switches.append({
            "platform": "switch",
            "key": f"bank_{bank + 1}_announce_value",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_announce_value"),
            "entity_id": entity_id("switch", suffix, f"bank_{bank + 1}_announce_value"),
            "name": f"Bank {bank + 1} Announce Value",
            "icon": "mdi:volume-high",
            "initial": False,
        })
    return switches


def get_text_definitions(suffix: str) -> list[dict]:
    """All text entities for one Pivot device."""
    return [
        {
            "platform": "text",
            "key": f"bank_{bank + 1}_entity",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_entity"),
            "entity_id": entity_id("text", suffix, f"bank_{bank + 1}_entity"),
            "name": f"Bank {bank + 1} Entity",
            "icon": "mdi:link-variant",
            "initial": "",
            "max_length": 255,
            "validate_entity_id": True,
        }
        for bank in range(NUM_BANKS)
    ]


def get_config_text_definitions(suffix: str) -> list[dict]:
    """Text entities storing the configured TTS and media player entity IDs.

    Written from the config entry on every setup/reload so the Announce and
    Timer blueprints can read them without needing TTS/media player as inputs.
    """
    return [
        {
            "platform": "text",
            "key": "tts_entity",
            "unique_id": entity_unique_id(suffix, "tts_entity"),
            "entity_id": entity_id("text", suffix, "tts_entity"),
            "name": "TTS Entity",
            "icon": "mdi:text-to-speech",
            "initial": "",
            "max_length": 255,
            "entity_category": "diagnostic",
        },
        {
            "platform": "text",
            "key": "media_player_entity",
            "unique_id": entity_unique_id(suffix, "media_player_entity"),
            "entity_id": entity_id("text", suffix, "media_player_entity"),
            "name": "Media Player Entity",
            "icon": "mdi:speaker",
            "initial": "",
            "max_length": 255,
            "entity_category": "diagnostic",
        },
    ]


def get_binary_sensor_definitions(suffix: str) -> list[dict]:
    """Passive-flag binary sensors for each bank (true = scene/script, knob disabled)."""
    return [
        {
            "platform": "binary_sensor",
            "key": f"bank_{bank + 1}_passive",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_passive"),
            "entity_id": entity_id("binary_sensor", suffix, f"bank_{bank + 1}_passive"),
            "name": f"Bank {bank + 1} Passive",
            "icon": "mdi:lightning-bolt-off",
        }
        for bank in range(NUM_BANKS)
    ]


def get_color_text_definitions(suffix: str) -> list[dict]:
    """Hidden text entities storing hex colour per bank (read by firmware)."""
    return [
        {
            "platform": "text",
            "key": f"bank_{bank + 1}_color",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_color"),
            "entity_id": entity_id("text", suffix, f"bank_{bank + 1}_color"),
            "name": f"Bank {bank + 1} Colour",
            "icon": "mdi:palette",
            "initial": BANK_COLORS_HEX[bank],
            "max_length": 7,
            "entity_category": "diagnostic",  # tucked away in UI but enabled so firmware can read it
        }
        for bank in range(NUM_BANKS)
    ]


def get_configured_color_text_definitions(suffix: str) -> list[dict]:
    """Hidden text entities storing the user's configured colour per bank.

    Unlike bank_N_color, these are NEVER overwritten by the mirror feature —
    they always hold whatever the user set in the colour picker. The firmware
    reads them to keep bank_mirror_r/g/b_N in sync so the Bank Indicator shows
    the correct identity colour even when mirror light is active.
    """
    return [
        {
            "platform": "text",
            "key": f"bank_{bank + 1}_configured_color",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_configured_color"),
            "entity_id": entity_id("text", suffix, f"bank_{bank + 1}_configured_color"),
            "name": f"Bank {bank + 1} Configured Colour",
            "icon": "mdi:palette-outline",
            "initial": BANK_COLORS_HEX[bank],
            "max_length": 7,
            "entity_category": "diagnostic",  # tucked away but always enabled so firmware can read it
        }
        for bank in range(NUM_BANKS)
    ]


def get_timer_number_definitions(suffix: str) -> list[dict]:
    """Timer duration number entity (disabled by default)."""
    return [
        {
            "platform": "number",
            "key": "timer_duration",
            "unique_id": entity_unique_id(suffix, "timer_duration"),
            "entity_id": entity_id("number", suffix, "timer_duration"),
            "name": "Timer Duration",
            "icon": "mdi:timer-cog-outline",
            "min": 1.0,
            "max": 60.0,
            "step": 1.0,
            "unit": "min",
            "initial": 25.0,
            "mode": "box",
            "entity_registry_enabled_default": False,
        }
    ]


def get_timer_select_definitions(suffix: str) -> list[dict]:
    """Timer state select entity (disabled by default)."""
    return [
        {
            "platform": "select",
            "key": "timer_state",
            "unique_id": entity_unique_id(suffix, "timer_state"),
            "entity_id": entity_id("select", suffix, "timer_state"),
            "name": "Timer State",
            "icon": "mdi:timer",
            "options": ["idle", "running", "paused", "alerting"],
            "initial": "idle",
            "entity_registry_enabled_default": False,
        }
    ]


def get_timer_text_definitions(suffix: str) -> list[dict]:
    """
    Timer end-time text entity (disabled by default).

    Stores the ISO-8601 end timestamp while the timer is running,
    "P{seconds}" of remaining time while paused, or "" when idle.
    Updated exclusively by the pivot_timer blueprint.
    """
    return [
        {
            "platform": "text",
            "key": "timer_end",
            "unique_id": entity_unique_id(suffix, "timer_end"),
            "entity_id": entity_id("text", suffix, "timer_end"),
            "name": "Timer End",
            "icon": "mdi:timer-outline",
            "initial": "",
            "max_length": 50,
            "entity_registry_enabled_default": False,
        },
        {
            "platform": "text",
            "key": "timer_restore_show_value",
            "unique_id": entity_unique_id(suffix, "timer_restore_show_value"),
            "entity_id": entity_id("text", suffix, "timer_restore_show_value"),
            "name": "Timer Restore Show Value",
            "icon": "mdi:restore",
            "initial": "",
            "max_length": 3,
            "entity_registry_enabled_default": False,
            "entity_category": "diagnostic",
        },
    ]


def get_light_definitions(suffix: str) -> list[dict]:
    """Virtual light entities for bank colour pickers."""
    return [
        {
            "platform": "light",
            "key": f"bank_{bank + 1}_color_light",
            "unique_id": entity_unique_id(suffix, f"bank_{bank + 1}_color_light"),
            "entity_id": entity_id("light", suffix, f"bank_{bank + 1}_color_light"),
            "name": f"Bank {bank + 1} Colour",
            "icon": "mdi:palette",
            "default_rgb": BANK_COLORS_RGB[bank],
            "bank": bank,
        }
        for bank in range(NUM_BANKS)
    ]
