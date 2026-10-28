"""Every timer flow, driven the way the hardware drives it.

A press changes the VPE's button event entity. Pivot's button listener turns
that into `pivot_button_press`, and Timer Control reacts to both, all inside
Home Assistant's handling of that one state change: where the 0.0.95 cancel
bug hid, and where tests that fire the event directly never look. Knob turns
are bare-context writes to the bank value, as the firmware's are. A template
switch stands in for the firmware's timer_ringing switch: turning it off
while the timer is alerting resets it to idle and puts Dim LEDs When Idle
back as it was, as firmware v0.0.30 does.
"""
import asyncio
import shutil
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.components import conversation
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.pivot.const import (
    CONF_DEVICE_ID,
    CONF_MEDIA_PLAYER_ENTITY,
    CONF_TTS_ENTITY,
    DOMAIN,
)

from .const import ENTRY_DATA, ESPHOME_NAME, SUFFIX

pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])

BLUEPRINTS = Path(__file__).parent.parent / "blueprints" / "automation"
BUTTON = "event.test_vpe_button_press"
RINGING = f"switch.{SUFFIX}_timer_ringing"
STATE = f"select.{SUFFIX}_timer_state"
DURATION = f"number.{SUFFIX}_timer_duration"
END = f"text.{SUFFIX}_timer_end"
GAUGE = f"number.{SUFFIX}_bank_4_value"
ACTIVE = f"number.{SUFFIX}_active_bank"
SHOW_VALUE = f"switch.{SUFFIX}_show_control_value"
DIM = f"switch.{SUFFIX}_dim_when_idle"
RESTORE_DIM = f"text.{SUFFIX}_timer_restore_dim"
RESTORE_SHOW = f"text.{SUFFIX}_timer_restore_show_value"


@dataclass
class Rig:
    hass: HomeAssistant
    freezer: object
    vpe: dr.DeviceEntry
    speech: list = field(default_factory=list)

    async def settle(self, seconds: float = 1) -> None:
        """Let time pass, then let everything finish.

        The clock is frozen, so a run waiting on its own delay or debounce
        (the finish message's 3 s, the knob's 150 ms) would never finish and
        block_till_done would wait forever. While anything is still running,
        let a tenth of a second pass now and then, as it would for real.
        """
        self.freezer.tick(timedelta(seconds=seconds))
        async_fire_time_changed(self.hass)
        done = asyncio.ensure_future(self.hass.async_block_till_done())
        for spin in range(4000):
            await asyncio.sleep(0)
            if done.done():
                return done.result()
            if spin % 50 == 49:
                self.freezer.tick(timedelta(milliseconds=100))
                async_fire_time_changed(self.hass)
        done.cancel()
        raise AssertionError("Home Assistant never settled")

    async def wait(self, seconds: float) -> None:
        """Let a long time pass in 30-second steps, so every gauge update runs."""
        while seconds > 0:
            await self.settle(min(30, seconds))
            seconds -= 30

    async def press(self, kind: str) -> None:
        self.freezer.tick(timedelta(milliseconds=200))
        self.hass.states.async_set(BUTTON, dt_util.utcnow().isoformat(), {"event_type": kind, "device_class": "button"})
        await self.settle()

    async def knob(self, value: float) -> None:
        await self.hass.services.async_call("number", "set_value", {"entity_id": GAUGE, "value": value}, blocking=True)
        await self.settle()

    async def say(self, text: str) -> None:
        await conversation.async_converse(self.hass, text, None, Context(), language="en", device_id=self.vpe.id)
        await self.settle()

    async def set(self, domain: str, service: str, entity_id: str, **data) -> None:
        await self.hass.services.async_call(domain, service, {"entity_id": entity_id, **data}, blocking=True)
        await self.settle()

    def state(self, entity_id: str) -> str:
        return self.hass.states.get(entity_id).state

    @property
    def timer(self) -> tuple[str, float, float]:
        return self.state(STATE), float(self.state(DURATION)), float(self.state(GAUGE))

    @property
    def said(self) -> list[str]:
        return [" ".join(call.data["message"].split()) for call in self.speech]

    def seconds_left(self) -> float:
        return (dt_util.parse_datetime(self.state(END)) - dt_util.utcnow()).total_seconds()


