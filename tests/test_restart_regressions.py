"""Regression tests for state lost across Home Assistant restarts.

Both scenarios shipped as real bugs (fixed in v0.0.84):

1. The bank colour picker pushed its restored colour over an active
   mirror colour on every startup.
2. Device settings never reached the firmware after a restart because the
   ESPHome integration drops entity-addition and same-state events; the
   integration now pushes them explicitly via the pivot_sync_settings
   action.
"""
import asyncio
from datetime import timedelta

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)

from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX, SYNC_SERVICE, SYNC_SERVICE_V2

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

    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)
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
        # Active bank, per-bank values and colours go stale after a restart
        # the same way the booleans did, so they are repaired in this push too.
        "active_bank_in",
        "bank_value_1_in", "bank_value_2_in", "bank_value_3_in",
        "bank_value_4_in",
        "bank_color_1_in", "bank_color_2_in", "bank_color_3_in",
        "bank_color_4_in",
        "bank_configured_color_1_in", "bank_configured_color_2_in",
        "bank_configured_color_3_in", "bank_configured_color_4_in",
    }
    assert set(data) == expected_keys

    # active_bank must be a 1-based int, matching the firmware action signature.
    assert isinstance(data["active_bank_in"], int)
    assert 1 <= data["active_bank_in"] <= 4
    for bank in range(1, 5):
        assert isinstance(data[f"bank_value_{bank}_in"], float)
        for key in (f"bank_color_{bank}_in", f"bank_configured_color_{bank}_in"):
            color = data[key]
            assert isinstance(color, str)
            assert len(color) == 7 and color.startswith("#")


async def test_settings_push_skipped_when_color_unavailable(hass):
    """A partial push is never sent. If any source entity is unreadable when
    the push runs, the whole push is skipped so the device keeps its cached
    values instead of being handed guesses."""
    pushes = []

    async def _fake_sync(call):
        pushes.append(call)

    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)

    # Same ordering as _setup_entry_during_startup, but with one source
    # entity knocked out between setup and the started-hook that pushes.
    hass.set_state(CoreState.starting)
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(f"text.{SUFFIX}_bank_1_color", "unavailable")

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert pushes == []


async def test_settings_push_skipped_without_firmware_action(hass):
    """With older firmware (no pivot_sync_settings service) setup still
    succeeds and nothing is raised."""
    entry = await _setup_entry_during_startup(hass)
    assert entry.state.value == "loaded"


async def test_settings_pushed_when_device_connects_after_start(hass):
    """The real restart ordering: the ESPHome device connects AFTER Home
    Assistant has started, so its action does not exist at the moment the
    push first runs. The settings must still reach it.

    This is the bug where Show Control Value / Dim When Idle silently kept
    their old device-side values after an HA restart until toggled off and on.
    """
    pushes = []

    async def _fake_sync(call):
        pushes.append(call)

    # Device not connected yet — ESPHome has not registered the action.
    await _setup_entry_during_startup(hass)
    assert pushes == []

    # Device connects; ESPHome registers its user-defined action.
    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)
    await hass.async_block_till_done()

    assert len(pushes) == 1
    assert pushes[0].data["dim_when_idle_in"] is False


async def test_settings_pushed_only_once(hass):
    """A successful push must not be repeated on later service churn."""
    pushes = []

    async def _fake_sync(call):
        pushes.append(call)

    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)
    await _setup_entry_during_startup(hass)
    assert len(pushes) == 1

    hass.services.async_remove("esphome", SYNC_SERVICE_V2)
    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)
    await hass.async_block_till_done()
    assert len(pushes) == 1


async def test_settings_push_falls_back_to_v1_on_old_firmware(hass):
    """Firmware predating v2 still gets the boolean repair.

    An ESPHome action requires every declared argument, so calling v2 against
    old firmware fails outright. HACS and ESPHome update independently, so this
    combination WILL happen in the field and must not lose the boolean sync.
    """
    pushes = []

    async def _fake_sync(call):
        pushes.append(call)

    # Old firmware advertises only the original 11-argument action.
    hass.services.async_register("esphome", SYNC_SERVICE, _fake_sync)
    await _setup_entry_during_startup(hass)

    assert len(pushes) == 1
    data = pushes[0].data
    assert set(data) == {
        "control_mode_in", "show_control_value_in", "dim_when_idle_in",
        "bank_mirror_1_in", "bank_mirror_2_in", "bank_mirror_3_in",
        "bank_mirror_4_in",
        "bank_passive_1_in", "bank_passive_2_in", "bank_passive_3_in",
        "bank_passive_4_in",
    }


