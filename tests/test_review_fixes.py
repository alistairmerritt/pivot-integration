"""Regressions from the 0.0.95 review of the whole integration."""
import asyncio
import shutil
from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.pivot import services
from custom_components.pivot.button import do_bank_toggle
from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA, SUFFIX
from .test_device_link import _dead_button_entry, _issue

BLUEPRINTS = Path(__file__).parent.parent / "blueprints" / "automation"


# --- A single press on a bank that cannot be toggled -------------------------

async def test_single_press_toggles_only_what_can_be_toggled(hass):
    """homeassistant.toggle warns on every press for a number or sensor bank."""
    toggles = async_mock_service(hass, "homeassistant", "toggle")
    async_mock_service(hass, "light", "toggle")
    for entity in ("input_number.volume", "number.progress", "sensor.tank"):
        await do_bank_toggle(hass, SUFFIX, entity)
    assert toggles == []
    for entity in ("light.desk", "group.downstairs"):
        await do_bank_toggle(hass, SUFFIX, entity)
    assert [c.data["entity_id"] for c in toggles] == ["light.desk", "group.downstairs"]


# --- Configure, with a bank outside the picker's domains ---------------------

async def test_configure_saves_with_a_bank_from_any_domain(hass):
    """A bank set to, say, a group used to make the Configure form unsavable."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": f"text.{SUFFIX}_bank_1_entity", "value": "group.downstairs"},
        blocking=True,
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    assert result["step_id"] == "banks"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"timer_banks": "none", "bank_0_entity": "group.downstairs"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert hass.states.get(f"text.{SUFFIX}_bank_1_entity").state == "group.downstairs"


# --- Cancelling a timer keeps its duration ------------------------------------

@pytest.fixture
async def running_timer(hass):
    """Control Mode on, the dial on its timer bank (4), a 25-minute timer running."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    reg = er.async_get(hass)
    for platform, key in (
        ("select", "timer_state"), ("number", "timer_duration"),
        ("text", "timer_end"), ("text", "timer_restore_show_value"),
    ):
        reg.async_get_or_create(
            platform, DOMAIN, f"pivot_{SUFFIX}_{key}", config_entry=entry, suggested_object_id=f"{SUFFIX}_{key}",
        )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async def call(domain, service, data):
        await hass.services.async_call(domain, service, data, blocking=True)

    await call("text", "set_value", {"entity_id": f"text.{SUFFIX}_bank_4_entity", "value": "timer"})
    await call("switch", "turn_on", {"entity_id": f"switch.{SUFFIX}_control_mode"})
    await call("number", "set_value", {"entity_id": f"number.{SUFFIX}_active_bank", "value": 4})
    await call("number", "set_value", {"entity_id": f"number.{SUFFIX}_timer_duration", "value": 25})
    await call("text", "set_value", {"entity_id": f"text.{SUFFIX}_timer_end", "value": "2030-01-01T00:00:00+00:00"})
    await call("select", "select_option", {"entity_id": f"select.{SUFFIX}_timer_state", "option": "running"})
    await call("number", "set_value", {"entity_id": f"number.{SUFFIX}_bank_4_value", "value": 60})
    await hass.async_block_till_done()
    return entry


def _timer(hass):
    return (
        hass.states.get(f"select.{SUFFIX}_timer_state").state,
        float(hass.states.get(f"number.{SUFFIX}_timer_duration").state),
        float(hass.states.get(f"number.{SUFFIX}_bank_4_value").state),
    )


async def test_cancel_fallback_keeps_the_duration(hass, running_timer, monkeypatch):
    """Going idle before emptying the gauge turned the 0 into a 1-minute duration."""
    monkeypatch.setattr(services, "CANCEL_FALLBACK_SECS", 0.2)
    await hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
    await hass.async_block_till_done()
    assert _timer(hass) == ("idle", 25.0, 0.0)


async def _use_blueprint(hass, tmp_path, name: str, inputs: dict) -> None:
    """Run one of the repository's blueprints in Home Assistant's own automation engine."""
    hass.config.config_dir = str(tmp_path)
    target = tmp_path / "blueprints" / "automation" / "pivot"
    target.mkdir(parents=True)
    shutil.copy(BLUEPRINTS / name, target / name)
    assert await async_setup_component(
        hass, "automation",
        {"automation": [{"alias": name, "use_blueprint": {"path": f"pivot/{name}", "input": inputs}}]},
    )
    await hass.async_block_till_done()


TIMER_INPUTS = {
    "suffix": SUFFIX,
    "bank": 4,
    "button_event_entity": "event.test_vpe_button_press",
    "timer_ringing_entity": "switch.test_vpe_timer_ringing",
}


@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_timer_control_cancel_keeps_the_duration(hass, running_timer, tmp_path):
    """The dashboard's cancel (a long_press event) through the real Timer Control blueprint."""
    await _use_blueprint(hass, tmp_path, "pivot_timer.yaml", TIMER_INPUTS)
    hass.bus.async_fire(
        "pivot_button_press",
        {"suffix": SUFFIX, "bank": 4, "press_type": "long_press", "bank_entity": "timer", "control_mode": True},
    )
    await hass.async_block_till_done()
    assert _timer(hass) == ("idle", 25.0, 0.0)
    assert hass.states.get(f"text.{SUFFIX}_timer_end").state == ""


