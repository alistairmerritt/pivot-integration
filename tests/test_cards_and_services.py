"""Tests for the dashboard-card delivery and the timer services."""
from unittest.mock import patch

import pytest
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pivot import cards, services
from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX


class _UrlSet:
    """Stand-in for the frontend's UrlManager (the real one needs hass_frontend)."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    def add(self, url: str) -> None:
        self.urls.append(url)


async def test_cards_registered_and_served(hass, hass_client):
    """The bundle is served from the integration and added as an extra module."""
    assert await async_setup_component(hass, "http", {})
    url_set = _UrlSet()
    hass.data[DATA_EXTRA_MODULE_URL] = url_set

    await cards.async_register_frontend(hass)
    await cards.async_register_frontend(hass)  # second call is a no-op

    assert len(url_set.urls) == 1
    url = url_set.urls[0]
    assert url.startswith(f"{cards.CARDS_URL}?v=")
    client = await hass_client()
    resp = await client.get(cards.CARDS_URL)
    assert resp.status == 200
    body = await resp.text()
    assert "pivot-device-card" in body


async def test_cards_skipped_without_frontend(hass, setup_pivot):
    """Without the frontend (as in these tests) Pivot still sets up normally."""
    assert DATA_EXTRA_MODULE_URL not in hass.data
    assert hass.services.has_service(DOMAIN, services.SERVICE_TIMER_TOGGLE)
    assert hass.services.has_service(DOMAIN, services.SERVICE_TIMER_CANCEL)


@pytest.fixture
async def pivot_with_timer(hass):
    """A Pivot entry with the (normally disabled) timer entities enabled and bank 4 = timer."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    reg = er.async_get(hass)
    for platform, key in (
        ("select", "timer_state"),
        ("number", "timer_duration"),
        ("text", "timer_end"),
        ("text", "timer_restore_show_value"),
    ):
        reg.async_get_or_create(
            platform, DOMAIN, f"pivot_{SUFFIX}_{key}",
            config_entry=entry, suggested_object_id=f"{SUFFIX}_{key}",
        )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call(
        "text", "set_value", {"entity_id": f"text.{SUFFIX}_bank_4_entity", "value": "timer"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"select.{SUFFIX}_timer_state") is not None
    return entry


def _capture_presses(hass):
    events = []
    hass.bus.async_listen("pivot_button_press", lambda e: events.append(e))
    return events


async def test_timer_toggle_activates_bank_and_presses(hass, pivot_with_timer):
    events = _capture_presses(hass)
    await hass.services.async_call(DOMAIN, "timer_toggle", {"device": SUFFIX}, blocking=True)
    await hass.async_block_till_done()

    assert float(hass.states.get(f"number.{SUFFIX}_active_bank").state) == 4
    assert len(events) == 1
    assert events[0].data == {
        "suffix": SUFFIX, "bank": 4, "press_type": "single_press",
        "bank_entity": "timer", "control_mode": True,
    }


async def test_timer_toggle_explicit_bank(hass, pivot_with_timer):
    events = _capture_presses(hass)
    await hass.services.async_call(DOMAIN, "timer_toggle", {"device": SUFFIX, "bank": 2}, blocking=True)
    await hass.async_block_till_done()
    assert float(hass.states.get(f"number.{SUFFIX}_active_bank").state) == 2
    assert events[0].data["bank"] == 2


async def test_timer_toggle_rejects_unknown_device(hass, pivot_with_timer):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "timer_toggle", {"device": "nope"}, blocking=True)


async def test_timer_toggle_rejects_device_without_timer_bank(hass, setup_pivot):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "timer_toggle", {"device": SUFFIX}, blocking=True)


async def test_timer_cancel_does_nothing_when_idle(hass, pivot_with_timer):
    events = _capture_presses(hass)
    await hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
    await hass.async_block_till_done()
    assert events == []


async def _start_fake_timer(hass, restore_show_value: str) -> None:
    async def call(domain, service, data):
        await hass.services.async_call(domain, service, data, blocking=True)

    await call("text", "set_value", {"entity_id": f"text.{SUFFIX}_timer_end", "value": "2030-01-01T00:00:00+00:00"})
    await call("select", "select_option", {"entity_id": f"select.{SUFFIX}_timer_state", "option": "running"})
    await call("switch", "turn_on", {"entity_id": f"switch.{SUFFIX}_show_control_value"})
    await call("switch", "turn_off", {"entity_id": f"switch.{SUFFIX}_dim_when_idle"})
    await call("text", "set_value", {"entity_id": f"text.{SUFFIX}_timer_restore_show_value", "value": restore_show_value})
    await hass.async_block_till_done()


async def test_timer_cancel_presses_long_and_falls_back(hass, pivot_with_timer):
    """No blueprint answers the long press here, so the service resets the timer itself."""
    await _start_fake_timer(hass, restore_show_value="off")
    events = _capture_presses(hass)

    with patch.object(services, "CANCEL_FALLBACK_SECS", 0.2):
        await hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
        await hass.async_block_till_done()

    assert [e.data["press_type"] for e in events] == ["long_press"]
    assert float(hass.states.get(f"number.{SUFFIX}_active_bank").state) == 4
    assert hass.states.get(f"select.{SUFFIX}_timer_state").state == "idle"
    assert hass.states.get(f"text.{SUFFIX}_timer_end").state == ""
    assert hass.states.get(f"switch.{SUFFIX}_dim_when_idle").state == "on"
    assert hass.states.get(f"switch.{SUFFIX}_show_control_value").state == "off"
    assert hass.states.get(f"text.{SUFFIX}_timer_restore_show_value").state == ""


async def test_timer_cancel_fallback_puts_dim_back(hass, pivot_with_timer):
    """Dim LEDs When Idle goes back to the value saved at the start, not always on."""
    await _start_fake_timer(hass, restore_show_value="off")
    await hass.services.async_call(
        "text", "set_value", {"entity_id": f"text.{SUFFIX}_timer_restore_dim", "value": "off"}, blocking=True,
    )

    with patch.object(services, "CANCEL_FALLBACK_SECS", 0.2):
        await hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
        await hass.async_block_till_done()

    assert hass.states.get(f"select.{SUFFIX}_timer_state").state == "idle"
    assert hass.states.get(f"switch.{SUFFIX}_dim_when_idle").state == "off"
    assert hass.states.get(f"text.{SUFFIX}_timer_restore_dim").state == ""


async def test_timer_cancel_leaves_blueprint_result_alone(hass, pivot_with_timer):
    """When the blueprint resets the timer itself, the fallback does nothing more."""
    await _start_fake_timer(hass, restore_show_value="on")

    async def _blueprint_stand_in(event):
        if event.data["press_type"] == "long_press":
            await hass.services.async_call(
                "select", "select_option",
                {"entity_id": f"select.{SUFFIX}_timer_state", "option": "idle"}, blocking=True,
            )

    hass.bus.async_listen("pivot_button_press", _blueprint_stand_in)
    with patch.object(services, "CANCEL_FALLBACK_SECS", 0.2):
        await hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
        await hass.async_block_till_done()

    assert hass.states.get(f"select.{SUFFIX}_timer_state").state == "idle"
    # The fallback never ran, so the fields only it would clear are untouched.
    assert hass.states.get(f"text.{SUFFIX}_timer_end").state != ""
    assert hass.states.get(f"switch.{SUFFIX}_show_control_value").state == "on"
