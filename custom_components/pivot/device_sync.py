"""Push Pivot settings directly to the device via an ESPHome action.

The ESPHome state subscription cannot be relied on for startup correctness:
Home Assistant's ESPHome integration forwards only genuine state *changes*
to the device — entity-addition events (old_state=None) and same-state
writes are dropped. A device that connects and subscribes before Pivot's
entities are restored (typical during HA startup) therefore never receives
their values, and nothing self-heals until the user toggles a setting.

This module closes that hole by pushing all settings explicitly through the
firmware's `pivot_sync_settings` user-defined action once Home Assistant has
fully started. Devices that (re)connect after startup are already covered:
the ESPHome integration sends current states on subscription when the
entities exist. With firmware that predates the action, the service does
not exist and the push is skipped silently.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.start import async_at_started

from .const import (
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    NUM_BANKS,
    make_suffix,
)

_LOGGER = logging.getLogger(__name__)

SYNC_ACTION = "pivot_sync_settings"


def setup_device_sync(hass: HomeAssistant, entry: ConfigEntry) -> list[CALLBACK_TYPE]:
    """Register the settings push at HA start.

    Returns a list of unsubscribe callbacks.
    """
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    esphome_name = entry.data.get(CONF_ESPHOME_DEVICE_NAME) or ""
    if not esphome_name:
        _LOGGER.debug(
            "Pivot: no ESPHome device name stored for %s — settings push disabled",
            suffix,
        )
        return []

    # ESPHome registers device actions as esphome.<device_name_slug>_<action>.
    service_name = f"{make_suffix(esphome_name)}_{SYNC_ACTION}"

    def _read_bool(entity_id: str) -> bool | None:
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state.state == "on"

    async def _push_settings() -> None:
        if not hass.services.has_service("esphome", service_name):
            _LOGGER.debug(
                "Pivot: esphome.%s not available (device offline or firmware "
                "without %s) — skipping settings push",
                service_name, SYNC_ACTION,
            )
            return

        sources = {
            "control_mode_in": f"switch.{suffix}_control_mode",
            "show_control_value_in": f"switch.{suffix}_show_control_value",
            "dim_when_idle_in": f"switch.{suffix}_dim_when_idle",
        }
        for bank in range(NUM_BANKS):
            sources[f"bank_mirror_{bank + 1}_in"] = (
                f"switch.{suffix}_bank_{bank + 1}_mirror_light"
            )
            sources[f"bank_passive_{bank + 1}_in"] = (
                f"binary_sensor.{suffix}_bank_{bank + 1}_passive"
            )

        data: dict[str, bool] = {}
        for key, entity_id in sources.items():
            value = _read_bool(entity_id)
            if value is None:
                # Never push partial defaults — leaving the device with its
                # cached values is safer than overwriting them with guesses.
                _LOGGER.debug(
                    "Pivot: %s not ready — skipping settings push", entity_id
                )
                return
            data[key] = value

        _LOGGER.debug("Pivot: pushing settings via esphome.%s: %s", service_name, data)
        try:
            await hass.services.async_call(
                "esphome", service_name, data, blocking=False
            )
        except Exception as err:
            _LOGGER.debug(
                "Pivot: settings push via esphome.%s failed: %s", service_name, err
            )

    @callback
    def _on_started(_hass: HomeAssistant) -> None:
        hass.async_create_task(_push_settings())

    # Fires once HA has fully started, or immediately if it already has
    # (e.g. on entry reload).
    return [async_at_started(hass, _on_started)]
