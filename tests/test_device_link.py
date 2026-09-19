"""Tests for the entry's link to its ESPHome device.

Three failure modes of that link shipped silently until v0.0.91:

1. Renaming the device in ESPHome broke the settings push, because the push
   called an action named after the ESPHome name stored at setup.
2. Adding the VPE to Home Assistant again left the entry linked to the old
   device, and the only fix was deleting and re-adding the entry.
3. Nothing warned when the entry was linked to a device whose button could
   not be heard.
"""
import logging
from datetime import timedelta

from homeassistant import config_entries
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Context, CoreState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.pivot import link_check
from custom_components.pivot.const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    DOMAIN,
)
from custom_components.pivot.device_sync import RETRY_DELAYS

from .const import ENTRY_DATA, ESPHOME_NAME, SUFFIX

BUTTON_PRESSED = "2026-01-01T00:00:00.000+00:00"


async def _esphome_device(
    hass,
    name: str,
    mac: str,
    *,
    button_state: str | None = BUTTON_PRESSED,
    host: str | None = None,
) -> dr.DeviceEntry:
    """Create an ESPHome device, optionally with its button event entity."""
    esphome_entry = MockConfigEntry(
        domain="esphome",
        data={"device_name": name, "host": host or f"{name}.local"} if host is None
        else {"host": host},
    )
    esphome_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=esphome_entry.entry_id,
        identifiers={("esphome", mac)},
        name=f"VPE {mac}",
    )
    if button_state is not None:
        entity = er.async_get(hass).async_get_or_create(
            "event", "esphome", f"{mac}-button",
            device_id=device.id,
            original_device_class="button",
            suggested_object_id=f"{mac.replace(':', '')}_button_press",
        )
        hass.states.async_set(entity.entity_id, button_state, {"device_class": "button"})
    return device


def _button_entity_id(hass, device: dr.DeviceEntry) -> str:
    entries = er.async_entries_for_device(er.async_get(hass), device.id)
    return next(e.entity_id for e in entries if e.domain == "event")


def _pivot_entry(hass, device_id: str | None, stored_name: str = ESPHOME_NAME):
    data = {**ENTRY_DATA, CONF_ESPHOME_DEVICE_NAME: stored_name}
    if device_id is None:
        data.pop(CONF_DEVICE_ID)
    else:
        data[CONF_DEVICE_ID] = device_id
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="Test VPE")
    entry.add_to_hass(hass)
    return entry


async def _setup(hass, entry) -> None:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _setup_during_startup(hass, entry) -> None:
    """Set up while HA is starting, then fire STARTED (a real restart)."""
    hass.set_state(CoreState.starting)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()


def _issue(hass, entry):
    return ir.async_get(hass).async_get_issue(DOMAIN, link_check.link_issue_id(entry))


def _recorder(pushes: list):
    async def _handler(call):
        pushes.append(call)
    return _handler


# --- 1. The settings push follows ESPHome renames -----------------------------

async def test_push_uses_current_esphome_name_after_rename(hass):
    """Renamed in ESPHome since setup: the push must reach the NEW name."""
    device = await _esphome_device(hass, "renamed-vpe", "aa:bb:cc:00:00:01")
    old, new = [], []
    old_slug = ESPHOME_NAME.replace("-", "_")
    hass.services.async_register("esphome", f"{old_slug}_pivot_sync_settings_v2", _recorder(old))
    hass.services.async_register("esphome", "renamed_vpe_pivot_sync_settings_v2", _recorder(new))

    await _setup_during_startup(hass, _pivot_entry(hass, device.id, stored_name=ESPHOME_NAME))

    assert len(new) == 1
    assert old == []


async def test_push_follows_a_rename_during_the_session(hass):
    """ESPHome records the new name, then registers actions under it."""
    device = await _esphome_device(hass, "first-name", "aa:bb:cc:00:00:02")
    entry = _pivot_entry(hass, device.id, stored_name="first-name")
    await _setup_during_startup(hass, entry)

    esphome_entry = hass.config_entries.async_get_entry(next(iter(device.config_entries)))
    hass.config_entries.async_update_entry(
        esphome_entry, data={**esphome_entry.data, "device_name": "second-name"}
    )
    pushes = []
    hass.services.async_register("esphome", "second_name_pivot_sync_settings_v2", _recorder(pushes))
    await hass.async_block_till_done()

    assert len(pushes) == 1


async def test_push_falls_back_to_stored_name_when_device_is_gone(hass):
    pushes = []
    hass.services.async_register(
        "esphome", f"{ESPHOME_NAME.replace('-', '_')}_pivot_sync_settings_v2", _recorder(pushes)
    )
    await _setup_during_startup(hass, _pivot_entry(hass, "no-such-device"))
    assert len(pushes) == 1


