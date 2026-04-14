"""Text entities for Pivot (stores the HA entity ID each bank controls)."""
from __future__ import annotations

import logging
import re

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_SUFFIX, get_text_definitions, get_color_text_definitions, get_timer_text_definitions, get_configured_color_text_definitions, get_config_text_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)

# Valid Home Assistant entity ID: domain.object_id (both lowercase, digits, underscores).
# "timer" is also allowed — it is a reserved value used to designate a bank as a timer bank.
_ENTITY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_]*$")
_ALLOWED_SPECIAL_VALUES = {"timer"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    async_add_entities([
        PivotText(defn, config_entry)
        for defn in (
            get_text_definitions(suffix)
            + get_color_text_definitions(suffix)
            + get_timer_text_definitions(suffix)
            + get_configured_color_text_definitions(suffix)
            + get_config_text_definitions(suffix)
        )
    ])


class PivotText(PivotEntity, TextEntity):
    """A text entity storing the HA entity ID a bank controls."""

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._attr_native_value: str = definition["initial"]
        self._attr_native_max = definition.get("max_length", 255)
        self._attr_pattern = definition.get("pattern")
        self._validate_entity_id: bool = definition.get("validate_entity_id", False)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "", "unavailable", "unknown"):
            self._attr_native_value = last.state
        # Always write state so entity is available immediately on startup
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        return self._attr_native_value

    async def async_set_value(self, value: str) -> None:
        if self._validate_entity_id and value != "" and value not in _ALLOWED_SPECIAL_VALUES:
            if not _ENTITY_ID_RE.match(value):
                _LOGGER.warning(
                    "Pivot: rejected invalid entity ID %r for %s — "
                    "must be in the form 'domain.object_id'",
                    value,
                    self.entity_id,
                )
                return
        self._attr_native_value = value
        self.async_write_ha_state()
