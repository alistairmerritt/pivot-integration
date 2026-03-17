"""Shared base class for all Pivot entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, CONF_DEVICE_ID, CONF_FRIENDLY_NAME, CONF_ESPHOME_DEVICE_NAME, CONF_DEVICE_SUFFIX


class PivotEntity(RestoreEntity):
    """Base class for all Pivot entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        definition: dict,
        config_entry: ConfigEntry,
    ) -> None:
        self._definition = definition
        self._config_entry = config_entry

        self._attr_unique_id = definition["unique_id"]
        self._attr_name = definition["name"]
        self._attr_icon = definition.get("icon")
        if "entity_category" in definition:
            from homeassistant.const import EntityCategory
            self._attr_entity_category = EntityCategory(definition["entity_category"])
        # Pin the entity_id explicitly so it matches what the firmware expects
        # regardless of the device friendly name or entity display name.
        if "entity_id" in definition:
            self.entity_id = definition["entity_id"]

        device_id: str = config_entry.data[CONF_DEVICE_ID]
        friendly_name: str = config_entry.data[CONF_FRIENDLY_NAME]
        esphome_name: str = config_entry.data[CONF_ESPHOME_DEVICE_NAME]
        suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]

        # Name the device "pivot_{suffix}" so HA auto-generates entity IDs as
        # "{platform}.pivot_{suffix}_{entity_key}" — matching what the firmware expects.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=suffix,
            model="Home Assistant Voice Preview Edition",
            manufacturer="Pivot",
            configuration_url=f"http://{esphome_name}.local",
        )
