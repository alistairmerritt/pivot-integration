"""Tests for the on/off status ring on passive banks.

Stateful passive banks (switch, input_boolean, open/close-only cover) mirror
their entity's state into the bank value — 100 on/open, 0 off/closed — so the
firmware can show a full ring. Stateless passive banks (scene, script) stay at
0, and the knob does nothing for any passive bank.
"""
from datetime import timedelta

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, State
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
    mock_restore_cache,
)

from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX

# supported_features: OPEN=1, CLOSE=2, SET_POSITION=4, STOP=8
GARAGE = {"supported_features": 3}
BLIND = {"supported_features": 15, "current_position": 40}

COVER_COMMANDS = ("set_cover_position", "open_cover", "close_cover", "toggle", "stop_cover")


async def _assign_bank(hass, bank: int, entity_id: str) -> None:
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_{bank}_entity", "value": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()


async def _set_active_bank(hass, bank: int) -> None:
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_active_bank", "value": bank},
        blocking=True,
    )
    await hass.async_block_till_done()


async def _control_mode_on(hass) -> None:
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": f"switch.{SUFFIX}_control_mode"}, blocking=True,
    )


async def _turn_knob(hass, bank: int, value: float) -> None:
    """A knob write as the firmware makes it: plain number.set_value."""
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": f"number.{SUFFIX}_bank_{bank}_value", "value": value},
        blocking=True,
    )
    await hass.async_block_till_done()


def _value(hass, bank: int) -> float:
    return float(hass.states.get(f"number.{SUFFIX}_bank_{bank}_value").state)


def _passive(hass, bank: int) -> str:
    return hass.states.get(f"binary_sensor.{SUFFIX}_bank_{bank}_passive").state


# --- Switches ---------------------------------------------------------------

async def test_switch_bank_value_mirrors_state(hass, setup_pivot):
    hass.states.async_set("switch.desk", "on")
    await _assign_bank(hass, 1, "switch.desk")
    assert _passive(hass, 1) == "on"
    assert _value(hass, 1) == 100

    hass.states.async_set("switch.desk", "off")
    await hass.async_block_till_done()
    assert _value(hass, 1) == 0

    hass.states.async_set("switch.desk", "on")
    await hass.async_block_till_done()
    assert _value(hass, 1) == 100


async def test_input_boolean_bank_value_mirrors_state(hass, setup_pivot):
    hass.states.async_set("input_boolean.guest", "off")
    await _assign_bank(hass, 1, "input_boolean.guest")
    assert _value(hass, 1) == 0
    hass.states.async_set("input_boolean.guest", "on")
    await hass.async_block_till_done()
    assert _value(hass, 1) == 100


async def test_switch_unavailable_leaves_value_alone(hass, setup_pivot):
    hass.states.async_set("switch.desk", "on")
    await _assign_bank(hass, 1, "switch.desk")
    for state in ("unavailable", "unknown"):
        hass.states.async_set("switch.desk", state)
        await hass.async_block_till_done()
        assert _value(hass, 1) == 100


async def test_switch_bank_value_set_even_when_bank_not_active(hass, setup_pivot):
    """A leftover value from the previous entity must never reach the ring."""
    hass.states.async_set("light.lamp", "on", {"brightness": 153})
    await _assign_bank(hass, 3, "light.lamp")
    await _turn_knob(hass, 3, 60)  # bank 3 not active: just a stored value
    assert _value(hass, 3) == 60

    hass.states.async_set("switch.desk", "off")
    await _assign_bank(hass, 3, "switch.desk")
    assert _value(hass, 3) == 0


async def test_bank_switch_to_switch_bank_shows_state(hass, setup_pivot):
    hass.states.async_set("switch.desk", "on")
    await _assign_bank(hass, 2, "switch.desk")
    await _set_active_bank(hass, 2)
    assert _value(hass, 2) == 100


async def test_knob_does_nothing_on_switch_bank(hass, setup_pivot):
    hass.states.async_set("switch.desk", "on")
    await _assign_bank(hass, 1, "switch.desk")
    await _control_mode_on(hass)
    calls = [async_mock_service(hass, "switch", s) for s in ("turn_on", "turn_off", "toggle")]
    knob_events = async_capture_events(hass, "pivot_knob_turn")
    await _turn_knob(hass, 1, 30)
    assert all(not c for c in calls)
    assert not knob_events


# --- Stateless passive: unchanged ------------------------------------------

async def test_scene_and_script_banks_stay_at_zero(hass, setup_pivot):
    hass.states.async_set("light.lamp", "on", {"brightness": 153})
    await _assign_bank(hass, 1, "light.lamp")
    await _assign_bank(hass, 3, "light.lamp")
    await _turn_knob(hass, 1, 60)
    await _turn_knob(hass, 3, 60)

    hass.states.async_set("script.bedtime", "off")
    await _assign_bank(hass, 1, "scene.movie")      # active bank
    await _assign_bank(hass, 3, "script.bedtime")   # non-active bank
    assert _value(hass, 1) == 0
    assert _value(hass, 3) == 0

    # A running script ("on") must not light the ring.
    hass.states.async_set("script.bedtime", "on")
    await hass.async_block_till_done()
    assert _value(hass, 3) == 0


