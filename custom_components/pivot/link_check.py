"""Raise a Repairs issue when Pivot cannot hear the device's button.

A Pivot entry takes button presses from one specific ESPHome device, chosen at
setup. If the VPE is later added to Home Assistant again — re-adopted in
ESPHome, reset, or first added by IP address — it becomes a new device, and
the entry keeps watching the old one. Presses then do nothing, with no error
anywhere, while the knob keeps working: the firmware reaches Pivot's entities
by suffix, not through the device link.

The issue is raised when:

- at setup, the linked device or its button entity no longer exists; or
- the firmware has just shown it is online — a knob turn or bank switch it
  sent — while the button Pivot watches has been unavailable for over a minute.

An offline or unplugged VPE sends nothing, so it never trips the second test.
The issue clears when the button becomes available again, when the entry is
reconfigured or reloaded with a working link, or when the entry is removed.
"""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .button import get_button_event_entity
from .const import CONF_DEVICE_ID, CONF_DEVICE_SUFFIX, DOMAIN, NUM_BANKS
from .entity_mappings import SyncContextTracker, bank_is_passive

# A button entity is briefly unavailable while its device reconnects. Only
# treat it as unreachable once it has been unavailable for longer than this.
UNAVAILABLE_GRACE = timedelta(seconds=60)

HELP_URL = "https://alistairmerritt.github.io/pivot/help/#the-button-press-does-nothing"


def link_issue_id(entry: ConfigEntry) -> str:
    """Return the Repairs issue ID for this entry."""
    return f"button_unreachable_{entry.entry_id}"


def setup_link_check(
    hass: HomeAssistant, entry: ConfigEntry, sync_contexts: SyncContextTracker
) -> list[CALLBACK_TYPE]:
    """Watch for a Pivot entry linked to a device it cannot hear.

    Returns a list of unsubscribe callbacks.
    """
    device_id = entry.data.get(CONF_DEVICE_ID)
    if not device_id:
        # Entries from before the device link was stored are matched by name
        # in button.py; there is no link here to check.
        return []

    suffix = entry.data[CONF_DEVICE_SUFFIX]
    issue_id = link_issue_id(entry)
    button_entity_id = get_button_event_entity(hass, device_id)

    @callback
    def _raise() -> None:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            learn_more_url=HELP_URL,
            severity=ir.IssueSeverity.WARNING,
            translation_key="button_unreachable",
            translation_placeholders={"name": entry.title},
        )

    @callback
    def _clear() -> None:
        ir.async_delete_issue(hass, DOMAIN, issue_id)

    if button_entity_id is None:
        # The linked device, or its button entity, no longer exists. Registry
        # entries are loaded before any integration sets up, so this is not a
        # startup race: nothing will ever be heard until the entry is re-linked.
        _raise()
        return []

    button_state = hass.states.get(button_entity_id)
    if button_state is not None and button_state.state != STATE_UNAVAILABLE:
        _clear()

    @callback
    def _button_unreachable() -> bool:
        state = hass.states.get(button_entity_id)
        if state is None:
            # Removed or disabled since setup: presses cannot arrive.
            return True
        if state.state != STATE_UNAVAILABLE:
            return False
        return dt_util.utcnow() - state.last_changed > UNAVAILABLE_GRACE

    @callback
    def _on_button_changed(event: Event) -> None:
        new_state = event.data.get("new_state")
        if new_state is not None and new_state.state != STATE_UNAVAILABLE:
            _clear()

    active_bank_id = f"number.{suffix}_active_bank"
    bank_value_ids = {
        f"number.{suffix}_bank_{bank + 1}_value": bank for bank in range(NUM_BANKS)
    }

    @callback
    def _on_pivot_number_changed(event: Event) -> None:
        """Treat a firmware-sent knob turn or bank switch as proof of life."""
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if old_state is None or new_state is None or old_state.state == new_state.state:
            return
        if STATE_UNAVAILABLE in (old_state.state, new_state.state) or STATE_UNKNOWN in (
            old_state.state, new_state.state
        ):
            return
        context = new_state.context
        # The firmware's writes arrive through Home Assistant's ESPHome
        # integration with a bare context. A person's write carries a user,
        # an automation's or script's a parent, and Pivot's sync writes a
        # tracked context.
        if context.user_id is not None or context.parent_id is not None:
            return
        if sync_contexts.is_sync_context(context):
            return
        bank = bank_value_ids.get(event.data.get("entity_id", ""))
        if bank is not None:
            # Pivot also holds scene and script banks at zero with a bare
            # context. The firmware ignores the knob on every passive bank, so
            # a passive bank's value never proves anything.
            text_state = hass.states.get(f"text.{suffix}_bank_{bank + 1}_entity")
            if text_state is None or bank_is_passive(hass, text_state.state):
                return
        if _button_unreachable():
            _raise()

    return [
        async_track_state_change_event(hass, [button_entity_id], _on_button_changed),
        async_track_state_change_event(
            hass, [active_bank_id, *bank_value_ids], _on_pivot_number_changed
        ),
    ]
