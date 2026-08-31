"""Shared base class for all Pivot entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_SUFFIX, DOMAIN


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
        # Pin entity_id explicitly — auto-generated IDs use the friendly name, not the ESPHome slug.
        if "entity_id" in definition:
            self.entity_id = definition["entity_id"]

        device_id: str = config_entry.data[CONF_DEVICE_ID]
        suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]

        # No configuration_url: the Pivot firmware ships no web_server
        # component, so http://<device>.local would be a dead link.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=suffix,
            model="Home Assistant Voice Preview Edition",
            manufacturer="Pivot",
        )
