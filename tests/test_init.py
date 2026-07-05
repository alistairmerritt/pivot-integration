"""Tests for Pivot setup, teardown, and entity provisioning."""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX


async def test_setup_creates_pinned_entities(hass, setup_pivot):
    """All entities are created with the firmware-facing pinned entity IDs."""
    entry = setup_pivot
    assert entry.state is ConfigEntryState.LOADED

    expected = [
        f"number.{SUFFIX}_bank_1_value",
        f"number.{SUFFIX}_bank_4_value",
        f"number.{SUFFIX}_active_bank",
        f"switch.{SUFFIX}_control_mode",
        f"switch.{SUFFIX}_show_control_value",
        f"switch.{SUFFIX}_dim_when_idle",
        f"switch.{SUFFIX}_bank_1_mirror_light",
        f"switch.{SUFFIX}_bank_1_announce_value",
        f"text.{SUFFIX}_bank_1_entity",
        f"text.{SUFFIX}_bank_1_color",
        f"text.{SUFFIX}_bank_1_configured_color",
        f"text.{SUFFIX}_tts_entity",
        f"binary_sensor.{SUFFIX}_bank_1_passive",
        f"light.{SUFFIX}_bank_1_color_light",
    ]
    for entity_id in expected:
        assert hass.states.get(entity_id) is not None, f"missing {entity_id}"

    # Defaults
    assert float(hass.states.get(f"number.{SUFFIX}_active_bank").state) == 1
    assert hass.states.get(f"switch.{SUFFIX}_control_mode").state == "off"
    assert hass.states.get(f"text.{SUFFIX}_bank_1_color").state == "#2889FF"

    # Timer entities are disabled by default — no state until enabled
    assert hass.states.get(f"number.{SUFFIX}_timer_duration") is None
    assert hass.states.get(f"select.{SUFFIX}_timer_state") is None


async def test_unload(hass, setup_pivot):
    """Entry unloads cleanly."""
    entry = setup_pivot
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_initial_bank_assignments_seeded(hass):
    """Bank entities chosen in the initial config flow are applied to the
    text entities on first setup, then stripped from entry data so they can
    never overwrite later changes."""
    data = {**ENTRY_DATA, "bank_0_entity": "light.kitchen", "bank_1_entity": "timer"}
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(f"text.{SUFFIX}_bank_1_entity").state == "light.kitchen"
    assert hass.states.get(f"text.{SUFFIX}_bank_2_entity").state == "timer"
    assert hass.states.get(f"text.{SUFFIX}_bank_3_entity").state == ""

    # Seed keys are stripped after applying
    assert "bank_0_entity" not in entry.data
    assert "bank_1_entity" not in entry.data


async def test_seed_never_overwrites_live_assignment(hass):
    """Regression: entries created before seeding existed carry stale
    bank keys from initial setup. Seeding must never overwrite a live
    (restored) assignment — the text entity is the source of truth and
    users may have reassigned banks by editing it directly."""
    mock_restore_cache(hass, (
        State(f"text.{SUFFIX}_bank_1_entity", "light.hue_go"),
    ))
    data = {**ENTRY_DATA, "bank_0_entity": "light.original", "bank_1_entity": "timer"}
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # The live assignment wins; the empty bank still gets seeded
    assert hass.states.get(f"text.{SUFFIX}_bank_1_entity").state == "light.hue_go"
    assert hass.states.get(f"text.{SUFFIX}_bank_2_entity").state == "timer"
    # Stale keys are stripped either way, so this can never recur
    assert "bank_0_entity" not in entry.data
    assert "bank_1_entity" not in entry.data