@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_timer_control_paused_expiry_keeps_the_duration(hass, running_timer, tmp_path, freezer):
    """A timer paused for 15 minutes is reset; that reset also kept turning into 1 minute."""
    await hass.services.async_call(
        "select", "select_option", {"entity_id": f"select.{SUFFIX}_timer_state", "option": "paused"}, blocking=True,
    )
    await hass.services.async_call(
        "text", "set_value", {"entity_id": f"text.{SUFFIX}_timer_end", "value": "P600"}, blocking=True,
    )
    await _use_blueprint(hass, tmp_path, "pivot_timer.yaml", TIMER_INPUTS)
    # The blueprint checks every 30 seconds, on the half minute.
    later = (dt_util.utcnow() + timedelta(minutes=16)).replace(second=30, microsecond=0)
    freezer.move_to(later)
    async_fire_time_changed(hass, later)
    # A bounded wait: with the old order, the blueprint's "duration changed"
    # step waits on a clock that is frozen here and would hang the test.
    await asyncio.wait_for(hass.async_block_till_done(), 10)
    assert _timer(hass) == ("idle", 25.0, 0.0)


def _blueprint(name: str):
    class Loader(yaml.SafeLoader):
        pass
    Loader.add_constructor("!input", lambda loader, node: loader.construct_scalar(node))
    return yaml.load((BLUEPRINTS / name).read_text(), Loader=Loader)


def _writes_gauge(step) -> bool:
    """True if a step, or anything nested in it, writes the timer bank's gauge."""
    if isinstance(step, dict):
        if step.get("action") == "number.set_value" and "bank_value_entity" in str(step.get("target")):
            return True
        return any(_writes_gauge(v) for v in step.values())
    if isinstance(step, list):
        return any(_writes_gauge(v) for v in step)
    return False


def _gauge_writes_after_idle(node, found: list) -> list:
    """Every sequence where a step sets the timer idle and a later step writes the gauge."""
    if isinstance(node, list):
        for i, step in enumerate(node):
            if isinstance(step, dict) and step.get("action") == "select.select_option" \
                    and step.get("data", {}).get("option") == "idle":
                found.extend(later for later in node[i + 1:] if _writes_gauge(later))
        for item in node:
            _gauge_writes_after_idle(item, found)
    elif isinstance(node, dict):
        for value in node.values():
            _gauge_writes_after_idle(value, found)
    return found


@pytest.mark.parametrize("name", ["pivot_timer.yaml", "pivot_timer_voice.yaml"])
def test_blueprints_empty_the_gauge_before_going_idle(name):
    """Pivot reads a gauge write on an idle timer bank as a new duration (1 minute for 0)."""
    assert _gauge_writes_after_idle(_blueprint(name), []) == []


# --- Automations are not the device ------------------------------------------

@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_time_triggered_automation_is_not_proof_the_device_is_online(hass, monkeypatch):
    """Timer Control rewrites the gauge every 30 s with a bare context, even with the VPE offline."""
    entry, _ = await _dead_button_entry(hass, monkeypatch, "aa:bb:cc:00:09:01")
    assert await async_setup_component(
        hass, "automation",
        {"automation": {
            "alias": "gauge",
            "trigger": {"trigger": "time_pattern", "seconds": "/5"},
            "action": {"action": "number.set_value", "target": {"entity_id": f"number.{SUFFIX}_active_bank"}, "data": {"value": 3}},
        }},
    )
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    assert hass.states.get(f"number.{SUFFIX}_active_bank").state == "3.0"
    assert _issue(hass, entry) is None


# --- Re-pointing a bank at the timer ------------------------------------------

async def test_repointing_a_bank_at_the_timer_shows_its_duration(hass, running_timer):
    """Every other re-point updates the gauge at once; the timer was left showing the old value."""
    await hass.services.async_call(
        "select", "select_option", {"entity_id": f"select.{SUFFIX}_timer_state", "option": "idle"}, blocking=True,
    )
    hass.states.async_set("light.desk", "on", {"brightness": 153})
    await hass.services.async_call(
        "text", "set_value", {"entity_id": f"text.{SUFFIX}_bank_2_entity", "value": "light.desk"}, blocking=True,
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(f"number.{SUFFIX}_bank_2_value").state) == 60.0
    await hass.services.async_call(
        "text", "set_value", {"entity_id": f"text.{SUFFIX}_bank_2_entity", "value": "timer"}, blocking=True,
    )
    await hass.async_block_till_done()
    # 25 minutes on the 1–60 scale, and the duration itself untouched.
    assert float(hass.states.get(f"number.{SUFFIX}_bank_2_value").state) == 41.0
    assert float(hass.states.get(f"number.{SUFFIX}_timer_duration").state) == 25.0
