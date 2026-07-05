"""Pivot integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant

from .bank_control import setup_bank_control_listener
from .blueprints import install_blueprints
from .button import setup_button_event_listener
from .const import (
    CONF_DEVICE_SUFFIX, CONF_FRIENDLY_NAME,
    CONF_ANNOUNCEMENTS, CONF_TTS_ENTITY, CONF_MEDIA_PLAYER_ENTITY,
    CONF_MANAGEMENT_MODE,
    MANAGEMENT_BLUEPRINTS,
    NUM_BANKS, PASSIVE_DOMAINS, entity_id as make_entity_id,
)
from .device_sync import setup_device_sync
from .entity_mappings import SyncContextTracker
from .mirror import setup_mirror_listeners

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "switch", "text", "binary_sensor", "light", "select"]


@dataclass
class PivotRuntimeData:
    """Runtime state for one Pivot config entry."""

    # Unsubscribe callbacks for all registered state-change listeners.
    unsubs: list[CALLBACK_TYPE] = field(default_factory=list)
    # Pending value-announcement debounce cancel handles, keyed by bank index.
    announce_cancels: dict[int, CALLBACK_TYPE] = field(default_factory=dict)
    # Context IDs of Pivot-initiated sync writes (loop prevention).
    sync_contexts: SyncContextTracker = field(default_factory=SyncContextTracker)


PivotConfigEntry = ConfigEntry[PivotRuntimeData]


# ---------------------------------------------------------------------------
# Entry setup / teardown
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: PivotConfigEntry) -> bool:
    """Set up Pivot from a config entry."""
    data = PivotRuntimeData()
    entry.runtime_data = data

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

    # One-time seed of initial bank assignments from the config flow.
    # The banks_initial step stores bank_N_entity values in entry.data, but
    # bank assignments live in the text entities — apply them once, then
    # strip the keys so a later restart can never overwrite user changes.
    _seed_keys = [k for k in (f"bank_{i}_entity" for i in range(NUM_BANKS)) if k in entry.data]
    if _seed_keys:
        for _key in _seed_keys:
            _value = entry.data[_key]
            if not _value:
                continue
            _bank_no = int(_key.split("_")[1]) + 1
            _text_eid = make_entity_id("text", suffix, f"bank_{_bank_no}_entity")
            try:
                await hass.services.async_call(
                    "text", "set_value",
                    {"entity_id": _text_eid, "value": _value},
                    blocking=True,
                )
            except Exception as err:
                _LOGGER.warning("Pivot: could not seed bank assignment %s=%s: %s", _text_eid, _value, err)
        hass.config_entries.async_update_entry(
            entry, data={k: v for k, v in entry.data.items() if k not in _seed_keys}
        )

    data.unsubs.extend(setup_bank_control_listener(
        hass, entry,
        sync_contexts=data.sync_contexts,
        tts_entity=_tts,
        media_player=_mp,
        announce_enabled=_announce_enabled,
        announce_cancels=data.announce_cancels,
    ))

    unsub_button = setup_button_event_listener(
        hass, entry,
        tts_entity=_tts,
        media_player=_mp,
        announce_enabled=_announce_enabled,
    )
    if unsub_button:
        data.unsubs.append(unsub_button)

    # Zero passive banks on startup so firmware cache is correct after HA restarts.
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

    data.unsubs.extend(setup_mirror_listeners(hass, entry))

    # Push settings to the device once HA has started — the ESPHome state
    # subscription alone cannot guarantee delivery across HA restarts.
    data.unsubs.extend(setup_device_sync(hass, entry))

    management_mode = (
        entry.options.get(CONF_MANAGEMENT_MODE)
        or entry.data.get(CONF_MANAGEMENT_MODE)
        or MANAGEMENT_BLUEPRINTS
    )

    if management_mode == MANAGEMENT_BLUEPRINTS:
        await install_blueprints(hass, entry)

    _LOGGER.info("Pivot: set up '%s' (suffix: %s, mode: %s)", friendly_name, suffix, management_mode)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PivotConfigEntry) -> bool:
    """Unload a Pivot config entry."""
    data = entry.runtime_data
    for unsub in data.unsubs:
        unsub()
    data.unsubs.clear()
    for cancel in data.announce_cancels.values():
        cancel()
    data.announce_cancels.clear()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
