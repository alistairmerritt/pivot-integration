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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import (
    CONF_DEVICE_SUFFIX,
    get_light_definitions,
    entity_id as make_entity_id,
)
from .entity_base import PivotEntity

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


class PivotBankColorLight(PivotEntity, LightEntity):
    """A colour-only light entity representing a bank's LED colour.

    Always reports as "on" — turning off is a no-op because this entity
    is a colour picker, not a real light switch. The colour is written to
    the firmware via the bank_N_color and bank_N_configured_color text entities.
    """

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
        self._bank: int = definition["bank"]

        r, g, b = definition["default_rgb"]
        self._rgb: tuple[int, int, int] = (r, g, b)
        self._is_on: bool = True

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        return self._rgb

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._is_on = True
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            self._rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            await self._push_colour()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        # This is a colour picker — turning off has no meaning; ignore silently.
        self.async_write_ha_state()

    async def _push_colour(self) -> None:
        """Write hex colour to the corresponding text entities for the firmware.

        Writes to two entities:
        - bank_N_color: the display colour (may be overwritten by the mirror listener)
        - bank_N_configured_color: the user's chosen colour (never overwritten by mirror)
        """
        r, g, b = self._rgb
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        text_entity_id = make_entity_id("text", self._suffix, f"bank_{self._bank}_color")
        configured_entity_id = make_entity_id("text", self._suffix, f"bank_{self._bank}_configured_color")
        _LOGGER.debug("Pivot: pushing bank %d colour %s to %s", self._bank, hex_color, text_entity_id)
        await self.hass.services.async_call(
            "text", "set_value", {"entity_id": text_entity_id, "value": hex_color}, blocking=False,
        )
        await self.hass.services.async_call(
            "text", "set_value", {"entity_id": configured_entity_id, "value": hex_color}, blocking=False,
        )

    async def async_added_to_hass(self) -> None:
        """Restore colour from last known state and push it to the firmware."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("rgb_color"):
            rgb = last_state.attributes["rgb_color"]
            self._rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._is_on = last_state.state != "off"

            @callback
            def _push_on_startup(_now: object) -> None:
                self.hass.async_create_task(self._push_colour())

            # Delay the push so all text entities are ready to receive the value.
            # Store the cancel handle so it is cleaned up if the entry unloads
            # before the timer fires.
            self.async_on_remove(async_call_later(self.hass, 3, _push_on_startup))