async def _rig(hass, tmp_path, freezer, **control_inputs) -> Rig:
    freezer.move_to("2026-10-27T10:00:05+00:00")
    esphome = MockConfigEntry(domain="esphome", data={"device_name": ESPHOME_NAME})
    esphome.add_to_hass(hass)
    vpe = dr.async_get(hass).async_get_or_create(
        config_entry_id=esphome.entry_id, identifiers={("esphome", "aa:bb:cc:00:0f:01")}, name="Test VPE",
    )
    reg = er.async_get(hass)
    reg.async_get_or_create(
        "event", "esphome", "button", device_id=vpe.id, original_device_class="button",
        suggested_object_id="test_vpe_button_press",
    )
    hass.states.async_set(BUTTON, "2026-10-26T09:00:00+00:00", {"event_type": "single_press", "device_class": "button"})

    data = {**ENTRY_DATA, CONF_DEVICE_ID: vpe.id, CONF_TTS_ENTITY: "tts.test", CONF_MEDIA_PLAYER_ENTITY: "media_player.test"}
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="Test VPE")
    entry.add_to_hass(hass)
    for platform, key in (
        ("select", "timer_state"), ("number", "timer_duration"),
        ("text", "timer_end"), ("text", "timer_restore_show_value"),
    ):
        reg.async_get_or_create(platform, DOMAIN, f"pivot_{SUFFIX}_{key}", config_entry=entry, suggested_object_id=f"{SUFFIX}_{key}")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    speech = async_mock_service(hass, "tts", "speak")
    # The firmware's timer_ringing switch: off while alerting puts the timer
    # back to idle and Dim LEDs When Idle back from its saved value.
    assert await async_setup_component(hass, "template", {"template": [{"switch": [{
        "name": f"{SUFFIX}_timer_ringing",
        "unique_id": "timer_ringing",
        "turn_on": [],
        "turn_off": [{
            "if": [{"condition": "state", "entity_id": STATE, "state": "alerting"}],
            "then": [
                {"action": "select.select_option", "target": {"entity_id": STATE}, "data": {"option": "idle"}},
                {"action": f"switch.turn_{{{{ 'off' if is_state('{RESTORE_DIM}', 'off') else 'on' }}}}",
                 "target": {"entity_id": DIM}},
                {"action": "text.set_value", "target": {"entity_id": RESTORE_DIM}, "data": {"value": ""}},
            ],
        }],
    }]}]})
    await hass.async_block_till_done()
    reg.async_update_entity(RINGING, device_id=vpe.id)

    hass.config.config_dir = str(tmp_path)
    target = tmp_path / "blueprints" / "automation" / "pivot"
    target.mkdir(parents=True)
    for name in ("pivot_timer.yaml", "pivot_timer_voice.yaml"):
        shutil.copy(BLUEPRINTS / name, target / name)
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    control = {"suffix": SUFFIX, "bank": 4, "button_event_entity": BUTTON, "timer_ringing_entity": RINGING,
               "finish_message": "Time is up.", **control_inputs}
    assert await async_setup_component(hass, "automation", {"automation": [
        {"alias": "control", "use_blueprint": {"path": "pivot/pivot_timer.yaml", "input": control}},
        {"alias": "voice", "use_blueprint": {"path": "pivot/pivot_timer_voice.yaml", "input": {"suffix": SUFFIX, "timer_ringing_entity": RINGING}}},
    ]})
    await hass.async_block_till_done()

    rig = Rig(hass, freezer, vpe, speech)
    await rig.set("text", "set_value", f"text.{SUFFIX}_bank_4_entity", value="timer")
    await rig.set("switch", "turn_on", f"switch.{SUFFIX}_control_mode")
    await rig.set("number", "set_value", ACTIVE, value=4)
    await rig.set("number", "set_value", DURATION, value=25)
    # Timer Control will not start a timer within 3 s of going idle.
    await rig.settle(5)
    return rig


@pytest.fixture
async def rig(hass, tmp_path, freezer) -> Rig:
    return await _rig(hass, tmp_path, freezer)


def _no_one_minute(rig: Rig) -> None:
    assert not [m for m in rig.said if m.startswith("1 minute timer")], rig.said


