"""Binary sensor entities for Pivot (passive bank flags)."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEVICE_SUFFIX,
    NUM_BANKS,
    get_binary_sensor_definitions,
    get_text_definitions,
)
from .entity_base import PivotEntity
from .entity_mappings import bank_is_passive

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
    switch, input_boolean or open/close-only cover — i.e. entities where the knob
    has no meaningful value to control. Derived automatically from the
    corresponding text entity (and, for covers, the cover's own features).
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
        self._assigned_entity_id: str = ""
        self._unsub_assigned: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Track the sibling text entity that holds this bank's assigned
        # entity ID. Platforms are set up concurrently, so the text entity
        # may not exist yet — the tracker is registered by entity ID and
        # fires when the entity first appears, making this order-independent.
        self._set_assigned_entity(self.hass.states.get(self._text_entity_id))
        self._recompute()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._text_entity_id],
                self._handle_text_state_change,
            )
        )
        self.async_on_remove(self._unsub_assigned_entity)

    @callback
    def _handle_text_state_change(self, event) -> None:
        self._set_assigned_entity(event.data.get("new_state"))
        self._recompute()
        self.async_write_ha_state()

    @callback
    def _set_assigned_entity(self, text_state) -> None:
        entity_id = text_state.state.strip() if text_state and text_state.state else ""
        if entity_id == self._assigned_entity_id:
            return
        self._unsub_assigned_entity()
        self._assigned_entity_id = entity_id
        # Only covers depend on the entity's own state (its features). Watch
        # them so the flag is right once the cover's state first appears —
        # it may load after Pivot — or if its features change.
        if entity_id.startswith("cover."):
            self._unsub_assigned = async_track_state_change_event(
                self.hass, [entity_id], self._handle_assigned_state_change
            )

    @callback
    def _unsub_assigned_entity(self) -> None:
        if self._unsub_assigned is not None:
            self._unsub_assigned()
            self._unsub_assigned = None

    @callback
    def _handle_assigned_state_change(self, event) -> None:
        # Write only when the flag flips: the firmware redraws the ring on
        # every passive update, and a moving door changes state repeatedly.
        was_on = self._attr_is_on
        self._recompute()
        if self._attr_is_on != was_on:
            self.async_write_ha_state()

    def _recompute(self) -> None:
        self._attr_is_on = bool(self._assigned_entity_id) and bank_is_passive(
            self.hass, self._assigned_entity_id
        )

    @property
    def is_on(self) -> bool:
        return self._attr_is_on
