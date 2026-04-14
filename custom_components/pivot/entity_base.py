"""Shared base class for all Pivot entities."""
from __future__ import annotations

import urllib.parse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, CONF_DEVICE_ID, CONF_ESPHOME_DEVICE_NAME, CONF_DEVICE_SUFFIX


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
            self._attr_entity_category = EntityCategory(definition["entity_category"])
        if not definition.get("entity_registry_enabled_default", True):
            self._attr_entity_registry_enabled_default = False
        # Pin the entity_id explicitly so it matches what the firmware expects
        # regardless of the device friendly name or entity display name.
        if "entity_id" in definition:
            self.entity_id = definition["entity_id"]

        device_id: str = config_entry.data[CONF_DEVICE_ID]
        esphome_name: str = config_entry.data[CONF_ESPHOME_DEVICE_NAME]
        suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]

        # Sanitise esphome_name before embedding in a URL.
        # ESPHome device names are hostnames (alphanumeric + hyphens) so
        # percent-encoding is a no-op in practice, but guards against any
        # unexpected value from the ESPHome config entry data.
        safe_host = urllib.parse.quote(esphome_name, safe="-.")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=suffix,
            model="Home Assistant Voice Preview Edition",
            manufacturer="Pivot",
            configuration_url=f"http://{safe_host}.local",
        )