# --- Open/close-only covers -------------------------------------------------

async def test_garage_door_bank_is_passive_and_mirrors_state(hass, setup_pivot):
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await _assign_bank(hass, 1, "cover.garage")
    assert _passive(hass, 1) == "on"
    assert _value(hass, 1) == 0

    hass.states.async_set("cover.garage", "opening", GARAGE)
    await hass.async_block_till_done()
    assert _value(hass, 1) == 0  # moving: left alone
    hass.states.async_set("cover.garage", "open", GARAGE)
    await hass.async_block_till_done()
    assert _value(hass, 1) == 100


async def test_knob_does_nothing_on_garage_door_bank(hass, setup_pivot):
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await _assign_bank(hass, 1, "cover.garage")
    await _control_mode_on(hass)
    calls = [async_mock_service(hass, "cover", s) for s in COVER_COMMANDS]
    knob_events = async_capture_events(hass, "pivot_knob_turn")
    for value in (2, 50, 98):
        await _turn_knob(hass, 1, value)
    assert all(not c for c in calls)
    assert not knob_events


async def test_blind_bank_is_unchanged(hass, setup_pivot):
    hass.states.async_set("cover.blind", "open", BLIND)
    await _assign_bank(hass, 1, "cover.blind")
    await _control_mode_on(hass)
    assert _passive(hass, 1) == "off"
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await _turn_knob(hass, 1, 70)
    # Covers are debounced; let the pending command fire.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    assert calls[0].data == {"entity_id": "cover.blind", "position": 70}


async def test_garage_door_that_loads_late_becomes_passive(hass, setup_pivot):
    """The cover's state may appear after Pivot — the flag must follow."""
    await _assign_bank(hass, 1, "cover.garage")
    assert _passive(hass, 1) == "off"  # unknown yet: original behaviour
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await hass.async_block_till_done()
    assert _passive(hass, 1) == "on"


async def test_garage_door_stays_passive_while_unavailable(hass, setup_pivot):
    """HA keeps supported_features on unavailable entities; so must the flag."""
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await _assign_bank(hass, 1, "cover.garage")
    hass.states.async_set("cover.garage", "unavailable", GARAGE)
    await hass.async_block_till_done()
    assert _passive(hass, 1) == "on"


async def test_passive_flag_not_rewritten_as_door_moves(hass, setup_pivot):
    """The firmware redraws on every passive update — only write on a flip."""
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await _assign_bank(hass, 1, "cover.garage")
    writes = async_capture_events(hass, "state_changed")
    for state in ("opening", "open", "closing", "closed"):
        hass.states.async_set("cover.garage", state, GARAGE)
        await hass.async_block_till_done()
    passive_id = f"binary_sensor.{SUFFIX}_bank_1_passive"
    assert not [e for e in writes if e.data["entity_id"] == passive_id]


async def test_reassigning_away_from_a_cover_stops_watching_it(hass, setup_pivot):
    hass.states.async_set("cover.garage", "closed", GARAGE)
    await _assign_bank(hass, 1, "cover.garage")
    hass.states.async_set("scene.movie", "scening")
    await _assign_bank(hass, 1, "scene.movie")
    writes = async_capture_events(hass, "state_changed")
    hass.states.async_set("cover.garage", "open", GARAGE)
    await hass.async_block_till_done()
    passive_id = f"binary_sensor.{SUFFIX}_bank_1_passive"
    assert not [e for e in writes if e.data["entity_id"] == passive_id]
    assert _value(hass, 1) == 0


# --- Restart ----------------------------------------------------------------

async def test_restart_sets_passive_bank_values(hass):
    """After a restart: switches and garage doors show their state, scenes 0."""
    mock_restore_cache(hass, (
        State(f"text.{SUFFIX}_bank_1_entity", "switch.desk"),
        State(f"text.{SUFFIX}_bank_2_entity", "cover.garage"),
        State(f"text.{SUFFIX}_bank_3_entity", "scene.movie"),
    ))
    hass.states.async_set("switch.desk", "on")
    hass.states.async_set("cover.garage", "open", GARAGE)

    hass.set_state(CoreState.starting)
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert _value(hass, 1) == 100
    assert _value(hass, 2) == 100
    assert _value(hass, 3) == 0
    assert _passive(hass, 2) == "on"


async def test_restart_with_entities_loading_after_pivot(hass):
    """Entities that appear after Pivot are picked up when they load."""
    mock_restore_cache(hass, (
        State(f"text.{SUFFIX}_bank_1_entity", "switch.desk"),
        State(f"text.{SUFFIX}_bank_2_entity", "cover.garage"),
    ))
    hass.set_state(CoreState.starting)
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("switch.desk", "on")
    hass.states.async_set("cover.garage", "open", GARAGE)
    await hass.async_block_till_done()

    assert _value(hass, 1) == 100
    assert _value(hass, 2) == 100
    assert _passive(hass, 2) == "on"
