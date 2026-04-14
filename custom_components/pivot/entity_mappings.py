"""Apply and sync 0-100 knob values to/from Home Assistant entities."""
from __future__ import annotations

import logging
import math

from homeassistant.core import Context, HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def apply_value_to_entity(
    hass: HomeAssistant, domain: str, entity_id: str, value: float
) -> None:
    """Call the appropriate service to apply a 0-100 value to an entity."""
    if math.isnan(value) or math.isinf(value):
        return
    value = max(0.0, min(100.0, value))
    if domain == "light":
        await hass.services.async_call(
            "light", "turn_on",
            {"entity_id": entity_id, "brightness_pct": round(value)},
        )
    elif domain == "fan":
        await hass.services.async_call(
            "fan", "set_percentage",
            {"entity_id": entity_id, "percentage": round(value)},
        )
    elif domain == "climate":
        state = hass.states.get(entity_id)
        if state is None:
            return
        try:
            min_temp = float(state.attributes.get("min_temp", 16))
            max_temp = float(state.attributes.get("max_temp", 30))
            step = float(state.attributes.get("target_temp_step", 0.5))
        except (ValueError, TypeError):
            return
        if max_temp <= min_temp:
            return
        temp = min_temp + (value / 100.0) * (max_temp - min_temp)
        temp = round(round(temp / step) * step, 10)  # snap to step
        temp = round(max(min_temp, min(max_temp, temp)), 2)
        await hass.services.async_call(
            "climate", "set_temperature",
            {"entity_id": entity_id, "temperature": temp},
        )
    elif domain == "media_player":
        await hass.services.async_call(
            "media_player", "volume_set",
            {"entity_id": entity_id, "volume_level": round(value / 100, 2)},
        )
    elif domain == "cover":
        await hass.services.async_call(
            "cover", "set_cover_position",
            {"entity_id": entity_id, "position": round(value)},
        )
    elif domain in ("input_number", "number"):
        state = hass.states.get(entity_id)
        if state is None:
            return
        try:
            min_val = float(state.attributes.get("min", 0))
            max_val = float(state.attributes.get("max", 100))
            step = float(state.attributes.get("step", 1))
        except (ValueError, TypeError):
            return
        scaled = min_val + (value / 100.0) * (max_val - min_val)
        # Snap to the entity's own step size to avoid rejection from HA validation
        if step > 0:
            scaled = round(round(scaled / step) * step, 10)
        scaled = round(max(min_val, min(max_val, scaled)), 2)
        await hass.services.async_call(
            domain, "set_value",
            {"entity_id": entity_id, "value": scaled},
        )


async def sync_value_from_entity(
    hass: HomeAssistant, domain: str, entity_id: str, value_entity_id: str
) -> None:
    """Read current state from an entity and sync it to the bank value number."""
    state = hass.states.get(entity_id)
    if state is None:
        return

    synced_value: float | None = None

    if domain == "light":
        if state.state == "off":
            synced_value = 0.0
        else:
            brightness = state.attributes.get("brightness")
            if brightness is not None:
                synced_value = round(float(brightness) / 255 * 100)
            else:
                # Light is on but has no brightness attribute (non-dimmable).
                # Report 100% so the knob reflects "fully on" rather than 0%.
                synced_value = 100.0
    elif domain == "fan":
        pct = state.attributes.get("percentage")
        if pct is not None:
            synced_value = round(float(pct))
    elif domain == "climate":
        temp = state.attributes.get("temperature")
        if temp is not None:
            try:
                min_temp = float(state.attributes.get("min_temp", 16))
                max_temp = float(state.attributes.get("max_temp", 30))
            except (ValueError, TypeError):
                # Cannot determine range — skip sync rather than using a
                # hardcoded Celsius fallback that may be wrong for Fahrenheit.
                return
            if max_temp > min_temp:
                synced_value = round((float(temp) - min_temp) / (max_temp - min_temp) * 100)
            else:
                synced_value = 0.0
    elif domain == "media_player":
        vol = state.attributes.get("volume_level")
        if vol is not None:
            synced_value = round(float(vol) * 100)
    elif domain == "cover":
        pos = state.attributes.get("current_position")
        if pos is not None:
            synced_value = round(float(pos))
    elif domain in ("input_number", "number"):
        try:
            raw = float(state.state)
        except (ValueError, TypeError):
            raw = None
        if raw is not None:
            try:
                min_val = float(state.attributes.get("min", 0))
                max_val = float(state.attributes.get("max", 100))
            except (ValueError, TypeError):
                return
            if max_val != min_val:
                synced_value = round((raw - min_val) / (max_val - min_val) * 100)
            else:
                synced_value = 0.0

    _LOGGER.debug(
        "Pivot sync: entity=%s domain=%s state=%s brightness=%s vol=%s pct=%s temp=%s pos=%s -> synced_value=%s",
        entity_id, domain, state.state,
        state.attributes.get("brightness"),
        state.attributes.get("volume_level"),
        state.attributes.get("percentage"),
        state.attributes.get("temperature"),
        state.attributes.get("current_position"),
        synced_value,
    )

    if synced_value is not None:
        if math.isnan(synced_value) or math.isinf(synced_value):
            _LOGGER.warning("Pivot sync: NaN/inf synced_value for %s, skipping", entity_id)
            return
        synced_value = max(0.0, min(100.0, synced_value))
        # Pass a context with a parent_id so _on_bank_value_changed's
        # parent_id guard treats this as a non-physical change and does
        # not fire pivot_knob_turn (which would trigger value announcements).
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": value_entity_id, "value": synced_value},
            context=Context(parent_id="pivot_sync"),
        )
