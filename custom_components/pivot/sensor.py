"""Sensor platform for Pivot — publishes assigned light RGB as R,G,B string per bank."""
from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    entity_id as make_entity_id,
    get_light_rgb_sensor_definitions,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    defs = get_light_rgb_sensor_definitions(suffix)
    entities = [PivotLightRGBSensor(hass, entry, d) for d in defs]
    async_add_entities(entities, update_before_add=True)


class PivotLightRGBSensor(SensorEntity):
    """Publishes the assigned bank's light RGB as 'R,G,B' string.

    Updates whenever the assigned light's state or colour changes.
    Returns '' when the light is off, not an RGB light, or no entity assigned.
    """

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, definition: dict) -> None:
        self._hass = hass
        self._entry = entry
        self._bank = definition["bank"]
        suffix = entry.data[CONF_DEVICE_SUFFIX]
        self._attr_unique_id = definition["unique_id"]
        self._attr_name = definition["name"]
        self._attr_icon = definition["icon"]
        self._attr_entity_category = definition.get("entity_category")
        self._entity_id_str = definition["entity_id"]
        self._bank_text_entity_id = make_entity_id("text", suffix, f"bank_{self._bank}_entity")
        self._unsub_light = None
        self._unsub_bank = None
        self._attr_native_value = ""

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data[CONF_DEVICE_ID])},
            name=self._entry.data[CONF_DEVICE_SUFFIX],
            model="Home Assistant Voice Preview Edition",
            manufacturer="Pivot",
            configuration_url=f"http://{self._entry.data[CONF_ESPHOME_DEVICE_NAME]}.local",
        )

    @property
    def entity_id(self) -> str:
        return self._entity_id_str

    @entity_id.setter
    def entity_id(self, value: str) -> None:
        self._entity_id_str = value

    async def async_added_to_hass(self) -> None:
        self._unsub_bank = async_track_state_change_event(
            self._hass,
            [self._bank_text_entity_id],
            self._on_bank_entity_change,
        )
        self._register_light_listener()
        self._update_value()
        self.async_write_ha_state()
        _LOGGER.debug(
            "Pivot RGB sensor bank %d: initial value=%r assigned=%r",
            self._bank, self._attr_native_value, self._get_assigned_light()
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_light:
            self._unsub_light()
            self._unsub_light = None
        if self._unsub_bank:
            self._unsub_bank()
            self._unsub_bank = None

    def _get_assigned_light(self) -> str | None:
        state = self._hass.states.get(self._bank_text_entity_id)
        if state and state.state not in ("", "unknown", "unavailable"):
            entity = state.state
            if entity.startswith("light."):
                return entity
        return None

    def _register_light_listener(self) -> None:
        if self._unsub_light:
            self._unsub_light()
            self._unsub_light = None
        light = self._get_assigned_light()
        if light:
            self._unsub_light = async_track_state_change_event(
                self._hass,
                [light],
                self._on_light_state_change,
            )
            _LOGGER.debug("Pivot RGB sensor bank %d: tracking %s", self._bank, light)

    @callback
    def _on_bank_entity_change(self, event) -> None:
        self._register_light_listener()
        self._update_value()
        self.async_write_ha_state()

    @callback
    def _on_light_state_change(self, event) -> None:
        self._update_value()
        self.async_write_ha_state()

    def _update_value(self) -> None:
        light = self._get_assigned_light()
        if not light:
            self._attr_native_value = ""
            return
        state = self._hass.states.get(light)
        if not state or state.state != "on":
            self._attr_native_value = ""
            return
        rgb = state.attributes.get("rgb_color")
        if not rgb or len(rgb) != 3:
            self._attr_native_value = ""
            return
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        self._attr_native_value = f"{r},{g},{b}"

    def update(self) -> None:
        self._update_value()
