"""Pivot virtual light entities for bank colour pickers.

Each bank has a colour-only light entity. When the user picks a colour,
the integration writes the hex value to the corresponding text entity
which the firmware reads and applies to the LED ring.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    get_light_definitions,
    entity_id as make_entity_id,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    async_add_entities([
        PivotBankColorLight(defn, config_entry)
        for defn in get_light_definitions(suffix)
    ])


class PivotBankColorLight(LightEntity, RestoreEntity):
    """A colour-only light entity representing a bank's LED colour."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        self._definition = definition
        self._suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
        self._bank: int = definition["bank"]

        r, g, b = definition["default_rgb"]
        self._rgb: tuple[int, int, int] = (r, g, b)
        self._is_on: bool = True

        self._attr_unique_id = definition["unique_id"]
        self._attr_name = definition["name"]
        self._attr_icon = definition["icon"]

        # Pin entity_id explicitly
        self.entity_id = definition["entity_id"]

        device_id: str = config_entry.data[CONF_DEVICE_ID]
        esphome_name: str = config_entry.data[CONF_ESPHOME_DEVICE_NAME]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._suffix,
            model="Home Assistant Voice Preview Edition",
            manufacturer="Pivot",
            configuration_url=f"http://{esphome_name}.local",
        )

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        return self._rgb

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._is_on = True
        if ATTR_RGB_COLOR in kwargs:
            self._rgb = kwargs[ATTR_RGB_COLOR]
            await self._push_colour()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        # Colour picker — turning off doesn't make sense, just ignore
        self.async_write_ha_state()

    async def _push_colour(self) -> None:
        """Write hex colour to the corresponding text entity for the firmware."""
        r, g, b = self._rgb
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        text_entity_id = make_entity_id("text", self._suffix, f"bank_{self._bank}_color")
        _LOGGER.debug("Pivot: pushing bank %d colour %s to %s", self._bank, hex_color, text_entity_id)
        await self.hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": text_entity_id, "value": hex_color},
            blocking=True,
        )

    async def async_added_to_hass(self) -> None:
        """Restore colour from last known state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("rgb_color"):
            self._rgb = tuple(last_state.attributes["rgb_color"])
            self._is_on = last_state.state != "off"

            async def _push_on_startup() -> None:
                import asyncio
                await asyncio.sleep(3)
                await self._push_colour()

            self.hass.async_create_task(_push_on_startup())