async def test_push_retried_when_device_is_unreachable(hass):
    """A registered action does not prove the device is reachable.

    Home Assistant registers ESPHome actions from CACHED metadata during setup,
    so has_service() is true for an offline device. A failed call must be
    retried, not silently recorded as delivered.
    """
    calls = []
    offline = True

    async def _fake_sync(call):
        calls.append(call)
        if offline:
            raise HomeAssistantError("device is offline")

    hass.services.async_register("esphome", SYNC_SERVICE_V2, _fake_sync)
    await _setup_entry_during_startup(hass)

    # Attempted, failed, nothing delivered.
    assert len(calls) == 1

    # Device comes back before the first retry fires.
    offline = False
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()

    assert len(calls) == 2


async def test_v2_wins_when_v1_registers_first(hass):
    """The firmware declares v1 before v2.

    Reacting to a v1 registration the moment it lands would push booleans only
    and set done=True, permanently downgrading a device that supports the full
    v2 repair.
    """
    v1_calls: list = []
    v2_calls: list = []

    async def _v1(call):
        v1_calls.append(call)

    async def _v2(call):
        v2_calls.append(call)

    # Device not connected during startup.
    await _setup_entry_during_startup(hass)
    assert v1_calls == [] and v2_calls == []

    # ESPHome registers the actions in declaration order: v1, then v2.
    hass.services.async_register("esphome", SYNC_SERVICE, _v1)
    hass.services.async_register("esphome", SYNC_SERVICE_V2, _v2)
    await hass.async_block_till_done()

    assert v1_calls == [], "v1 must not win the race against v2"
    assert len(v2_calls) == 1


async def test_v2_registered_while_v1_call_in_flight(hass):
    """v2 can appear DURING a v1 call, not just before or after it.

    The in-progress guard drops the v2 trigger while a v1 push is awaiting, so
    without a recheck the v1 success would set done=True and strand a
    v2-capable device on boolean-only repair until the next restart.
    """
    v1_calls: list = []
    v2_calls: list = []
    v1_started = asyncio.Event()
    release_v1 = asyncio.Event()

    async def _v1(call):
        v1_calls.append(call)
        v1_started.set()
        await release_v1.wait()          # hold the call open

    async def _v2(call):
        v2_calls.append(call)

    # Only the cached v1 action exists at startup (device was on old firmware).
    hass.services.async_register("esphome", SYNC_SERVICE, _v1)
    await _setup_entry_during_startup(hass)
    await v1_started.wait()

    # Device connects on new firmware and registers v2 mid-call.
    hass.services.async_register("esphome", SYNC_SERVICE_V2, _v2)
    release_v1.set()
    await hass.async_block_till_done()

    assert len(v1_calls) == 1
    assert len(v2_calls) == 1, "v2 repair must still run after the v1 fallback"


async def test_degrades_to_v1_when_a_colour_entity_is_missing(hass):
    """A bank colour entity can be absent rather than merely late.

    Observed on a real device: three configured-colour entities had no state at
    all while its siblings had 36 entities each. Aborting every attempt would
    deliver nothing, which is worse than the boolean-only repair that shipped
    before v2 existed. The last attempt degrades instead of giving up.
    """
    v1_calls: list = []
    v2_calls: list = []

    async def _v1(call):
        v1_calls.append(call)

    async def _v2(call):
        v2_calls.append(call)

    hass.services.async_register("esphome", SYNC_SERVICE, _v1)
    hass.services.async_register("esphome", SYNC_SERVICE_V2, _v2)

    hass.set_state(CoreState.starting)
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(f"text.{SUFFIX}_bank_2_configured_color", "unavailable")

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    # Nothing yet: incomplete data is retried, not guessed at.
    assert v1_calls == [] and v2_calls == []

    now = dt_util.utcnow()
    for delay in (5, 10, 20, 30, 60, 120):
        now += timedelta(seconds=delay + 1)
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()

    # v2 never fires with partial data; v1 carries the boolean repair.
    assert v2_calls == []
    assert len(v1_calls) == 1
    assert set(v1_calls[0].data) == {
        "control_mode_in", "show_control_value_in", "dim_when_idle_in",
        "bank_mirror_1_in", "bank_mirror_2_in", "bank_mirror_3_in",
        "bank_mirror_4_in",
        "bank_passive_1_in", "bank_passive_2_in", "bank_passive_3_in",
        "bank_passive_4_in",
    }
