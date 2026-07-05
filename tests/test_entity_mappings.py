"""Tests for the 0-100 value mapping layer and sync-context tracking."""
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.pivot.entity_mappings import (
    SyncContextTracker,
    apply_value_to_entity,
    sync_value_from_entity,
)


async def test_apply_light_brightness(hass):
    calls = async_mock_service(hass, "light", "turn_on")
    await apply_value_to_entity(hass, "light", "light.kitchen", 55.0)
    assert len(calls) == 1
    assert calls[0].data == {"entity_id": "light.kitchen", "brightness_pct": 55}


async def test_apply_clamps_out_of_range(hass):
    calls = async_mock_service(hass, "light", "turn_on")
    await apply_value_to_entity(hass, "light", "light.kitchen", 150.0)
    assert calls[0].data["brightness_pct"] == 100


async def test_apply_rejects_nan_and_inf(hass):
    calls = async_mock_service(hass, "light", "turn_on")
    await apply_value_to_entity(hass, "light", "light.kitchen", float("nan"))
    await apply_value_to_entity(hass, "light", "light.kitchen", float("inf"))
    assert not calls


async def test_apply_climate_scales_and_snaps_to_step(hass):
    hass.states.async_set(
        "climate.hvac", "heat",
        {"min_temp": 16, "max_temp": 30, "target_temp_step": 0.5},
    )
    calls = async_mock_service(hass, "climate", "set_temperature")
    await apply_value_to_entity(hass, "climate", "climate.hvac", 50.0)
    assert calls[0].data["temperature"] == 23.0


async def test_apply_number_scales_and_snaps_to_step(hass):
    hass.states.async_set("number.pos", "0", {"min": 0, "max": 200, "step": 5})
    calls = async_mock_service(hass, "number", "set_value")
    await apply_value_to_entity(hass, "number", "number.pos", 33.0)
    # 33% of 0-200 = 66, snapped to step 5 -> 65
    assert calls[0].data["value"] == 65


async def test_sync_light_brightness(hass):
    tracker = SyncContextTracker()
    hass.states.async_set("light.a", "on", {"brightness": 128})
    calls = async_mock_service(hass, "number", "set_value")
    await sync_value_from_entity(hass, "light", "light.a", "number.gauge", tracker)
    assert calls[0].data["value"] == 50
    # The write carries a tracked context for loop prevention
    assert tracker.is_sync_context(calls[0].context)


async def test_sync_light_off_is_zero(hass):
    tracker = SyncContextTracker()
    hass.states.async_set("light.a", "off")
    calls = async_mock_service(hass, "number", "set_value")
    await sync_value_from_entity(hass, "light", "light.a", "number.gauge", tracker)
    assert calls[0].data["value"] == 0


async def test_sync_non_dimmable_light_reports_full(hass):
    tracker = SyncContextTracker()
    hass.states.async_set("light.a", "on", {})
    calls = async_mock_service(hass, "number", "set_value")
    await sync_value_from_entity(hass, "light", "light.a", "number.gauge", tracker)
    assert calls[0].data["value"] == 100


async def test_sync_climate_without_range_is_skipped(hass):
    """No hardcoded Celsius fallback — skip sync when range is unknown."""
    tracker = SyncContextTracker()
    hass.states.async_set(
        "climate.hvac", "heat",
        {"temperature": 21, "min_temp": "bad", "max_temp": "bad"},
    )
    calls = async_mock_service(hass, "number", "set_value")
    await sync_value_from_entity(hass, "climate", "climate.hvac", "number.gauge", tracker)
    assert not calls


def test_sync_context_tracker_is_bounded():
    tracker = SyncContextTracker(max_ids=64)
    first = tracker.new_context()
    assert tracker.is_sync_context(first)
    for _ in range(64):
        latest = tracker.new_context()
    # Oldest evicted, newest still tracked, foreign contexts never match
    assert not tracker.is_sync_context(first)
    assert tracker.is_sync_context(latest)
    assert not tracker.is_sync_context(None)
