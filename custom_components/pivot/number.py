"""Number entities for Pivot."""
from __future__ import annotations

import logging
import math

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_SUFFIX, get_number_definitions, get_timer_number_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    async_add_entities([
        PivotNumber(defn, config_entry)
        for defn in get_number_definitions(suffix) + get_timer_number_definitions(suffix)
    ])


class PivotNumber(PivotEntity, RestoreNumber):

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._attr_native_min_value = definition["min"]
        self._attr_native_max_value = definition["max"]
        self._attr_native_step = definition["step"]
        self._attr_native_unit_of_measurement = definition.get("unit")
        self._attr_native_value: float = definition["initial"]
        self._attr_mode = NumberMode.BOX if definition.get("mode") == "box" else NumberMode.SLIDER

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_data := await self.async_get_last_number_data()) is not None:
            if last_data.native_value is not None:
                restored = float(last_data.native_value)
                if not math.isnan(restored) and not math.isinf(restored):
                    self._attr_native_value = max(
                        self._attr_native_min_value,
                        min(self._attr_native_max_value, restored)
                    )

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        if math.isnan(value) or math.isinf(value):
            return
        self._attr_native_value = max(
            self._attr_native_min_value,
            min(self._attr_native_max_value, value)
        )
        self.async_write_ha_state()
