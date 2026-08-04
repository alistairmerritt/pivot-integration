"""TTS announcement helpers for Pivot."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Domains that support continuous value announcements (e.g. "Brightness 70 percent").
# Passive domains (scene, script, switch, input_boolean) are excluded — their
# knob position has no meaningful value to announce.
ANNOUNCEABLE_DOMAINS: frozenset[str] = frozenset(
    ("light", "fan", "climate", "media_player", "cover", "number", "input_number")
)


def format_value_announcement(hass: HomeAssistant, bank_entity: str, bank_value: float) -> str | None:
    """Build a TTS message for a value change. Uses knob position, not entity state."""
    if not bank_entity or "." not in bank_entity:
        return None
    domain = bank_entity.split(".")[0]
    if domain not in ANNOUNCEABLE_DOMAINS:
        return None
    entity_state = hass.states.get(bank_entity)
    if entity_state is None or entity_state.state in ("unavailable", "unknown"):
        return None
    if domain == "climate":
        try:
            min_temp = float(entity_state.attributes.get("min_temp", 16))
            max_temp = float(entity_state.attributes.get("max_temp", 30))
            target = min_temp + (bank_value / 100.0) * (max_temp - min_temp)
            target = max(min_temp, min(max_temp, target))
        except (TypeError, ValueError):
            return None
        return f"Temperature {round(target)} degrees."
    if domain == "cover":
        pos = round(bank_value)
        if pos == 0:
            return "Closing."
        if pos == 100:
            return "Opening."
        return f"{pos} percent open."
    if domain == "light":
        return f"Brightness {round(bank_value)} percent."
    if domain == "media_player":
        return f"Volume {round(bank_value)} percent."
    if domain == "fan":
        return f"Speed {round(bank_value)} percent."
    if domain in ("number", "input_number"):
        unit = entity_state.attributes.get("unit_of_measurement") or ""
        return f"Set to {entity_state.state}{' ' + unit if unit else ''}."
    return None


def clip_id_for_value(hass: HomeAssistant, bank_entity: str, bank_value: float) -> str | None:
    """Map a knob value to a pre-baked local announcement clip id (audio_file id
    in the firmware), e.g. "ann_brightness_47". Mirrors format_value_announcement's
    wording but returns the clip to play LOCALLY instead of speaking via HA TTS
    (which crashes on ESPHome 2026.6+, voice-pe#613).

    Scope: light/fan/media_player/cover (percent) and climate (degrees). Returns
    None for number/input_number (custom units aren't pre-baked) and passive
    domains, so those simply aren't announced.
    """
    if not bank_entity or "." not in bank_entity:
        return None
    domain = bank_entity.split(".")[0]
    entity_state = hass.states.get(bank_entity)
    if entity_state is None or entity_state.state in ("unavailable", "unknown"):
        return None

    def clamp(x: float) -> int:
        return max(0, min(100, int(round(x))))

    if domain == "light":
        return f"ann_brightness_{clamp(bank_value)}"
    if domain == "media_player":
        return f"ann_volume_{clamp(bank_value)}"
    if domain == "fan":
        return f"ann_speed_{clamp(bank_value)}"
    if domain == "cover":
        # clip 0 = "Closing", 100 = "Opening", 1..99 = "{n} percent open"
        return f"ann_cover_{clamp(bank_value)}"
    if domain == "climate":
        try:
            min_temp = float(entity_state.attributes.get("min_temp", 16))
            max_temp = float(entity_state.attributes.get("max_temp", 30))
            target = min_temp + (bank_value / 100.0) * (max_temp - min_temp)
        except (TypeError, ValueError):
            return None
        return f"ann_temp_{clamp(target)}"
    return None


async def do_tts(hass: HomeAssistant, tts_entity: str, media_player: str, message: str) -> None:
    """Call tts.speak with the given message."""
    if not tts_entity or not media_player or not message:
        return
    try:
        await hass.services.async_call(
            "tts", "speak",
            {
                "entity_id": tts_entity,
                "media_player_entity_id": media_player,
                "message": message.strip(),
            },
            blocking=False,
        )
    except Exception as err:
        _LOGGER.debug("Pivot: TTS call failed (entity=%s message=%r): %s", tts_entity, message, err)
