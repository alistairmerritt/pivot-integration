"""Mirror light colour listeners for Pivot bank LEDs."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import BANK_COLORS_HEX, CONF_DEVICE_SUFFIX, NUM_BANKS, entity_id as make_entity_id

_LOGGER = logging.getLogger(__name__)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def setup_mirror_listeners(hass: HomeAssistant, entry: ConfigEntry) -> list:
    """Register state listeners for mirror light feature.

    For each bank, if switch.{suffix}_bank_N_mirror_light is on and the bank's
    assigned entity is an RGB light that is on, write its colour as hex to
    text.{suffix}_bank_N_color so the firmware picks it up via the existing
    ha_bank_color_N text sensor sync.

    Returns unsub list.
    """
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    unsubs = []

    def _apply_mirror_for_bank(bank: int) -> None:
        """Check mirror state for one bank and write hex to color text entity."""
        mirror_switch_id = make_entity_id("switch", suffix, f"bank_{bank + 1}_mirror_light")
        bank_entity_id = make_entity_id("text", suffix, f"bank_{bank + 1}_entity")
        color_text_id = make_entity_id("text", suffix, f"bank_{bank + 1}_color")
        configured_text_id = make_entity_id("text", suffix, f"bank_{bank + 1}_configured_color")

        # Always compute the user's configured color from the color picker light.
        # Write it to bank_N_configured_color regardless of mirror state — this entity
        # is never overwritten by the mirror listener, so the firmware can always read
        # the user's chosen color from it (used for Bank Indicator identity colors).
        color_light_id = make_entity_id("light", suffix, f"bank_{bank + 1}_color_light")
        color_light_state = hass.states.get(color_light_id)
        rgb = color_light_state.attributes.get("rgb_color") if color_light_state else None
        if rgb and len(rgb) == 3:
            configured_hex = rgb_to_hex(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        else:
            configured_hex = BANK_COLORS_HEX[bank]
        current_configured = hass.states.get(configured_text_id)
        if not current_configured or current_configured.state.upper() != configured_hex.upper():
            hass.async_create_task(
                hass.services.async_call(
                    "text", "set_value",
                    {"entity_id": configured_text_id, "value": configured_hex},
                    blocking=False,
                )
            )

        mirror_state = hass.states.get(mirror_switch_id)
        if not mirror_state or mirror_state.state != "on":
            # Mirror turned off — restore the configured color to the display entity too
            current = hass.states.get(color_text_id)
            if not current or current.state.upper() != configured_hex.upper():
                _LOGGER.debug("Pivot mirror: bank %d mirror off, restoring user color %s", bank, configured_hex)
                hass.async_create_task(
                    hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": color_text_id, "value": configured_hex},
                        blocking=False,
                    )
                )
            return

        bank_entity_state = hass.states.get(bank_entity_id)
        if not bank_entity_state or bank_entity_state.state in ("", "unknown", "unavailable"):
            return  # no entity assigned

        assigned = bank_entity_state.state
        if not assigned.startswith("light."):
            return  # not a light

        light_state = hass.states.get(assigned)
        if not light_state or light_state.state != "on":
            return  # light is off — leave bank color as-is

        rgb = light_state.attributes.get("rgb_color")
        if not rgb or len(rgb) != 3:
            return  # no RGB color available

        hex_color = rgb_to_hex(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        # Check if color text entity already has this value to avoid loops
        current = hass.states.get(color_text_id)
        if current and current.state.upper() == hex_color.upper():
            return

        _LOGGER.debug("Pivot mirror: bank %d writing %s to %s", bank, hex_color, color_text_id)
        hass.async_create_task(
            hass.services.async_call(
                "text", "set_value",
                {"entity_id": color_text_id, "value": hex_color},
                blocking=False,
            )
        )

    @callback
    def _on_any_change(event) -> None:
        """Called when any watched entity changes — recheck all banks."""
        for bank in range(NUM_BANKS):
            _apply_mirror_for_bank(bank)

    watch_entities = []
    for bank in range(NUM_BANKS):
        watch_entities.append(make_entity_id("switch", suffix, f"bank_{bank + 1}_mirror_light"))
        watch_entities.append(make_entity_id("text", suffix, f"bank_{bank + 1}_entity"))

    unsubs.append(
        async_track_state_change_event(hass, watch_entities, _on_any_change)
    )

    def _get_assigned_lights() -> list[str]:
        lights = []
        for bank in range(NUM_BANKS):
            bank_entity_id = make_entity_id("text", suffix, f"bank_{bank + 1}_entity")
            state = hass.states.get(bank_entity_id)
            if state and state.state.startswith("light."):
                lights.append(state.state)
        return lights

    # Initial check on setup
    for bank in range(NUM_BANKS):
        _apply_mirror_for_bank(bank)

    _light_unsubs = []

    def _register_light_watchers() -> None:
        for u in _light_unsubs:
            u()
        _light_unsubs.clear()
        lights = _get_assigned_lights()
        if lights:
            _light_unsubs.append(
                async_track_state_change_event(hass, lights, _on_any_change)
            )

    @callback
    def _on_bank_entity_change(event) -> None:
        _register_light_watchers()
        _on_any_change(event)

    bank_entity_ids = [
        make_entity_id("text", suffix, f"bank_{bank + 1}_entity")
        for bank in range(NUM_BANKS)
    ]
    unsubs.append(
        async_track_state_change_event(hass, bank_entity_ids, _on_bank_entity_change)
    )

    _register_light_watchers()
    unsubs.append(lambda: [u() for u in _light_unsubs])

    return unsubs