# --- What is and isn't a press --------------------------------------------------

async def test_a_reconnect_is_not_a_press(rig):
    """The button comes back from unavailable carrying its last press."""
    last = rig.state(BUTTON)
    rig.hass.states.async_set(BUTTON, "unavailable", {"device_class": "button"})
    await rig.settle()
    rig.hass.states.async_set(BUTTON, last, {"event_type": "single_press", "device_class": "button"})
    await rig.settle()
    assert rig.state(STATE) == "idle"


async def test_the_first_press_after_an_unknown_button_counts(rig):
    """Home Assistant stopped while the VPE was offline: it comes back 'unknown', and the next change is a press.

    Seen on the Spare VPE on 21 October 2026; Pivot dropped that press.
    """
    rig.hass.states.async_set(BUTTON, "unavailable", {"device_class": "button"})
    await rig.settle()
    rig.hass.states.async_set(BUTTON, "unknown", {"event_type": "double_press", "device_class": "button"})
    await rig.settle()
    assert rig.state(STATE) == "idle"
    await rig.press("single_press")
    assert rig.state(STATE) == "running"


# --- The button --------------------------------------------------------------

async def test_press_start_pause_resume_and_long_press_cancel(rig):
    await rig.press("single_press")
    assert rig.timer == ("running", 25.0, 100.0)
    assert 25 * 60 - 5 < rig.seconds_left() <= 25 * 60
    assert (rig.state(SHOW_VALUE), rig.state(DIM)) == ("on", "off")
    assert rig.said[-1] == "25 minute timer started."

    await rig.wait(5 * 60)
    assert rig.state(STATE) == "running"
    assert 75 <= float(rig.state(GAUGE)) <= 82  # about 20 of 25 minutes left

    await rig.press("single_press")
    assert rig.state(STATE) == "paused"
    assert rig.state(END).startswith("P")
    assert rig.said[-1].startswith("Timer paused. 19 minutes remaining")
    assert rig.state(DIM) == "on"

    await rig.wait(120)
    assert rig.state(STATE) == "paused"

    await rig.press("single_press")
    assert rig.state(STATE) == "running"
    assert rig.said[-1] == "Timer resumed."

    await rig.press("long_press")
    assert rig.timer == ("idle", 25.0, 0.0)
    assert rig.state(END) == ""
    # Both settings go back to how they were before the timer.
    assert (rig.state(SHOW_VALUE), rig.state(DIM)) == ("off", "off")
    assert rig.said[-1] == "Timer cancelled."
    _no_one_minute(rig)


async def test_long_press_while_paused_cancels(rig):
    await rig.press("single_press")
    await rig.press("single_press")
    await rig.press("long_press")
    assert rig.timer == ("idle", 25.0, 0.0)
    _no_one_minute(rig)


async def test_long_press_on_another_bank_leaves_the_timer_alone(rig):
    await rig.press("single_press")
    await rig.set("number", "set_value", ACTIVE, value=1)
    await rig.press("long_press")
    assert rig.state(STATE) == "running"


async def test_finish_rings_and_a_press_dismisses(rig):
    await rig.set("number", "set_value", DURATION, value=2)
    await rig.press("single_press")
    await rig.set("number", "set_value", ACTIVE, value=1)
    await rig.wait(2 * 60 + 35)
    assert rig.state(STATE) == "alerting"
    assert rig.state(END) == ""
    assert rig.said[-1] == "Time is up."
    # The finish brings the dial back to the timer bank, empty.
    assert (rig.state(ACTIVE), float(rig.state(GAUGE))) == ("4.0", 0.0)

    await rig.press("single_press")
    assert rig.timer == ("idle", 2.0, 0.0)
    assert rig.state(DIM) == "off"
    # A second press straight after the dismiss is not a new start...
    await rig.press("single_press")
    assert rig.state(STATE) == "idle"
    # ...but one a few seconds later is.
    await rig.settle(4)
    await rig.press("single_press")
    assert rig.state(STATE) == "running"
    _no_one_minute(rig)


async def test_a_timer_paused_for_15_minutes_is_cleared(rig):
    await rig.press("single_press")
    await rig.press("single_press")
    await rig.wait(16 * 60)
    assert rig.timer == ("idle", 25.0, 0.0)
    assert rig.state(END) == ""
    _no_one_minute(rig)


