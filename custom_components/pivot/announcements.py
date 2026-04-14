"""TTS announcement helpers for Pivot."""
from __future__ import annotations

import logging

from homeassistant.core import CALLBACK_TYPE, HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Domains that support continuous value announcements (e.g. "Brightness 70 percent").
# Passive domains (scene, script, switch, input_boolean) are excluded — their
# knob position has no meaningful value to announce.
ANNOUNCEABLE_DOMAINS: frozenset[str] = frozenset(
    ("light", "fan", "climate", "media_player", "cover", "number", "input_number")
)


def format_value_announcement(hass: HomeAssistant, bank_entity: str, bank_value: float) -> str | None:
    """Build a TTS message string for a value announcement.

    Uses the knob position (bank_value) for light/fan/media_player/cover since
    the entity may still be transitioning at announcement time. For climate and
    cover, reads the actual attribute value post-debounce so the spoken
    temperature/position reflects what the entity confirmed, not the knob target.
    """
    if not bank_entity or "." not in bank_entity:
        return None
    domain = bank_entity.split(".")[0]
    if domain not in ANNOUNCEABLE_DOMAINS:
        return None
    entity_state = hass.states.get(bank_entity)
    if entity_state is None or entity_state.state in ("unavailable", "unknown"):
        return None
    if domain == "climate":
        temp = entity_state.attributes.get("temperature")
        if temp is None:
            return None
        return f"Temperature {round(float(temp))} degrees."
    if domain == "cover":
        pos = entity_state.attributes.get("current_position")
        if pos is None:
            return None
        return f"{round(float(pos))} percent open."
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


# Re-export CALLBACK_TYPE so callers that store cancel handles can type them correctly
# without importing directly from homeassistant.core.
__all__ = ["ANNOUNCEABLE_DOMAINS", "format_value_announcement", "do_tts", "CALLBACK_TYPE"]
