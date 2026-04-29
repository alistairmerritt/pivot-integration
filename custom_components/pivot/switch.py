"""Switch entities for Pivot (control mode, show control value, announcements)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_SUFFIX, get_switch_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]

    async_add_entities([
        PivotSwitch(defn, config_entry)
        for defn in get_switch_definitions(suffix)
    ])


class PivotSwitch(PivotEntity, SwitchEntity):
    """A switch entity for Pivot. All switches use normal restore behaviour."""

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._attr_is_on: bool = definition["initial"]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._attr_is_on = last.state == "on"
        self.async_write_ha_state()

        # Re-publish the restored state once HA has fully started.
        # The ESPHome firmware subscribes to these entities via WebSocket; if it
        # connects while HA is still starting up it may receive 'unavailable' and
        # latch onto that, ignoring the later restore. Republishing after
        # EVENT_HOMEASSISTANT_STARTED ensures the firmware gets the correct value.
        @callback
        def _on_ha_started(_event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)
        )

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
