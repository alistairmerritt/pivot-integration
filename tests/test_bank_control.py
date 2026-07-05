"""Tests for knob value application, bank switching, and loop prevention."""
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_mock_service,
)

from custom_components.pivot.entity_mappings import sync_value_from_entity

from .const import SUFFIX


async def _assign_bank(hass, bank: int, entity_id: str) -> None:
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_{bank}_entity", "value": entity_id},
        blocking=True,
    )


async def _control_mode(hass, on: bool) -> None:
    await hass.services.async_call(
        "switch", "turn_on" if on else "turn_off",
        {"entity_id": f"switch.{SUFFIX}_control_mode"},
        blocking=True,
    )


async def test_knob_turn_applies_to_light(hass, setup_pivot):
    hass.states.async_set("light.kitchen", "on", {"brightness": 100})
    await _assign_bank(hass, 1, "light.kitchen")
    await _control_mode(hass, True)
    calls = async_mock_service(hass, "light", "turn_on")
    events = async_capture_events(hass, "pivot_knob_turn")

    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_bank_1_value", "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": "light.kitchen", "brightness_pct": 40}
    assert len(events) == 1
    assert events[0].data["bank"] == 1
    assert events[0].data["value"] == 40


async def test_knob_ignored_when_control_mode_off(hass, setup_pivot):
    hass.states.async_set("light.kitchen", "on", {"brightness": 100})
    await _assign_bank(hass, 1, "light.kitchen")
    calls = async_mock_service(hass, "light", "turn_on")

    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_bank_1_value", "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert not calls


async def test_passive_bank_knob_does_nothing(hass, setup_pivot):
    await _assign_bank(hass, 1, "scene.movie")
    await _control_mode(hass, True)
    await hass.async_block_till_done()

    # Passive flag reflects the assignment
    assert hass.states.get(f"binary_sensor.{SUFFIX}_bank_1_passive").state == "on"

    calls = async_mock_service(hass, "scene", "turn_on")
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_bank_1_value", "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert not calls


async def test_bank_switch_syncs_gauge_from_entity(hass, setup_pivot):
    hass.states.async_set("light.lamp", "on", {"brightness": 255})
    await _assign_bank(hass, 2, "light.lamp")
    events = async_capture_events(hass, "pivot_bank_changed")

    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_active_bank", "value": 2},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert float(hass.states.get(f"number.{SUFFIX}_bank_2_value").state) == 100
    assert len(events) == 1
    assert events[0].data["bank_entity"] == "light.lamp"


async def test_sync_write_is_not_treated_as_knob_turn(hass, setup_pivot):
    """Loop prevention: a Pivot sync write must not re-apply to the entity
    or fire pivot_knob_turn."""
    entry = setup_pivot
    hass.states.async_set("light.kitchen", "on", {"brightness": 128})
    await _assign_bank(hass, 1, "light.kitchen")
    await _control_mode(hass, True)
    calls = async_mock_service(hass, "light", "turn_on")
    events = async_capture_events(hass, "pivot_knob_turn")

    await sync_value_from_entity(
        hass, "light", "light.kitchen",
        f"number.{SUFFIX}_bank_1_value",
        entry.runtime_data.sync_contexts,
    )
    await hass.async_block_till_done()

    # Gauge updated to the light's real value...
    assert float(hass.states.get(f"number.{SUFFIX}_bank_1_value").state) == 50
    # ...but nothing was applied back and no knob event fired
    assert not calls
    assert not events