async def test_failed_push_warning_names_the_action_and_the_fix(hass, caplog):
    device = await _esphome_device(hass, "renamed-vpe", "aa:bb:cc:00:00:03")
    await _setup_during_startup(hass, _pivot_entry(hass, device.id))

    with caplog.at_level(logging.WARNING, logger="custom_components.pivot.device_sync"):
        now = dt_util.utcnow()
        for delay in RETRY_DELAYS:
            now += timedelta(seconds=delay + 1)
            async_fire_time_changed(hass, now)
            await hass.async_block_till_done()

    assert "esphome.renamed_vpe_pivot_sync_settings_v2" in caplog.text
    assert "Reconfigure" in caplog.text


# --- 2. Reconfigure re-links the entry and keeps everything else -------------

async def _start_reconfigure(hass, entry):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )


async def test_reconfigure_relinks_device_and_keeps_settings(hass):
    old = await _esphome_device(hass, "old-copy", "aa:bb:cc:00:00:10", button_state="unavailable")
    new = await _esphome_device(hass, "live-copy", "aa:bb:cc:00:00:11")
    plug = await _esphome_device(hass, "a-plug", "aa:bb:cc:00:00:12", button_state=None)
    entry = _pivot_entry(hass, old.id, stored_name="old-copy")
    await _setup(hass, entry)
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_1_entity", "value": "light.desk"},
        blocking=True,
    )

    result = await _start_reconfigure(hass, entry)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    labels = result["data_schema"].schema[CONF_DEVICE_ID].container
    assert labels[old.id].endswith("(unavailable)")
    assert not labels[new.id].endswith(")")
    assert labels[plug.id].endswith("(no button)")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: new.id}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DEVICE_ID] == new.id
    assert entry.data[CONF_ESPHOME_DEVICE_NAME] == "live-copy"
    assert entry.data[CONF_DEVICE_SUFFIX] == SUFFIX
    assert hass.states.get(f"text.{SUFFIX}_bank_1_entity").state == "light.desk"


async def test_reconfigure_rejects_a_device_used_by_another_entry(hass):
    mine = await _esphome_device(hass, "mine", "aa:bb:cc:00:00:20")
    theirs = await _esphome_device(hass, "theirs", "aa:bb:cc:00:00:21")
    entry = _pivot_entry(hass, mine.id, stored_name="mine")
    MockConfigEntry(
        domain=DOMAIN,
        data={**ENTRY_DATA, CONF_DEVICE_ID: theirs.id, CONF_DEVICE_SUFFIX: "other_vpe"},
    ).add_to_hass(hass)
    await _setup(hass, entry)

    result = await _start_reconfigure(hass, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: theirs.id}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_DEVICE_ID: "device_in_use"}
    assert entry.data[CONF_DEVICE_ID] == mine.id


async def test_reconfigure_rejects_a_device_without_a_name(hass):
    mine = await _esphome_device(hass, "mine", "aa:bb:cc:00:00:30")
    by_ip = await _esphome_device(hass, "", "aa:bb:cc:00:00:31", host="192.168.1.50")
    entry = _pivot_entry(hass, mine.id, stored_name="mine")
    await _setup(hass, entry)

    result = await _start_reconfigure(hass, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: by_ip.id}
    )
    assert result["errors"] == {CONF_DEVICE_ID: "cannot_read_device_name"}
    assert entry.data[CONF_DEVICE_ID] == mine.id


async def test_reconfigure_keeps_the_current_device_selected(hass):
    mine = await _esphome_device(hass, "mine", "aa:bb:cc:00:00:40")
    entry = _pivot_entry(hass, mine.id, stored_name="mine")
    await _setup(hass, entry)

    result = await _start_reconfigure(hass, entry)
    key = next(k for k in result["data_schema"].schema if k == CONF_DEVICE_ID)
    assert key.default() == mine.id


# --- 3. Repairs issue when the button cannot be heard ------------------------

async def _firmware_write(hass, entity_id: str, value: float) -> None:
    """A write as the firmware makes it: no user, no parent context."""
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True
    )
    await hass.async_block_till_done()


async def _dead_button_entry(hass, monkeypatch, mac: str):
    """An entry whose linked button is unavailable, past the grace period."""
    monkeypatch.setattr(link_check, "UNAVAILABLE_GRACE", timedelta(0))
    device = await _esphome_device(hass, "stale-copy", mac, button_state="unavailable")
    entry = _pivot_entry(hass, device.id, stored_name="stale-copy")
    await _setup(hass, entry)
    return entry, device


