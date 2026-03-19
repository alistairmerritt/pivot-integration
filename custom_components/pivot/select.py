"""Select entities for Pivot."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_SUFFIX, get_timer_select_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pivot select entities."""
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    async_add_entities([
        PivotSelect(defn, config_entry)
        for defn in get_timer_select_definitions(suffix)
    ])


class PivotSelect(PivotEntity, SelectEntity):
    """
    Select entity for Pivot (timer state mirror).

    Updated by the pivot_timer blueprint to reflect the current timer state.
    Useful for dashboard cards and external automations that need a simple
    idle / running / paused state without reading timer attributes.
    """

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._attr_options = definition["options"]
        self._attr_current_option: str = definition["initial"]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self._attr_options:
            self._attr_current_option = last.state
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
