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


# --- Covers -----------------------------------------------------------------
# supported_features: OPEN=1, CLOSE=2, SET_POSITION=4, STOP=8

BLIND = {"supported_features": 15, "current_position": 40}
# Meross-style garage opener: open/close only, no position at all.
GARAGE = {"supported_features": 3}
# Shutter-style garage door: reports 0/100 but cannot be sent a position.
GARAGE_WITH_POSITION = {"supported_features": 11, "current_position": 0}

COVER_COMMANDS = ("set_cover_position", "open_cover", "close_cover", "toggle", "stop_cover")


def _mock_all_cover_commands(hass):
    return [async_mock_service(hass, "cover", svc) for svc in COVER_COMMANDS]


async def test_apply_positional_cover_sets_position(hass):
    hass.states.async_set("cover.blind", "open", BLIND)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await apply_value_to_entity(hass, "cover", "cover.blind", 55.0)
    assert calls[0].data == {"entity_id": "cover.blind", "position": 55}


async def test_apply_cover_without_features_attr_falls_back_to_position(hass):
    hass.states.async_set("cover.blind", "open", {"current_position": 20})
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await apply_value_to_entity(hass, "cover", "cover.blind", 30.0)
    assert calls[0].data["position"] == 30


async def test_knob_never_moves_an_open_close_only_cover(hass):
    """Garage doors are press-only: no knob value, in any state, sends a command."""
    mocks = _mock_all_cover_commands(hass)
    for attrs in (GARAGE, GARAGE_WITH_POSITION):
        for state in ("open", "opening", "closed", "closing", "unknown"):
            hass.states.async_set("cover.garage", state, attrs)
            for value in (0.0, 2.0, 49.0, 50.0, 98.0, 100.0):
                await apply_value_to_entity(hass, "cover", "cover.garage", value)
    assert all(not calls for calls in mocks)


async def test_cover_without_state_keeps_original_behaviour(hass):
    """No state means no feature info: don't guess, behave as before."""
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await apply_value_to_entity(hass, "cover", "cover.gone", 80.0)
    assert calls[0].data == {"entity_id": "cover.gone", "position": 80}


async def test_sync_cover_position(hass):
    tracker = SyncContextTracker()
    hass.states.async_set("cover.blind", "open", BLIND)
    calls = async_mock_service(hass, "number", "set_value")
    await sync_value_from_entity(hass, "cover", "cover.blind", "number.gauge", tracker)
    assert calls[0].data["value"] == 40


async def test_sync_positionless_cover_shows_full_or_empty_ring(hass):
    tracker = SyncContextTracker()
    calls = async_mock_service(hass, "number", "set_value")
    hass.states.async_set("cover.garage", "open", GARAGE)
    await sync_value_from_entity(hass, "cover", "cover.garage", "number.gauge", tracker)
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await sync_value_from_entity(hass, "cover", "cover.garage", "number.gauge", tracker)
    assert [c.data["value"] for c in calls] == [100, 0]
    # Tagged as sync writes, so they can never be mistaken for a knob turn.
    assert all(tracker.is_sync_context(c.context) for c in calls)


async def test_sync_positionless_cover_leaves_gauge_while_moving(hass):
    tracker = SyncContextTracker()
    calls = async_mock_service(hass, "number", "set_value")
    for state in ("opening", "closing", "unknown", "unavailable"):
        hass.states.async_set("cover.garage", state, GARAGE)
        await sync_value_from_entity(hass, "cover", "cover.garage", "number.gauge", tracker)
    assert not calls


async def test_sync_positional_cover_without_position_is_not_guessed(hass):
    """A blind reporting 'open' with no position must not read as 100."""
    tracker = SyncContextTracker()
    calls = async_mock_service(hass, "number", "set_value")
    hass.states.async_set("cover.blind", "open", {"supported_features": 15})
    await sync_value_from_entity(hass, "cover", "cover.blind", "number.gauge", tracker)
    assert not calls
