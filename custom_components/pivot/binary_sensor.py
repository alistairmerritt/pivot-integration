"""Binary sensor entities for Pivot (passive bank flags)."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_DEVICE_SUFFIX, NUM_BANKS, PASSIVE_DOMAINS, get_binary_sensor_definitions, get_text_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    text_defs = get_text_definitions(suffix)
    bs_defs = get_binary_sensor_definitions(suffix)

    entities = [
        PivotBankPassiveSensor(
            definition=bs_defs[bank],
            text_definition=text_defs[bank],
            bank=bank,
            config_entry=config_entry,
        )
        for bank in range(NUM_BANKS)
    ]
    async_add_entities(entities)


class PivotBankPassiveSensor(PivotEntity, BinarySensorEntity):
    """
    Binary sensor that is ON when the bank's assigned entity is a scene, script,
    switch, or input_boolean — i.e. entities where the knob has no meaningful value
    to control. Derived automatically from the corresponding text entity.
    The firmware reads this to decide whether to disable the knob for this bank.
    """

    def __init__(
        self,
        definition: dict,
        text_definition: dict,
        bank: int,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(definition, config_entry)
        self._bank = bank
        # Pinned entity ID of the sibling text entity — addressed by
        # convention like everywhere else, never via a registry lookup.
        self._text_entity_id = text_definition["entity_id"]
        self._attr_is_on: bool = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Track the sibling text entity that holds this bank's assigned
        # entity ID. Platforms are set up concurrently, so the text entity
        # may not exist yet — the tracker is registered by entity ID and
        # fires when the entity first appears, making this order-independent.
        self._update_from_text_state(self.hass.states.get(self._text_entity_id))
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._text_entity_id],
                self._handle_text_state_change,
            )
        )

    @callback
    def _handle_text_state_change(self, event) -> None:
        new_state = event.data.get("new_state")
        self._update_from_text_state(new_state)
        self.async_write_ha_state()

    def _update_from_text_state(self, state) -> None:
        if state is None or not state.state:
            self._attr_is_on = False
            return
        entity_id = state.state.strip()
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        self._attr_is_on = domain in PASSIVE_DOMAINS

    @property
    def is_on(self) -> bool:
        return self._attr_is_on