async def test_an_alarm_nobody_stops_is_cleared_after_16_minutes(rig):
    await rig.set("number", "set_value", DURATION, value=1)
    await rig.press("single_press")
    await rig.wait(95)
    assert rig.state(STATE) == "alerting"
    await rig.wait(17 * 60)
    assert rig.timer == ("idle", 1.0, 0.0)


# --- The knob ------------------------------------------------------------------

async def test_knob_sets_the_duration_while_idle(rig):
    await rig.knob(50)
    assert rig.timer == ("idle", 30.0, 50.0)
    assert rig.said[-1] == "30 minute timer. Press to start."
    await rig.knob(0)
    assert rig.timer == ("idle", 1.0, 0.0)
    assert rig.said[-1] == "1 minute timer. Press to start."


async def test_knob_does_nothing_while_running(rig):
    await rig.press("single_press")
    await rig.knob(10)
    assert rig.state(DURATION) == "25.0"
    assert not [m for m in rig.said if "Press to start" in m]


async def test_knob_on_another_bank_leaves_the_duration(rig):
    await rig.set("number", "set_value", ACTIVE, value=1)
    await rig.knob(80)
    assert rig.state(DURATION) == "25.0"


# --- The dashboard ---------------------------------------------------------------

async def test_dashboard_toggle_and_cancel(rig):
    await rig.set("number", "set_value", ACTIVE, value=2)
    await rig.hass.services.async_call(DOMAIN, "timer_toggle", {"device": SUFFIX}, blocking=True)
    await rig.settle()
    # The timer bank is made active first, as the physical button would need.
    assert (rig.state(ACTIVE), rig.state(STATE)) == ("4.0", "running")
    await rig.hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
    await rig.settle(3)
    assert rig.timer == ("idle", 25.0, 0.0)
    assert rig.said.count("Timer cancelled.") == 1
    _no_one_minute(rig)


async def test_dashboard_preset_on_the_active_timer_bank(rig):
    # The card writes the bank value; Pivot turns it into the duration, as for the knob.
    await rig.knob(24)
    assert rig.timer == ("idle", 15.0, 24.0)


# --- Voice ---------------------------------------------------------------------------

async def test_voice_start_status_pause_resume_cancel(rig):
    await rig.say("set a 10 minute timer")
    assert rig.timer == ("running", 10.0, 100.0)
    assert rig.said[-1] == "10 minute timer started."
    await rig.say("set a 5 minute timer")
    assert rig.said[-1] == "A timer is already running."
    assert rig.state(DURATION) == "10.0"

    await rig.wait(2 * 60)
    await rig.say("how much time is left")
    assert rig.said[-1].startswith("7 minutes")

    await rig.say("pause the timer")
    assert rig.state(STATE) == "paused"
    await rig.say("how much time is left")
    assert rig.said[-1].startswith("Timer is paused.")
    await rig.say("resume the timer")
    assert rig.state(STATE) == "running"

    await rig.say("cancel the timer")
    assert rig.timer == ("idle", 10.0, 0.0)
    assert rig.said[-1] == "Timer cancelled."
    await rig.say("how much time is left")
    assert rig.said[-1] == "No timer is running."
    _no_one_minute(rig)


@pytest.mark.parametrize(
    "phrase", ["dismiss timer", "dismiss the timer", "dismiss alarm", "dismiss the alarm", "stop the alarm"],
)
async def test_voice_dismiss(rig, phrase):
    await rig.say("set a 1 minute timer")
    await rig.wait(95)
    assert rig.state(STATE) == "alerting"
    await rig.say(phrase)
    assert rig.timer == ("idle", 1.0, 0.0)


async def test_voice_seconds_timer_keeps_the_duration(rig):
    await rig.say("set a 30 second timer")
    assert rig.state(STATE) == "running"
    assert rig.state(DURATION) == "25.0"
    assert 25 < rig.seconds_left() <= 30
    await rig.wait(45)
    assert rig.state(STATE) == "alerting"


