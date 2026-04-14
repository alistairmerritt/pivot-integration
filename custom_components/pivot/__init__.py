"""Pivot integration.

Handles all runtime logic for Pivot devices:
- Bank control: listens for bank value changes and applies them to assigned entities
- Bank sync: when active bank changes, reads entity state and syncs value back
- Bank toggle: performed natively on single_press in control mode; also fires
  pivot_button_press events for user automations
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant

from .bank_control import setup_bank_control_listener
from .blueprints import install_blueprints
from .button import setup_button_event_listener
from .const import (
    DOMAIN, CONF_DEVICE_SUFFIX, CONF_FRIENDLY_NAME,
    CONF_ANNOUNCEMENTS, CONF_TTS_ENTITY, CONF_MEDIA_PLAYER_ENTITY,
    CONF_MANAGEMENT_MODE,
    MANAGEMENT_BLUEPRINTS,
    NUM_BANKS, PASSIVE_DOMAINS, entity_id as make_entity_id,
)
from .mirror import setup_mirror_listeners

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "switch", "text", "binary_sensor", "light", "select"]


# ---------------------------------------------------------------------------
# Entry setup / teardown
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pivot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]

    # Write configured TTS and media player entity IDs to their text entities so
    # the Announce and Timer blueprints can read them without needing manual input.
    _tts = entry.options.get(CONF_TTS_ENTITY) or entry.data.get(CONF_TTS_ENTITY) or ""
    _mp = entry.options.get(CONF_MEDIA_PLAYER_ENTITY) or entry.data.get(CONF_MEDIA_PLAYER_ENTITY) or ""
    _announce_enabled = bool(
        entry.options.get(CONF_ANNOUNCEMENTS, entry.data.get(CONF_ANNOUNCEMENTS, True))
    )

    async def _write_config_text_entities() -> None:
        for _key, _val in [("tts_entity", _tts), ("media_player_entity", _mp)]:
            _eid = make_entity_id("text", suffix, _key)
            if hass.states.get(_eid) is not None:
                try:
                    await hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": _eid, "value": _val},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Pivot: could not write config text entity %s: %s", _eid, err)

    hass.async_create_task(_write_config_text_entities())

    # Debounce cancel handles for native value announcements (bank_idx -> cancel callable)
    _announce_cancels: dict[int, CALLBACK_TYPE] = {}
    hass.data[DOMAIN][entry.entry_id + "_announce_cancels"] = _announce_cancels

    # Set up internal listeners for bank control and bank sync
    unsubs = setup_bank_control_listener(
        hass, entry,
        tts_entity=_tts,
        media_player=_mp,
        announce_enabled=_announce_enabled,
        announce_cancels=_announce_cancels,
    )

    # Set up button event listener separately — handles press events and fires
    # pivot_button_press on the HA event bus. Kept outside bank_control so each
    # module has a single, clear responsibility.
    unsub_button = setup_button_event_listener(
        hass, entry,
        tts_entity=_tts,
        media_player=_mp,
        announce_enabled=_announce_enabled,
    )
    if unsub_button:
        unsubs.append(unsub_button)

    hass.data[DOMAIN][entry.entry_id + "_unsub"] = unsubs

    # Zero bank values for passive domains on startup so the firmware cache
    # is correct even if HA restarted while a passive entity was assigned.
    for _i in range(NUM_BANKS):
        _text_eid = f"text.{suffix}_bank_{_i + 1}_entity"
        _value_eid = f"number.{suffix}_bank_{_i + 1}_value"

        async def _zero_if_passive(t_eid=_text_eid, v_eid=_value_eid) -> None:
            text_state = hass.states.get(t_eid)
            if text_state is None or text_state.state in ("", "unknown", "unavailable"):
                return
            bank_entity = text_state.state
            if "." not in bank_entity:
                return
            if bank_entity.split(".")[0] in PASSIVE_DOMAINS:
                try:
                    await hass.services.async_call(
                        "number", "set_value",
                        {"entity_id": v_eid, "value": 0},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Pivot: could not zero passive bank value %s: %s", v_eid, err)

        hass.async_create_task(_zero_if_passive())

    # Set up mirror light listeners — watches assigned lights and mirror switches,
    # writes hex colour to the bank colour text entity when mirror is enabled.
    unsubs_mirror = setup_mirror_listeners(hass, entry)
    hass.data[DOMAIN][entry.entry_id + "_unsub_mirror"] = unsubs_mirror

    management_mode = (
        entry.options.get(CONF_MANAGEMENT_MODE)
        or entry.data.get(CONF_MANAGEMENT_MODE)
        or MANAGEMENT_BLUEPRINTS
    )

    if management_mode == MANAGEMENT_BLUEPRINTS:
        await install_blueprints(hass, entry)
    # MANAGEMENT_NEITHER: do nothing

    _LOGGER.info("Pivot: set up '%s' (suffix: %s, mode: %s)", friendly_name, suffix, management_mode)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Pivot config entry."""
    # Cancel state change listeners (includes button listener)
    for unsub in hass.data[DOMAIN].pop(entry.entry_id + "_unsub", []):
        unsub()

    # Cancel mirror listeners
    for unsub in hass.data[DOMAIN].pop(entry.entry_id + "_unsub_mirror", []):
        unsub()

    # Cancel any pending value-announcement debounce timers
    for cancel in hass.data[DOMAIN].pop(entry.entry_id + "_announce_cancels", {}).values():
        cancel()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
