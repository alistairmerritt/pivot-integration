"""Regression tests for state lost across Home Assistant restarts.

Both scenarios shipped as real bugs (fixed in v0.0.84):

1. The bank colour picker pushed its restored colour over an active
   mirror colour on every startup.
2. Device settings never reached the firmware after a restart because the
   ESPHome integration drops entity-addition and same-state events; the
   integration now pushes them explicitly via the pivot_sync_settings
   action.
"""
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX, SYNC_SERVICE

MIRRORED = "#AB3412"
CONFIGURED = "#2889FF"


async def _setup_entry_during_startup(hass):
    """Set up the entry while HA is still starting, then fire STARTED.

    This mirrors a real restart: integration setup happens first, and
    anything hooked on the started signal fires afterwards. Setting up
    with HA already 'running' would let started-hooks fire mid-setup,
    which is not the ordering a restart produces.
    """
    hass.set_state(CoreState.starting)
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    return entry


async def test_mirror_colour_survives_restart(hass):
    """An active mirror colour must not be overwritten by the configured
    bank colour when HA restarts."""
    mock_restore_cache(hass, (
        State(f"text.{SUFFIX}_bank_1_entity", "light.test_rgb"),
        State(f"text.{SUFFIX}_bank_1_color", MIRRORED),
        State(f"text.{SUFFIX}_bank_1_configured_color", CONFIGURED),
        State(f"switch.{SUFFIX}_bank_1_mirror_light", "on"),
        State(
            f"light.{SUFFIX}_bank_1_color_light", "on",
            {"rgb_color": (40, 137, 255)},
        ),
    ))
    # The mirrored RGB light, already restored by its own integration
    hass.states.async_set("light.test_rgb", "on", {"rgb_color": (171, 52, 18)})

    await _setup_entry_during_startup(hass)

    # Display colour keeps the mirrored value; configured colour untouched
    assert hass.states.get(f"text.{SUFFIX}_bank_1_color").state == MIRRORED
    assert hass.states.get(f"text.{SUFFIX}_bank_1_configured_color").state == CONFIGURED


async def test_mirror_off_restores_configured_colour(hass):
    """With mirror off, a leftover mirrored display colour is restored to
    the configured colour at startup."""
    mock_restore_cache(hass, (
        State(f"text.{SUFFIX}_bank_1_entity", "light.test_rgb"),
        State(f"text.{SUFFIX}_bank_1_color", MIRRORED),
        State(f"text.{SUFFIX}_bank_1_configured_color", CONFIGURED),
        State(f"switch.{SUFFIX}_bank_1_mirror_light", "off"),
        State(
            f"light.{SUFFIX}_bank_1_color_light", "on",
            {"rgb_color": (40, 137, 255)},
        ),
    ))

    await _setup_entry_during_startup(hass)

    assert hass.states.get(f"text.{SUFFIX}_bank_1_color").state == CONFIGURED


async def test_settings_pushed_to_device_on_start(hass):
    """All settings are pushed via the pivot_sync_settings action once HA
    has started, with restored values."""
    pushes = []

    async def _fake_sync(call):
        pushes.append(call)

    hass.services.async_register("esphome", SYNC_SERVICE, _fake_sync)
    mock_restore_cache(hass, (
        State(f"switch.{SUFFIX}_dim_when_idle", "on"),
        State(f"switch.{SUFFIX}_bank_2_mirror_light", "on"),
    ))

    await _setup_entry_during_startup(hass)

    assert len(pushes) == 1
    data = pushes[0].data
    assert data["dim_when_idle_in"] is True
    assert data["bank_mirror_2_in"] is True
    assert data["control_mode_in"] is False
    assert data["bank_mirror_1_in"] is False
    expected_keys = {
        "control_mode_in", "show_control_value_in", "dim_when_idle_in",
        "bank_mirror_1_in", "bank_mirror_2_in", "bank_mirror_3_in",
        "bank_mirror_4_in",
        "bank_passive_1_in", "bank_passive_2_in", "bank_passive_3_in",
        "bank_passive_4_in",
    }
    assert set(data) == expected_keys


async def test_settings_push_skipped_without_firmware_action(hass):
    """With older firmware (no pivot_sync_settings service) setup still
    succeeds and nothing is raised."""
    entry = await _setup_entry_during_startup(hass)
    assert entry.state.value == "loaded"
