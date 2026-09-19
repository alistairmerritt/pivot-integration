"""Apply and sync 0-100 knob values to/from Home Assistant entities."""
from __future__ import annotations

import logging
import math
from collections import OrderedDict

from homeassistant.components.cover import CoverEntityFeature
from homeassistant.core import Context, HomeAssistant, State

from .const import PASSIVE_DOMAINS, STATEFUL_PASSIVE_DOMAINS

_LOGGER = logging.getLogger(__name__)


def cover_is_open_close_only(state: State | None) -> bool:
    """Return True for a cover that opens and closes but takes no position.

    Most garage doors. Some still report a current_position of 0/100, so
    reporting a position is not the same as accepting one: only the
    SET_POSITION feature bit decides. HA keeps supported_features on
    unavailable entities, so the answer holds through outages. With no
    state or no feature attribute, answer False — every caller then keeps
    its original (pre open/close-only) behaviour rather than guessing.
    """
    if state is None:
        return False
    features = state.attributes.get("supported_features")
    if features is None:
        return False
    try:
        return not int(features) & CoverEntityFeature.SET_POSITION
    except (TypeError, ValueError):
        return False


def bank_is_passive(hass: HomeAssistant, entity_id: str) -> bool:
    """Return True if the knob has no value to control for this entity."""
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    if domain in PASSIVE_DOMAINS:
        return True
    return domain == "cover" and cover_is_open_close_only(hass.states.get(entity_id))


def bank_value_held_at_zero(entity_id: str) -> bool:
    """Return True for stateless passive entities (scene, script).

    Their bank value is always 0, so the ring stays off. Stateful passive
    entities (switches, open/close-only covers) mirror their state instead.
    """
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    return domain in PASSIVE_DOMAINS and domain not in STATEFUL_PASSIVE_DOMAINS


class SyncContextTracker:
    """Tracks the context IDs of Pivot-initiated sync writes.

    When Pivot syncs a bank value number from the real entity state, the
    resulting state change must not be mistaken for a physical knob turn
    (which would re-apply the value and fire pivot_knob_turn). Each sync
    write gets a fresh Context whose ID is recorded here; the knob-turn
    listener drops any state change whose context ID matches.

    The ID set is bounded so long-running instances don't accumulate
    context IDs indefinitely.
    """

    def __init__(self, max_ids: int = 64) -> None:
        self._ids: OrderedDict[str, None] = OrderedDict()
        self._max_ids = max_ids

    def new_context(self) -> Context:
        """Create and record a Context for a sync service call."""
        ctx = Context()
        self._ids[ctx.id] = None
        while len(self._ids) > self._max_ids:
            self._ids.popitem(last=False)
        return ctx

    def is_sync_context(self, context: Context | None) -> bool:
        """Return True if the given context came from a Pivot sync write."""
        return context is not None and context.id in self._ids


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
        # Open/close-only covers (most garage doors) reject set_cover_position.
        # Their banks are passive, so the firmware ignores the knob; this
        # guards the window before the passive flag reaches the device.
        if cover_is_open_close_only(hass.states.get(entity_id)):
            return
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
    hass: HomeAssistant, domain: str, entity_id: str, value_entity_id: str,
    sync_contexts: SyncContextTracker,
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
        # Open/close-only cover with no position (e.g. a garage door): show
        # open/closed as a full/empty ring. Display only — the bank is
        # passive. Leave the gauge alone while it is moving; the settled state
        # syncs it. A cover that CAN take a position but isn't reporting one
        # keeps its gauge — a guessed 100 would send it to ~98% on the next
        # detent.
        elif cover_is_open_close_only(state):
            if state.state == "open":
                synced_value = 100.0
            elif state.state == "closed":
                synced_value = 0.0
    elif domain in STATEFUL_PASSIVE_DOMAINS:
        # Switch / input_boolean: display only (passive bank) — full ring
        # when on, off when off. Unknown/unavailable leave the gauge alone.
        if state.state == "on":
            synced_value = 100.0
        elif state.state == "off":
            synced_value = 0.0
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

    _LOGGER.debug("Pivot sync: %s (%s) state=%s -> %s", entity_id, domain, state.state, synced_value)

    if synced_value is not None:
        if math.isnan(synced_value) or math.isinf(synced_value):
            _LOGGER.warning("Pivot sync: NaN/inf synced_value for %s, skipping", entity_id)
            return
        synced_value = max(0.0, min(100.0, synced_value))
        # Use a tracked context so _on_bank_value_changed recognises this as
        # a Pivot sync write (non-physical change) and does not fire
        # pivot_knob_turn (which would trigger value announcements).
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": value_entity_id, "value": synced_value},
            context=sync_contexts.new_context(),
        )
