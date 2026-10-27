"""Timer services for the Pivot dashboard cards.

`pivot.timer_toggle` and `pivot.timer_cancel` press the timer bank the way the
physical button does: they make the timer bank active and fire the same
`pivot_button_press` event (single or long press) that the Pivot - Timer
Control blueprint already handles. They replace the user-created
`script.pivot_timer_toggle`, which could only send a single press.
"""
from __future__ import annotations

import asyncio
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import CONF_DEVICE_SUFFIX, DOMAIN, NUM_BANKS

_LOGGER = logging.getLogger(__name__)

SERVICE_TIMER_TOGGLE = "timer_toggle"
SERVICE_TIMER_CANCEL = "timer_cancel"
ATTR_DEVICE = "device"
ATTR_BANK = "bank"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE): cv.string,
        vol.Optional(ATTR_BANK): vol.All(vol.Coerce(int), vol.Range(min=1, max=NUM_BANKS)),
    }
)

# How long timer_cancel waits for the blueprint to reset the timer before
# doing it directly. Timer Control blueprints imported before Pivot 0.0.93
# never handle a dashboard cancel: their long-press condition reads
# trigger.to_state, which an event trigger does not have, so it errors.
CANCEL_FALLBACK_SECS = 2.0


def _resolve(hass: HomeAssistant, call: ServiceCall) -> tuple[str, int]:
    """Return (suffix, timer bank) for a service call, or raise."""
    suffix: str = call.data[ATTR_DEVICE]
    loaded = {
        entry.data.get(CONF_DEVICE_SUFFIX)
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    }
    if suffix not in loaded:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_device",
            translation_placeholders={"device": suffix},
        )
    bank: int | None = call.data.get(ATTR_BANK)
    if bank is None:
        for n in range(1, NUM_BANKS + 1):
            text_state = hass.states.get(f"text.{suffix}_bank_{n}_entity")
            if text_state is not None and text_state.state.strip().lower() == "timer":
                bank = n
                break
    if bank is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_timer_bank",
            translation_placeholders={"device": suffix},
        )
    return suffix, bank


async def _press(
    hass: HomeAssistant, suffix: str, bank: int, press_type: str, context: Context
) -> None:
    """Make the timer bank active, then fire the press (as pivot_timer_toggle.yaml did)."""
    active_eid = f"number.{suffix}_active_bank"
    active = hass.states.get(active_eid)
    try:
        current = int(float(active.state)) if active is not None else None
    except ValueError:
        current = None
    if current != bank:
        await hass.services.async_call(
            "number", "set_value", {"entity_id": active_eid, "value": bank},
            blocking=True, context=context,
        )
    hass.bus.async_fire(
        "pivot_button_press",
        {
            "suffix": suffix,
            "bank": bank,
            "press_type": press_type,
            "bank_entity": "timer",
            "control_mode": True,
        },
        context=context,
    )


async def _cancel_fallback(
    hass: HomeAssistant, suffix: str, bank: int, context: Context
) -> None:
    """Reset the timer directly if the blueprint did not act on the long press.

    Mirrors the blueprint's cancel branch, minus the spoken "Timer cancelled".
    """
    state_eid = f"select.{suffix}_timer_state"
    deadline = asyncio.get_running_loop().time() + CANCEL_FALLBACK_SECS
    while asyncio.get_running_loop().time() < deadline:
        current = hass.states.get(state_eid)
        if current is None or current.state not in ("running", "paused"):
            return
        await asyncio.sleep(0.1)
    current = hass.states.get(state_eid)
    if current is None or current.state not in ("running", "paused"):
        return

    _LOGGER.info(
        "Pivot: the Timer Control blueprint did not cancel the %s timer; resetting it "
        "directly. Re-import the blueprint to get the spoken confirmation back",
        suffix,
    )

    async def _call(domain: str, service: str, data: dict) -> None:
        if hass.states.get(data["entity_id"]) is None:
            return
        await hass.services.async_call(domain, service, data, blocking=True, context=context)

    await _call("text", "set_value", {"entity_id": f"text.{suffix}_timer_end", "value": ""})
    await _call("select", "select_option", {"entity_id": state_eid, "option": "idle"})
    await _call("number", "set_value", {"entity_id": f"number.{suffix}_bank_{bank}_value", "value": 0})
    await _call("switch", "turn_on", {"entity_id": f"switch.{suffix}_dim_when_idle"})
    restore_eid = f"text.{suffix}_timer_restore_show_value"
    restore = hass.states.get(restore_eid)
    if restore is not None and restore.state == "off":
        await _call("switch", "turn_off", {"entity_id": f"switch.{suffix}_show_control_value"})
    await _call("text", "set_value", {"entity_id": restore_eid, "value": ""})


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the timer services (once per Home Assistant run)."""
    if hass.services.has_service(DOMAIN, SERVICE_TIMER_TOGGLE):
        return

    async def _timer_toggle(call: ServiceCall) -> None:
        suffix, bank = _resolve(hass, call)
        await _press(hass, suffix, bank, "single_press", call.context)

    async def _timer_cancel(call: ServiceCall) -> None:
        suffix, bank = _resolve(hass, call)
        state = hass.states.get(f"select.{suffix}_timer_state")
        if state is None or state.state not in ("running", "paused"):
            return
        await _press(hass, suffix, bank, "long_press", call.context)
        hass.async_create_task(
            _cancel_fallback(hass, suffix, bank, call.context),
            name="pivot_timer_cancel_fallback",
        )

    hass.services.async_register(DOMAIN, SERVICE_TIMER_TOGGLE, _timer_toggle, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TIMER_CANCEL, _timer_cancel, schema=SERVICE_SCHEMA)