async def test_issue_raised_when_linked_device_has_no_button(hass):
    device = await _esphome_device(hass, "gone", "aa:bb:cc:00:01:00", button_state=None)
    entry = _pivot_entry(hass, device.id, stored_name="gone")
    await _setup(hass, entry)
    issue = _issue(hass, entry)
    assert issue is not None
    assert issue.translation_key == "button_unreachable"
    assert issue.translation_placeholders == {"name": "Test VPE"}


async def test_no_issue_and_old_issue_cleared_when_button_is_available(hass):
    device = await _esphome_device(hass, "live", "aa:bb:cc:00:01:01")
    entry = _pivot_entry(hass, device.id, stored_name="live")
    ir.async_create_issue(
        hass, DOMAIN, link_check.link_issue_id(entry),
        is_fixable=False, severity=ir.IssueSeverity.WARNING,
        translation_key="button_unreachable",
    )
    await _setup(hass, entry)
    assert _issue(hass, entry) is None


async def test_issue_raised_by_firmware_activity_with_dead_button(hass, monkeypatch):
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:02")
    assert _issue(hass, entry) is None  # unavailable alone proves nothing

    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is not None


async def test_knob_turn_on_a_normal_bank_counts_as_activity(hass, monkeypatch):
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:03")
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_1_entity", "value": "light.desk"},
        blocking=True,
    )
    await _firmware_write(hass, f"number.{SUFFIX}_bank_1_value", 42)
    assert _issue(hass, entry) is not None


async def test_people_and_automations_do_not_count_as_firmware(
    hass, monkeypatch, hass_admin_user
):
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:04")
    for context in (Context(user_id=hass_admin_user.id), Context(parent_id="an-automation")):
        value = 2 if context.user_id else 3
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": f"number.{SUFFIX}_active_bank", "value": value},
            blocking=True, context=context,
        )
        await hass.async_block_till_done()
    assert _issue(hass, entry) is None


async def test_pivot_writes_do_not_count_as_firmware(hass, monkeypatch):
    """Pivot's own sync writes and its zeroing of passive banks."""
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:05")
    # A sync write: the assigned light changes and Pivot updates the gauge.
    hass.states.async_set("light.desk", "on", {"brightness": 255})
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_1_entity", "value": "light.desk"},
        blocking=True,
    )
    hass.states.async_set("light.desk", "on", {"brightness": 128})
    await hass.async_block_till_done()
    # A bare-context write to a passive bank, like Pivot holding a scene at 0.
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_2_entity", "value": "scene.movie"},
        blocking=True,
    )
    await _firmware_write(hass, f"number.{SUFFIX}_bank_2_value", 30)
    assert _issue(hass, entry) is None


async def test_button_unavailable_within_grace_does_not_raise(hass):
    device = await _esphome_device(hass, "rebooting", "aa:bb:cc:00:01:06", button_state="unavailable")
    entry = _pivot_entry(hass, device.id, stored_name="rebooting")
    await _setup(hass, entry)
    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is None


async def test_issue_clears_when_button_returns(hass, monkeypatch):
    entry, device = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:07")
    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is not None

    hass.states.async_set(_button_entity_id(hass, device), BUTTON_PRESSED)
    await hass.async_block_till_done()
    assert _issue(hass, entry) is None


async def test_issue_cleared_by_reconfigure(hass, monkeypatch):
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:08")
    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is not None

    live = await _esphome_device(hass, "live-copy", "aa:bb:cc:00:01:09")
    result = await _start_reconfigure(hass, entry)
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_DEVICE_ID: live.id})
    await hass.async_block_till_done()
    assert _issue(hass, entry) is None


async def test_issue_deleted_with_entry(hass, monkeypatch):
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:01:0a")
    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is not None

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _issue(hass, entry) is None


async def test_entry_without_device_link_is_not_checked(hass):
    entry = _pivot_entry(hass, None)
    await _setup(hass, entry)
    assert _issue(hass, entry) is None


async def _press(hass, entity_id: str, when: str) -> None:
    """Fire a button press the way the firmware's event entity does."""
    hass.states.async_set(entity_id, when, {"device_class": "button", "event_type": "single_press"})
    await hass.async_block_till_done()


async def test_button_presses_follow_the_new_device(hass):
    """End to end: after re-linking, presses on the NEW device are heard."""
    old = await _esphome_device(hass, "old-copy", "aa:bb:cc:00:02:00")
    new = await _esphome_device(hass, "live-copy", "aa:bb:cc:00:02:01")
    entry = _pivot_entry(hass, old.id, stored_name="old-copy")
    await _setup(hass, entry)
    old_button, new_button = _button_entity_id(hass, old), _button_entity_id(hass, new)

    presses = async_capture_events(hass, "pivot_button_press")
    await _press(hass, old_button, "2026-01-01T00:01:00.000+00:00")
    assert len(presses) == 1  # linked to the old device for now

    result = await _start_reconfigure(hass, entry)
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_DEVICE_ID: new.id})
    await hass.async_block_till_done()

    presses.clear()
    await _press(hass, old_button, "2026-01-01T00:02:00.000+00:00")
    assert presses == []  # the old copy is no longer listened to

    await _press(hass, new_button, "2026-01-01T00:03:00.000+00:00")
    assert len(presses) == 1  # the newly linked copy is heard
    assert presses[0].data["suffix"] == SUFFIX


