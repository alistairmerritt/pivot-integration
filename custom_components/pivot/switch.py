"""Switch entities for Pivot (control mode, show control value, announcements)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_SUFFIX, CONF_ANNOUNCEMENTS, get_switch_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)

# The key used in switch definitions to identify the announcements switch.
# This switch is config-backed, not restore-backed (see below).
ANNOUNCEMENTS_KEY = "announcements"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]

    # config_entry.options is canonical after any options flow save + reload.
    # Falls back to data for first-run before options have ever been set.
    announce_default: bool = config_entry.options.get(
        CONF_ANNOUNCEMENTS,
        config_entry.data.get(CONF_ANNOUNCEMENTS, True),
    )

    async_add_entities([
        PivotSwitch(defn, config_entry)
        for defn in get_switch_definitions(suffix, announce_default)
    ])


class PivotSwitch(PivotEntity, SwitchEntity):
    """
    A switch entity for Pivot.

    The announcements switch is treated as config-backed: its state is always
    initialised from config_entry.options (or data on first run) rather than
    from restored entity history. This ensures that when the user changes the
    option and the integration reloads via OptionsFlowWithReload, the switch
    reflects the new config immediately with no ambiguity about restore
    precedence.

    All other switches (control_mode, show_control_value) use normal restore
    behaviour because they represent live device state rather than a user
    config preference.
    """

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._is_config_backed: bool = definition.get("key") == ANNOUNCEMENTS_KEY
        self._attr_is_on: bool = definition["initial"]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        if self._is_config_backed:
            # Config-backed: options are already applied via definition["initial"]
            # set at setup time. Do not restore old entity state — the config
            # entry is the authority, not history.
            return

        # Normal restore for non-config-backed switches
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