async def test_voice_start_with_the_set_duration(rig):
    await rig.say("start a timer")
    assert rig.timer == ("running", 25.0, 100.0)
    assert rig.said[-1] == "25 minute timer started."


async def test_voice_timer_switches_to_the_timer_bank(hass, tmp_path, freezer):
    rig = await _rig(hass, tmp_path, freezer, switch_to_bank_on_start=True)
    await rig.set("number", "set_value", ACTIVE, value=1)
    await rig.say("set a 20 minute timer")
    assert (rig.state(STATE), rig.state(ACTIVE)) == ("running", "4.0")
    # Moving the dial to the timer bank must not turn its full gauge into a duration.
    assert rig.state(DURATION) == "20.0"


# --- The settings a timer borrows ----------------------------------------------
# A timer turns Show Control Value on and Dim LEDs When Idle off while it runs.
# Both go back to how they were, however the timer ends. Until 0.0.97 every
# end turned Dim LEDs When Idle on, which is off by default.

def _settings(rig: Rig) -> tuple[str, str]:
    return rig.state(SHOW_VALUE), rig.state(DIM)


@pytest.fixture(params=[("off", "off"), ("on", "on")], ids=["both-off", "both-on"])
async def before(request, rig) -> tuple[str, str]:
    show, dim = request.param
    await rig.set("switch", f"turn_{show}", SHOW_VALUE)
    await rig.set("switch", f"turn_{dim}", DIM)
    return request.param


async def _ended(rig: Rig, before: tuple[str, str]) -> None:
    assert rig.state(STATE) == "idle"
    assert _settings(rig) == before
    assert (rig.state(RESTORE_SHOW), rig.state(RESTORE_DIM)) == ("", "")


async def test_settings_after_a_long_press_cancel(rig, before):
    await rig.press("single_press")
    assert _settings(rig) == ("on", "off")
    await rig.press("long_press")
    await _ended(rig, before)


async def test_settings_after_a_pause_and_a_cancel(rig, before):
    await rig.press("single_press")
    await rig.press("single_press")
    assert rig.state(DIM) == "on"  # a paused gauge dims
    await rig.press("long_press")
    await _ended(rig, before)


async def test_settings_after_an_alarm(rig, before):
    await rig.set("number", "set_value", DURATION, value=1)
    await rig.press("single_press")
    await rig.wait(95)
    assert rig.state(STATE) == "alerting"
    await rig.press("single_press")
    await _ended(rig, before)


async def test_settings_after_an_alarm_nobody_stops(rig, before):
    await rig.set("number", "set_value", DURATION, value=1)
    await rig.press("single_press")
    await rig.wait(95)
    await rig.wait(17 * 60)
    await _ended(rig, before)


async def test_settings_after_15_minutes_paused(rig, before):
    await rig.press("single_press")
    await rig.press("single_press")
    await rig.wait(16 * 60)
    await _ended(rig, before)


async def test_settings_after_a_voice_cancel(rig, before):
    await rig.say("set a 10 minute timer")
    await rig.say("cancel the timer")
    await _ended(rig, before)


async def test_settings_after_a_press_start_and_a_voice_cancel(rig, before):
    """Voice cancel left Show Control Value on, and the next start saved that as the setting."""
    await rig.press("single_press")
    await rig.say("cancel the timer")
    await _ended(rig, before)


async def test_settings_after_a_voice_alarm(rig, before):
    await rig.say("set a 1 minute timer")
    await rig.wait(95)
    assert rig.state(STATE) == "alerting"
    await rig.say("stop the alarm")
    await _ended(rig, before)


async def test_settings_after_a_dashboard_cancel(rig, before):
    await rig.hass.services.async_call(DOMAIN, "timer_toggle", {"device": SUFFIX}, blocking=True)
    await rig.settle()
    await rig.hass.services.async_call(DOMAIN, "timer_cancel", {"device": SUFFIX}, blocking=True)
    await rig.settle(3)
    await _ended(rig, before)


async def test_a_timer_started_before_the_upgrade_ends_with_dim_on(rig):
    """No saved value: an older blueprint started it, and turned dim on at the end."""
    await rig.press("single_press")
    await rig.set("text", "set_value", RESTORE_DIM, value="")
    await rig.press("long_press")
    assert rig.state(DIM) == "on"