async def test_reconfigure_keeps_the_pivot_device_and_its_customisation(hass):
    """The Pivot device is identified by the linked device, so re-linking must
    carry it across — otherwise its area, name and device automations are lost."""
    old = await _esphome_device(hass, "old-copy", "aa:bb:cc:00:02:10")
    new = await _esphome_device(hass, "live-copy", "aa:bb:cc:00:02:11")
    entry = _pivot_entry(hass, old.id, stored_name="old-copy")
    await _setup(hass, entry)

    dev_reg = dr.async_get(hass)
    pivot_device = dev_reg.async_get_device(identifiers={(DOMAIN, old.id)})
    assert pivot_device is not None
    dev_reg.async_update_device(pivot_device.id, name_by_user="Kitchen dial")
    entity_id = f"number.{SUFFIX}_bank_1_value"
    assert er.async_get(hass).async_get(entity_id).device_id == pivot_device.id

    result = await _start_reconfigure(hass, entry)
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_DEVICE_ID: new.id})
    await hass.async_block_till_done()

    moved = dev_reg.async_get_device(identifiers={(DOMAIN, new.id)})
    assert moved is not None
    assert moved.id == pivot_device.id            # same device, not a new one
    assert moved.name_by_user == "Kitchen dial"   # customisation kept
    assert dev_reg.async_get_device(identifiers={(DOMAIN, old.id)}) is None
    assert er.async_get(hass).async_get(entity_id).device_id == moved.id
    pivot_devices = [
        d for d in dev_reg.devices.values()
        if any(i[0] == DOMAIN for i in d.identifiers)
    ]
    assert len(pivot_devices) == 1


async def test_reconfigure_to_the_same_device_is_harmless(hass):
    device = await _esphome_device(hass, "same", "aa:bb:cc:00:02:20")
    entry = _pivot_entry(hass, device.id, stored_name="same")
    await _setup(hass, entry)

    result = await _start_reconfigure(hass, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: device.id}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DEVICE_ID] == device.id
    assert hass.states.get(f"number.{SUFFIX}_bank_1_value") is not None


async def test_link_check_listeners_stop_on_unload(hass, monkeypatch):
    """A leaked listener would keep acting after the entry is unloaded."""
    entry, device = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:03:00")
    await _firmware_write(hass, f"number.{SUFFIX}_active_bank", 2)
    assert _issue(hass, entry) is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    # The button coming back must NOT clear the issue now: nothing is listening.
    hass.states.async_set(_button_entity_id(hass, device), BUTTON_PRESSED)
    await hass.async_block_till_done()
    assert _issue(hass, entry) is not None


async def test_reconfigure_recovers_an_entry_whose_device_was_deleted(hass):
    """The real-world case: the old ESPHome device is gone from Home Assistant.

    The entry still holds its ID, its Pivot device still exists, and a Repairs
    notice is raised at setup. Re-linking must fix all of it.
    """
    entry = _pivot_entry(hass, "deleted-device-id", stored_name="old-copy")
    await _setup(hass, entry)
    assert _issue(hass, entry) is not None

    dev_reg = dr.async_get(hass)
    pivot_device = dev_reg.async_get_device(identifiers={(DOMAIN, "deleted-device-id")})
    assert pivot_device is not None

    live = await _esphome_device(hass, "live-copy", "aa:bb:cc:00:04:00")
    result = await _start_reconfigure(hass, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: live.id}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_DEVICE_ID] == live.id
    assert _issue(hass, entry) is None
    moved = dev_reg.async_get_device(identifiers={(DOMAIN, live.id)})
    assert moved is not None and moved.id == pivot_device.id

    presses = async_capture_events(hass, "pivot_button_press")
    await _press(hass, _button_entity_id(hass, live), "2026-01-01T01:00:00.000+00:00")
    assert len(presses) == 1


async def test_removing_a_healthy_entry_is_clean(hass):
    """Entry removal must not depend on a Repairs issue existing."""
    device = await _esphome_device(hass, "live", "aa:bb:cc:00:05:00")
    entry = _pivot_entry(hass, device.id, stored_name="live")
    await _setup(hass, entry)
    assert _issue(hass, entry) is None

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.config_entries.async_get_entry(entry.entry_id) is None
