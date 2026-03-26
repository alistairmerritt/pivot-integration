"""Pivot integration.

Handles all runtime logic for Pivot devices:
- Bank control: listens for bank value changes and applies them to assigned entities
- Bank sync: when active bank changes, reads entity state and syncs value back
- Bank toggle: registers a service script.{suffix}_bank_toggle that the firmware
  calls on button press to toggle/activate the active bank's assigned entity
"""
from __future__ import annotations

import logging
import os
import time

import yaml as _yaml

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN, CONF_DEVICE_ID, CONF_FRIENDLY_NAME, CONF_DEVICE_SUFFIX,
    CONF_ANNOUNCEMENTS, CONF_TTS_ENTITY, CONF_MEDIA_PLAYER_ENTITY,
    CONF_SATELLITE_ENTITY, CONF_MANAGEMENT_MODE,
    MANAGEMENT_MANAGED, MANAGEMENT_BLUEPRINTS, MANAGEMENT_NEITHER,
    NUM_BANKS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "switch", "text", "binary_sensor", "light", "select"]


def _make_pivot_dumper():
    """YAML dumper that single-quotes strings containing Jinja2 templates."""
    import yaml

    class PivotDumper(yaml.Dumper):
        pass

    def _str_representer(dumper, data):
        if any(c in data for c in ("{{", "}}", "\n", ": ")):
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    PivotDumper.add_representer(str, _str_representer)
    return PivotDumper


_PivotDumper = _make_pivot_dumper()


# ---------------------------------------------------------------------------
# Entry setup / teardown
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pivot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]

    # Set up internal listeners for bank control and bank sync
    unsubs = _setup_bank_control_listener(hass, entry)
    hass.data[DOMAIN][entry.entry_id + "_unsub"] = unsubs

    # Apply any bank entity values stored during initial setup
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    for i in range(4):
        key = f"bank_{i}_entity"
        value = entry.data.get(key, "")
        if value:
            from .const import entity_id as make_entity_id
            text_eid = make_entity_id("text", suffix, key)
            async def _write_bank(eid=text_eid, val=value):
                try:
                    await hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": eid, "value": val},
                        blocking=False,
                    )
                except Exception:
                    pass
            hass.async_create_task(_write_bank())

    # Zero bank values for passive domains on startup so the firmware cache
    # is correct even if HA restarted while a passive entity was assigned.
    _PASSIVE_DOMAINS_STARTUP = {"scene", "script", "switch", "input_boolean"}
    for _i in range(NUM_BANKS):
        _text_eid = f"text.{suffix}_bank_{_i}_entity"
        _value_eid = f"number.{suffix}_bank_{_i}_value"

        async def _zero_if_passive(t_eid=_text_eid, v_eid=_value_eid) -> None:
            text_state = hass.states.get(t_eid)
            if text_state is None or text_state.state in ("", "unknown", "unavailable"):
                return
            bank_entity = text_state.state
            if "." not in bank_entity:
                return
            if bank_entity.split(".")[0] in _PASSIVE_DOMAINS_STARTUP:
                try:
                    await hass.services.async_call(
                        "number", "set_value",
                        {"entity_id": v_eid, "value": 0},
                        blocking=False,
                    )
                except Exception:
                    pass

        hass.async_create_task(_zero_if_passive())

    # Set up mirror light listeners — watches assigned lights and mirror switches,
    # writes hex colour to the bank colour text entity when mirror is enabled
    unsubs_mirror = _setup_mirror_listeners(hass, entry)
    hass.data[DOMAIN][entry.entry_id + "_unsub_mirror"] = unsubs_mirror

    management_mode = (
        entry.options.get(CONF_MANAGEMENT_MODE)
        or entry.data.get(CONF_MANAGEMENT_MODE)
        or MANAGEMENT_MANAGED
    )

    # Detect if mode has changed from managed to something else — clean up files
    prev_mode = hass.data[DOMAIN].get(entry.entry_id + "_prev_mode")
    if prev_mode == MANAGEMENT_MANAGED and management_mode != MANAGEMENT_MANAGED:
        _LOGGER.info("Pivot: mode changed from managed to %s — cleaning up files", management_mode)
        await _cleanup_managed_files(hass, entry)
    hass.data[DOMAIN][entry.entry_id + "_prev_mode"] = management_mode

    if management_mode == MANAGEMENT_MANAGED:
        await _write_bank_toggle_script(hass, entry)
        await _write_announcements_automation(hass, entry)
    elif management_mode == MANAGEMENT_BLUEPRINTS:
        await _install_blueprints(hass, entry)
    # MANAGEMENT_NEITHER: do nothing

    _LOGGER.info("Pivot: set up '%s' (suffix: %s, mode: %s)", friendly_name, suffix, management_mode)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Pivot config entry."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]

    # Cancel state change listeners
    for unsub in hass.data[DOMAIN].pop(entry.entry_id + "_unsub", []):
        unsub()

    # Cancel mirror listeners
    for unsub in hass.data[DOMAIN].pop(entry.entry_id + "_unsub_mirror", []):
        unsub()

    management_mode = (
        entry.options.get(CONF_MANAGEMENT_MODE)
        or entry.data.get(CONF_MANAGEMENT_MODE)
        or MANAGEMENT_MANAGED
    )

    if management_mode == MANAGEMENT_MANAGED:
        await _remove_bank_toggle_script(hass, entry)
        await _remove_announcements_automation(hass, entry)
    # Blueprints and Neither: nothing to clean up on unload

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok



# ---------------------------------------------------------------------------
# Mirror light colour listeners
#
# For each bank, if switch.{suffix}_bank_N_mirror_light is on and the bank's
# assigned entity is an RGB light that is on, write its colour as hex to
# text.{suffix}_bank_N_color so the firmware picks it up via the existing
# ha_bank_color_N text sensor sync.
# ---------------------------------------------------------------------------

def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _setup_mirror_listeners(hass, entry) -> list:
    """Register state listeners for mirror light feature. Returns unsub list."""
    from homeassistant.helpers.event import async_track_state_change_event
    from .const import NUM_BANKS, entity_id as make_entity_id

    suffix = entry.data[CONF_DEVICE_SUFFIX]
    unsubs = []

    def _apply_mirror_for_bank(bank: int) -> None:
        """Check mirror state for one bank and write hex to colour text entity."""
        from .const import BANK_COLORS_HEX
        mirror_switch_id = make_entity_id("switch", suffix, f"bank_{bank}_mirror_light")
        bank_entity_id = make_entity_id("text", suffix, f"bank_{bank}_entity")
        colour_text_id = make_entity_id("text", suffix, f"bank_{bank}_color")
        configured_text_id = make_entity_id("text", suffix, f"bank_{bank}_configured_color")

        # Always compute the user's configured colour from the colour picker light.
        # Write it to bank_N_configured_color regardless of mirror state — this entity
        # is never overwritten by the mirror listener, so the firmware can always read
        # the user's chosen colour from it (used for Bank Indicator identity colours).
        colour_light_id = make_entity_id("light", suffix, f"bank_{bank}_color_light")
        colour_light_state = hass.states.get(colour_light_id)
        rgb = colour_light_state.attributes.get("rgb_color") if colour_light_state else None
        if rgb and len(rgb) == 3:
            configured_hex = _rgb_to_hex(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        else:
            configured_hex = BANK_COLORS_HEX[bank]
        current_configured = hass.states.get(configured_text_id)
        if not current_configured or current_configured.state.upper() != configured_hex.upper():
            hass.async_create_task(
                hass.services.async_call(
                    "text", "set_value",
                    {"entity_id": configured_text_id, "value": configured_hex},
                    blocking=False,
                )
            )

        mirror_state = hass.states.get(mirror_switch_id)
        if not mirror_state or mirror_state.state != "on":
            # Mirror turned off — restore the configured colour to the display entity too
            current = hass.states.get(colour_text_id)
            if not current or current.state.upper() != configured_hex.upper():
                _LOGGER.debug("Pivot mirror: bank %d mirror off, restoring user colour %s", bank, configured_hex)
                hass.async_create_task(
                    hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": colour_text_id, "value": configured_hex},
                        blocking=False,
                    )
                )
            return

        bank_entity_state = hass.states.get(bank_entity_id)
        if not bank_entity_state or bank_entity_state.state in ("", "unknown", "unavailable"):
            return  # no entity assigned

        assigned = bank_entity_state.state
        if not assigned.startswith("light."):
            return  # not a light

        light_state = hass.states.get(assigned)
        if not light_state or light_state.state != "on":
            return  # light is off — leave bank colour as-is

        rgb = light_state.attributes.get("rgb_color")
        if not rgb or len(rgb) != 3:
            return  # no RGB colour available

        hex_colour = _rgb_to_hex(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        # Check if colour text entity already has this value to avoid loops
        current = hass.states.get(colour_text_id)
        if current and current.state.upper() == hex_colour.upper():
            return

        _LOGGER.debug("Pivot mirror: bank %d writing %s to %s", bank, hex_colour, colour_text_id)
        hass.async_create_task(
            hass.services.async_call(
                "text", "set_value",
                {"entity_id": colour_text_id, "value": hex_colour},
                blocking=False,
            )
        )

    @callback
    def _on_any_change(event) -> None:
        """Called when any watched entity changes — recheck all banks."""
        for bank in range(NUM_BANKS):
            _apply_mirror_for_bank(bank)

    # Watch all mirror switches, bank entity text sensors, and we'll add
    # light watchers dynamically — for simplicity watch all light state changes
    # (cheap since it only triggers on actual changes)
    watch_entities = []
    for bank in range(NUM_BANKS):
        watch_entities.append(make_entity_id("switch", suffix, f"bank_{bank}_mirror_light"))
        watch_entities.append(make_entity_id("text", suffix, f"bank_{bank}_entity"))

    unsubs.append(
        async_track_state_change_event(hass, watch_entities, _on_any_change)
    )

    # Also watch any light entities currently assigned
    def _get_assigned_lights() -> list[str]:
        lights = []
        for bank in range(NUM_BANKS):
            bank_entity_id = make_entity_id("text", suffix, f"bank_{bank}_entity")
            state = hass.states.get(bank_entity_id)
            if state and state.state.startswith("light."):
                lights.append(state.state)
        return lights

    # Initial check on setup
    for bank in range(NUM_BANKS):
        _apply_mirror_for_bank(bank)

    # Register a listener that re-builds light watchers when bank assignments change
    _light_unsubs = []

    def _register_light_watchers() -> None:
        for u in _light_unsubs:
            u()
        _light_unsubs.clear()
        lights = _get_assigned_lights()
        if lights:
            _light_unsubs.append(
                async_track_state_change_event(hass, lights, _on_any_change)
            )

    @callback
    def _on_bank_entity_change(event) -> None:
        _register_light_watchers()
        _on_any_change(event)

    bank_entity_ids = [
        make_entity_id("text", suffix, f"bank_{bank}_entity")
        for bank in range(NUM_BANKS)
    ]
    unsubs.append(
        async_track_state_change_event(hass, bank_entity_ids, _on_bank_entity_change)
    )

    _register_light_watchers()
    # Add light_unsubs cleanup to main unsubs list via wrapper
    unsubs.append(lambda: [u() for u in _light_unsubs])

    return unsubs

# ---------------------------------------------------------------------------
# Bank control listener
#
# Two triggers handled internally:
#
# 1. Knob turn -- number.{suffix}_bank_X_value changes
#    -> read assigned entity from text.{suffix}_bank_X_entity
#    -> call the appropriate service to apply the value
#
# 2. Bank switch -- number.{suffix}_active_bank changes
#    -> read the newly active bank's assigned entity
#    -> read that entity's current state
#    -> sync the value back to number.{suffix}_bank_X_value
#    so the knob always starts from the real current value
# ---------------------------------------------------------------------------

def _setup_bank_control_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> list:
    """Register state change listeners. Returns list of unsubscribe callbacks."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]

    bank_value_entity_ids = [
        f"number.{suffix}_bank_{bank}_value" for bank in range(NUM_BANKS)
    ]
    active_bank_entity_id = f"number.{suffix}_active_bank"

    @callback
    def _on_bank_value_changed(event) -> None:
        """Apply bank value to the assigned entity when knob is turned."""
        changed_entity_id = event.data.get("entity_id", "")
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state in ("unknown", "unavailable", ""):
            return
        # Ignore if value hasn't actually changed
        if old_state is not None and old_state.state == new_state.state:
            return

        # Identify which bank changed
        bank_idx = None
        for bank in range(NUM_BANKS):
            if changed_entity_id == f"number.{suffix}_bank_{bank}_value":
                bank_idx = bank
                break
        if bank_idx is None:
            return

        # Only act when control mode is active
        control_mode_state = hass.states.get(f"switch.{suffix}_control_mode")
        if control_mode_state is None or control_mode_state.state != "on":
            return

        # Only act when this bank is the active one
        active_bank_state = hass.states.get(active_bank_entity_id)
        if active_bank_state is None:
            return
        try:
            active_bank_idx = int(float(active_bank_state.state)) - 1
        except ValueError:
            return
        if active_bank_idx != bank_idx:
            return

        # Look up assigned entity
        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        if text_state is None or text_state.state in ("", "unknown", "unavailable"):
            return

        bank_entity = text_state.state

        # Timer bank: map knob value (0-100) to timer_duration when idle
        if bank_entity == "timer":
            # Only respond to genuine device pushes (physical knob turns).
            # Automation/blueprint service calls carry a non-None context.parent_id;
            # skip those so the alert loop's gauge flashing and cancel resets
            # don't trigger spurious duration announcements.
            if new_state.context.parent_id is not None:
                return
            timer_state_id = f"select.{suffix}_timer_state"
            timer_st = hass.states.get(timer_state_id)
            if timer_st is None or timer_st.state != "idle":
                return  # Knob does nothing while running/paused
            duration_eid = f"number.{suffix}_timer_duration"
            dur_st = hass.states.get(duration_eid)
            if dur_st is None:
                return
            try:
                min_val = float(dur_st.attributes.get("min", 1))
                max_val = float(dur_st.attributes.get("max", 120))
                knob_val = float(new_state.state)
                duration = round(min_val + (knob_val / 100.0) * (max_val - min_val))
                duration = max(int(min_val), min(int(max_val), max(1, duration)))
            except (ValueError, TypeError):
                return
            hass.async_create_task(
                hass.services.async_call(
                    "number", "set_value",
                    {"entity_id": duration_eid, "value": duration},
                    blocking=False,
                )
            )
            hass.bus.async_fire(
                "pivot_timer_duration_set",
                {"suffix": suffix, "bank": bank_idx + 1, "duration": duration},
            )
            return

        if "." not in bank_entity:
            return

        domain = bank_entity.split(".")[0]

        # Skip passive domains -- knob does nothing for scenes/scripts/switches
        if domain in ("scene", "script", "switch", "input_boolean"):
            return

        try:
            value = float(new_state.state)
        except ValueError:
            return

        # Stamp cooldown so incoming entity state changes (e.g. light
        # transition intermediate values) don't sync back and create a loop.
        _entity_apply_cooldown[bank_idx] = time.monotonic()
        hass.async_create_task(
            _apply_value_to_entity(hass, domain, bank_entity, value)
        )

        # Fire event for user automations
        try:
            old_value = float(old_state.state) if old_state else value
        except ValueError:
            old_value = value
        hass.bus.async_fire(
            "pivot_knob_turn",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,  # 1-based
                "bank_entity": bank_entity,
                "value": value,
                "delta": round(value - old_value, 1),
            },
        )

    @callback
    def _on_active_bank_changed(event) -> None:
        """Sync bank value FROM entity state when user switches banks."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state in ("unknown", "unavailable", ""):
            return
        if old_state is not None and old_state.state == new_state.state:
            return

        try:
            bank_idx = int(float(new_state.state)) - 1  # 1-based -> 0-based
        except ValueError:
            return

        if not 0 <= bank_idx < NUM_BANKS:
            return

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        if text_state is None or text_state.state in ("", "unknown", "unavailable"):
            return

        bank_entity = text_state.state

        # Timer bank: sync current duration to gauge when idle (running handled by gauge_sync)
        if bank_entity == "timer":
            timer_state_id = f"select.{suffix}_timer_state"
            timer_st = hass.states.get(timer_state_id)
            if timer_st is None or timer_st.state != "idle":
                return
            duration_eid = f"number.{suffix}_timer_duration"
            dur_st = hass.states.get(duration_eid)
            if dur_st is None:
                return
            try:
                min_val = float(dur_st.attributes.get("min", 1))
                max_val = float(dur_st.attributes.get("max", 120))
                raw = float(dur_st.state)
                synced = round((raw - min_val) / (max_val - min_val) * 100) if max_val != min_val else 0
                synced = max(0, min(100, synced))
            except (ValueError, TypeError):
                return
            value_entity_id = f"number.{suffix}_bank_{bank_idx}_value"
            hass.async_create_task(
                hass.services.async_call(
                    "number", "set_value",
                    {"entity_id": value_entity_id, "value": synced},
                    blocking=False,
                )
            )
            return

        if "." not in bank_entity:
            return

        domain = bank_entity.split(".")[0]
        value_entity_id = f"number.{suffix}_bank_{bank_idx}_value"

        # Passive banks (scene/script) have no controllable value — zero the gauge
        if domain in ("scene", "script", "switch", "input_boolean"):
            hass.async_create_task(
                hass.services.async_call(
                    "number", "set_value",
                    {"entity_id": value_entity_id, "value": 0},
                    blocking=False,
                )
            )
            return

        hass.async_create_task(
            _sync_value_from_entity(hass, domain, bank_entity, value_entity_id)
        )

    # ── Live entity sync ────────────────────────────────────────────────────
    # Keeps the LED gauge in sync when an assigned entity is changed externally
    # (e.g. voice command, another dashboard, or a physical switch).
    #
    # _entity_apply_cooldown: monotonic timestamp of the last time Pivot
    # applied a value to each bank's entity via _on_bank_value_changed.
    # Incoming entity state changes are ignored for _SYNC_COOLDOWN_SECS after
    # a Pivot-initiated apply, which covers the transition period during which
    # the light reports intermediate brightness values. Without this, each
    # intermediate value would trigger a sync that writes back to the number,
    # which fires _on_bank_value_changed again, causing an oscillation loop.
    _entity_apply_cooldown: dict = {}  # bank_idx -> time.monotonic() of last apply
    _SYNC_COOLDOWN_SECS = 2.0

    @callback
    def _on_assigned_entity_changed(event) -> None:
        """Sync bank value when an assigned entity changes externally."""
        changed_entity_id = event.data.get("entity_id", "")
        new_state = event.data.get("new_state")

        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return

        for bank in range(NUM_BANKS):
            text_state = hass.states.get(f"text.{suffix}_bank_{bank}_entity")
            if text_state is None or text_state.state != changed_entity_id:
                continue
            domain = changed_entity_id.split(".")[0]
            if domain not in ("light", "fan", "climate", "media_player", "cover", "input_number", "number"):
                continue

            # Skip if Pivot just applied a value to this entity — the entity
            # is still transitioning and these are not external changes.
            if time.monotonic() - _entity_apply_cooldown.get(bank, 0) < _SYNC_COOLDOWN_SECS:
                continue

            value_entity_id = f"number.{suffix}_bank_{bank}_value"
            hass.async_create_task(
                _sync_value_from_entity(hass, domain, changed_entity_id, value_entity_id)
            )

    _assigned_entity_unsubs: list = []

    def _register_assigned_entity_watchers() -> None:
        """(Re-)register state watchers for all currently assigned entities."""
        for u in _assigned_entity_unsubs:
            u()
        _assigned_entity_unsubs.clear()
        entities = []
        for bank in range(NUM_BANKS):
            text_state = hass.states.get(f"text.{suffix}_bank_{bank}_entity")
            if text_state and text_state.state and "." in text_state.state:
                entities.append(text_state.state)
        if entities:
            _assigned_entity_unsubs.append(
                async_track_state_change_event(hass, entities, _on_assigned_entity_changed)
            )

    @callback
    def _on_bank_assignment_changed(event) -> None:
        """Re-register entity watchers when a bank's assigned entity changes."""
        _register_assigned_entity_watchers()

        # If the active bank was just reassigned to a passive entity, zero the gauge
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("", "unknown", "unavailable"):
            return
        changed_entity_text_id = event.data.get("entity_id", "")
        bank_idx = None
        for bank in range(NUM_BANKS):
            if changed_entity_text_id == f"text.{suffix}_bank_{bank}_entity":
                bank_idx = bank
                break
        if bank_idx is None:
            return
        active_bank_state = hass.states.get(active_bank_entity_id)
        if active_bank_state is None:
            return
        try:
            active_bank_idx = int(float(active_bank_state.state)) - 1
        except ValueError:
            return
        if active_bank_idx != bank_idx:
            return
        bank_entity = new_state.state
        if "." not in bank_entity:
            return
        domain = bank_entity.split(".")[0]
        if domain in ("scene", "script", "switch", "input_boolean"):
            value_entity_id = f"number.{suffix}_bank_{bank_idx}_value"
            hass.async_create_task(
                hass.services.async_call(
                    "number", "set_value",
                    {"entity_id": value_entity_id, "value": 0},
                    blocking=False,
                )
            )

    _register_assigned_entity_watchers()

    unsub_values = async_track_state_change_event(
        hass, bank_value_entity_ids, _on_bank_value_changed
    )
    unsub_active = async_track_state_change_event(
        hass, [active_bank_entity_id], _on_active_bank_changed
    )
    unsub_assignments = async_track_state_change_event(
        hass,
        [f"text.{suffix}_bank_{bank}_entity" for bank in range(NUM_BANKS)],
        _on_bank_assignment_changed,
    )

    # Button event listener — fires pivot_button_press for user automations
    unsub_button = _setup_button_event_listener(hass, entry)

    # Bank-toggle listener — fires single_press (with dedup so reflashed firmware
    # and the script path never both fire for the same physical press)
    unsub_bank_toggle = _setup_bank_toggle_listener(hass, entry)

    return (
        [unsub_values, unsub_active, unsub_assignments]
        + ([unsub_button] if unsub_button else [])
        + [unsub_bank_toggle]
        + [lambda: [u() for u in _assigned_entity_unsubs]]
    )


# ---------------------------------------------------------------------------
# Button event listener — fires pivot_button_press for user automations
# ---------------------------------------------------------------------------

def _setup_button_event_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Listen for VPE button press events and fire pivot_button_press on the HA bus."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    device_id = entry.data.get(CONF_DEVICE_ID)

    if not device_id:
        return None

    button_entity_id = _get_button_event_entity(hass, device_id)
    if not button_entity_id:
        _LOGGER.debug("Pivot: no button event entity found for %s — pivot_button_press will not fire", suffix)
        return None

    @callback
    def _on_button_press(event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        press_type = new_state.attributes.get("event_type")
        if not press_type:
            return

        # Resolve active bank and assigned entity
        active_bank_state = hass.states.get(f"number.{suffix}_active_bank")
        try:
            bank_idx = int(float(active_bank_state.state)) - 1 if active_bank_state else 0
        except ValueError:
            bank_idx = 0

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        bank_entity = (
            text_state.state
            if text_state and text_state.state not in ("", "unknown", "unavailable")
            else ""
        )

        control_mode_state = hass.states.get(f"switch.{suffix}_control_mode")
        control_mode = control_mode_state.state == "on" if control_mode_state else False

        # Record timestamp so the bank_toggle script listener can skip its
        # duplicate when the firmware already fired single_press via button_press_event.
        if press_type == "single_press":
            import time as _time
            hass.data[DOMAIN][entry.entry_id + "_last_single_press"] = _time.monotonic()

        hass.bus.async_fire(
            "pivot_button_press",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,  # 1-based
                "bank_entity": bank_entity,
                "press_type": press_type,
                "control_mode": control_mode,
            },
        )

    return async_track_state_change_event(hass, [button_entity_id], _on_button_press)


# ---------------------------------------------------------------------------
# Bank-toggle script listener — fires single_press when not already fired
# by the firmware via button_press_event (deduplication for reflashed firmware)
# ---------------------------------------------------------------------------

def _setup_bank_toggle_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Fire pivot_button_press for single_press by watching the bank-toggle script.

    On pre-reflash firmware the bank-toggle script is the only source of
    single_press events, so we fire here unconditionally (after a 3-second
    dedup window).  On post-reflash firmware the button_press_event entity
    already fired single_press via _on_button_press; the timestamp check
    prevents a second event reaching automations 2-3 seconds later when the
    HA API call to run the script eventually completes.
    """
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    script_entity_id = f"script.{suffix}_bank_toggle"
    _DEDUP_WINDOW = 3.0  # seconds

    @callback
    def _on_bank_toggle_start(event) -> None:
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        # Only act on the off → on transition (script just started).
        if new_state is None or new_state.state != "on":
            return
        if old_state is not None and old_state.state == "on":
            return  # was already running (queued instance), not a new press

        import time as _time
        now = _time.monotonic()
        last = hass.data[DOMAIN].get(entry.entry_id + "_last_single_press", 0.0)
        if now - last < _DEDUP_WINDOW:
            _LOGGER.debug(
                "Pivot: suppressing duplicate single_press for %s "
                "(firmware already fired %.1fs ago)",
                suffix, now - last,
            )
            return

        hass.data[DOMAIN][entry.entry_id + "_last_single_press"] = now

        active_bank_state = hass.states.get(f"number.{suffix}_active_bank")
        try:
            bank_idx = int(float(active_bank_state.state)) - 1 if active_bank_state else 0
        except (ValueError, AttributeError):
            bank_idx = 0

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        bank_entity = (
            text_state.state
            if text_state and text_state.state not in ("", "unknown", "unavailable")
            else ""
        )

        control_mode_state = hass.states.get(f"switch.{suffix}_control_mode")
        control_mode = control_mode_state.state == "on" if control_mode_state else False

        hass.bus.async_fire(
            "pivot_button_press",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,
                "bank_entity": bank_entity,
                "press_type": "single_press",
                "control_mode": control_mode,
            },
        )

    return async_track_state_change_event(hass, [script_entity_id], _on_bank_toggle_start)


# ---------------------------------------------------------------------------
# Helper: apply 0-100 value to an entity
# ---------------------------------------------------------------------------

async def _apply_value_to_entity(
    hass: HomeAssistant, domain: str, entity_id: str, value: float
) -> None:
    """Call the appropriate service to apply a 0-100 value to an entity."""
    import math
    if math.isnan(value) or math.isinf(value):
        return
    value = max(0.0, min(100.0, value))
    if domain == "light":
        await hass.services.async_call(
            "light", "turn_on",
            {"entity_id": entity_id, "brightness_pct": round(value)},
        )
    elif domain == "fan":
        await hass.services.async_call(
            "fan", "set_percentage",
            {"entity_id": entity_id, "percentage": round(value)},
        )
    elif domain == "climate":
        # Map 0-100% -> 16-30 degrees C
        temp = round(16 + (value / 100 * 14), 1)
        await hass.services.async_call(
            "climate", "set_temperature",
            {"entity_id": entity_id, "temperature": temp},
        )
    elif domain == "media_player":
        await hass.services.async_call(
            "media_player", "volume_set",
            {"entity_id": entity_id, "volume_level": round(value / 100, 2)},
        )
    elif domain == "cover":
        await hass.services.async_call(
            "cover", "set_cover_position",
            {"entity_id": entity_id, "position": round(value)},
        )
    elif domain in ("input_number", "number"):
        state = hass.states.get(entity_id)
        if state is None:
            return
        min_val = float(state.attributes.get("min", 0))
        max_val = float(state.attributes.get("max", 100))
        scaled = min_val + (value / 100.0) * (max_val - min_val)
        scaled = round(max(min_val, min(max_val, scaled)), 2)
        await hass.services.async_call(
            domain, "set_value",
            {"entity_id": entity_id, "value": scaled},
        )


# ---------------------------------------------------------------------------
# Helper: read entity state and sync back to bank value number
# ---------------------------------------------------------------------------

async def _sync_value_from_entity(
    hass: HomeAssistant, domain: str, entity_id: str, value_entity_id: str
) -> None:
    """Read current state from an entity and sync it to the bank value number."""
    state = hass.states.get(entity_id)
    if state is None:
        return

    synced_value: float | None = None

    if domain == "light":
        brightness = state.attributes.get("brightness")
        if brightness is not None:
            synced_value = round(float(brightness) / 255 * 100)
        else:
            # Light is off - sync to 0
            synced_value = 0.0
    elif domain == "fan":
        pct = state.attributes.get("percentage")
        if pct is not None:
            synced_value = round(float(pct))
    elif domain == "climate":
        temp = state.attributes.get("temperature")
        if temp is not None:
            synced_value = round((float(temp) - 16) / 14 * 100)
    elif domain == "media_player":
        vol = state.attributes.get("volume_level")
        if vol is not None:
            synced_value = round(float(vol) * 100)
    elif domain == "cover":
        pos = state.attributes.get("current_position")
        if pos is not None:
            synced_value = round(float(pos))
    elif domain in ("input_number", "number"):
        try:
            raw = float(state.state)
        except (ValueError, TypeError):
            raw = None
        if raw is not None:
            min_val = float(state.attributes.get("min", 0))
            max_val = float(state.attributes.get("max", 100))
            if max_val != min_val:
                synced_value = round((raw - min_val) / (max_val - min_val) * 100)
            else:
                synced_value = 0.0

    _LOGGER.debug(
        "Pivot sync: entity=%s domain=%s state=%s brightness=%s vol=%s pct=%s temp=%s pos=%s -> synced_value=%s",
        entity_id, domain, state.state,
        state.attributes.get("brightness"),
        state.attributes.get("volume_level"),
        state.attributes.get("percentage"),
        state.attributes.get("temperature"),
        state.attributes.get("current_position"),
        synced_value,
    )

    if synced_value is not None:
        import math
        if math.isnan(synced_value) or math.isinf(synced_value):
            _LOGGER.warning("Pivot sync: NaN/inf synced_value for %s, skipping", entity_id)
            return
        synced_value = max(0.0, min(100.0, synced_value))
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": value_entity_id, "value": synced_value},
        )


# ---------------------------------------------------------------------------
# Blueprint installation
# ---------------------------------------------------------------------------

async def _install_blueprints(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Copy Pivot blueprint files into /config/blueprints/ and show a persistent notification."""
    import shutil

    integration_dir = os.path.dirname(__file__)
    src_automation = os.path.join(integration_dir, "..", "..", "blueprints", "automation")
    src_script = os.path.join(integration_dir, "..", "..", "blueprints", "script")

    dest_automation = hass.config.path("blueprints", "automation", "pivot")
    dest_script = hass.config.path("blueprints", "script", "pivot")

    def _copy():
        copied = []
        for src, dest in [(src_automation, dest_automation), (src_script, dest_script)]:
            src = os.path.realpath(src)
            if os.path.isdir(src):
                os.makedirs(dest, exist_ok=True)
                for fname in os.listdir(src):
                    if fname.endswith(".yaml"):
                        shutil.copy2(os.path.join(src, fname), os.path.join(dest, fname))
                        copied.append(fname)
        return copied

    copied = await hass.async_add_executor_job(_copy)
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]

    if copied:
        _LOGGER.info("Pivot: installed blueprints for %s: %s", suffix, copied)
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"Pivot — {friendly_name} Blueprints Installed",
                "message": (
                    f"Pivot blueprints have been installed for **{friendly_name}**. "
                    f"You now need to create automations from them:\n\n"
                    f"- **Pivot — Bank Control**: go to [Automations](/config/automation/dashboard) → Create → Search blueprints → Pivot\n"
                    f"- **Pivot — Announce Bank**: same as above (optional, for spoken announcements)\n"
                    f"- **Pivot — Bank Toggle**: go to [Scripts](/config/script/dashboard) → Create → Search blueprints → Pivot\n\n"
                    f"The bank toggle script **must** be given the ID `{suffix}_bank_toggle` when saving."
                ),
                "notification_id": f"pivot_blueprints_{suffix}",
            },
            blocking=False,
        )


async def _cleanup_managed_files(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove Pivot-managed files when switching away from Managed mode."""
    await _remove_bank_toggle_script(hass, entry)
    await _remove_announcements_automation(hass, entry)
    _LOGGER.info("Pivot: cleaned up managed files for %s", entry.data[CONF_DEVICE_SUFFIX])


# ---------------------------------------------------------------------------
# Bank toggle script file management
#
# The firmware calls script.turn_on with entity_id: script.{suffix}_bank_toggle
# HA's script.turn_on requires a real script entity in the script registry.
# We create it by writing to scripts.yaml in the HA config directory,
# then calling script.reload to pick it up.
# ---------------------------------------------------------------------------


async def _write_bank_toggle_script(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Write the bank toggle script to a Pivot-owned file and register it in scripts.yaml."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]
    script_key = f"{suffix}_bank_toggle"

    # The script body — written to its own file that Pivot fully owns
    script_body = {
        "alias": f"Pivot \u2014 {friendly_name} Bank Toggle",
        "description": "Auto-created by Pivot integration. Do not edit manually.",
        "icon": "mdi:knob",
        "mode": "single",
        "sequence": [
            {
                "variables": {
                    "bank": f"{{{{ (states('number.{suffix}_active_bank') | int(1)) - 1 }}}}",
                    "bank_entity": (
                        f"{{% set entities = ["
                        f"states('text.{suffix}_bank_0_entity'),"
                        f"states('text.{suffix}_bank_1_entity'),"
                        f"states('text.{suffix}_bank_2_entity'),"
                        f"states('text.{suffix}_bank_3_entity')"
                        f"] %}}"
                        f"{{{{ entities[bank] }}}}"
                    ),
                    "domain": "{{ bank_entity.split('.')[0] if '.' in bank_entity else '' }}",
                }
            },
            # pivot_button_press for single_press is now fired by the
            # _setup_bank_toggle_listener in __init__.py, which also deduplicates
            # against the firmware button_press_event path on reflashed devices.
            {
                "condition": "template",
                "value_template": "{{ bank_entity | length > 0 and bank_entity not in ('unknown', 'unavailable', '', 'timer') }}",
            },
            {
                "choose": [
                    {
                        "conditions": "{{ domain == 'scene' }}",
                        "sequence": [{"action": "scene.turn_on", "target": {"entity_id": "{{ bank_entity }}"}}],
                    },
                    {
                        "conditions": "{{ domain == 'script' }}",
                        "sequence": [{"action": "script.turn_on", "target": {"entity_id": "{{ bank_entity }}"}}],
                    },
                    {
                        "conditions": "{{ domain == 'media_player' }}",
                        "sequence": [{"action": "media_player.media_play_pause", "target": {"entity_id": "{{ bank_entity }}"}}],
                    },
                    {
                        "conditions": "{{ domain == 'cover' }}",
                        "sequence": [{"action": "cover.toggle", "target": {"entity_id": "{{ bank_entity }}"}}],
                    },
                    {
                        "conditions": "{{ domain in ('input_number', 'number') }}",
                        "sequence": [],
                    },
                ],
                "default": [
                    {"action": "homeassistant.toggle", "target": {"entity_id": "{{ bank_entity }}"}}
                ],
            },
            {"delay": {"milliseconds": 150}},
            {
                "variables": {
                    "new_brightness": f"{{{{ state_attr(bank_entity, 'brightness') }}}}",
                    "new_volume": f"{{{{ state_attr(bank_entity, 'volume_level') }}}}",
                    "new_percentage": f"{{{{ state_attr(bank_entity, 'percentage') }}}}",
                    "new_temperature": f"{{{{ state_attr(bank_entity, 'temperature') }}}}",
                    "new_position": f"{{{{ state_attr(bank_entity, 'current_position') }}}}",
                    "entity_state": f"{{{{ states(bank_entity) }}}}",
                    "number_min": f"{{{{ state_attr(bank_entity, 'min') | float(0) }}}}",
                    "number_max": f"{{{{ state_attr(bank_entity, 'max') | float(100) }}}}",
                }
            },
            {
                "choose": [
                    {
                        "conditions": "{{ domain == 'light' }}",
                        "sequence": [{
                            "action": "number.set_value",
                            "target": {"entity_id": f"number.{suffix}_bank_{{{{ bank }}}}_value"},
                            "data": {"value": "{{ (new_brightness | float(0) / 255 * 100) | round(0) | int if new_brightness not in (None, 'None') else 0 }}"},
                        }],
                    },
                    {
                        "conditions": "{{ domain == 'media_player' }}",
                        "sequence": [{
                            "action": "number.set_value",
                            "target": {"entity_id": f"number.{suffix}_bank_{{{{ bank }}}}_value"},
                            "data": {"value": "{{ (new_volume | float(0) * 100) | round(0) | int }}"},
                        }],
                    },
                    {
                        "conditions": "{{ domain == 'fan' }}",
                        "sequence": [{
                            "action": "number.set_value",
                            "target": {"entity_id": f"number.{suffix}_bank_{{{{ bank }}}}_value"},
                            "data": {"value": "{{ new_percentage | float(0) | round(0) | int }}"},
                        }],
                    },
                    {
                        "conditions": "{{ domain == 'cover' }}",
                        "sequence": [{
                            "action": "number.set_value",
                            "target": {"entity_id": f"number.{suffix}_bank_{{{{ bank }}}}_value"},
                            "data": {"value": "{{ new_position | float(0) | round(0) | int }}"},
                        }],
                    },
                    {
                        "conditions": "{{ domain in ('input_number', 'number') }}",
                        "sequence": [{
                            "action": "number.set_value",
                            "target": {"entity_id": f"number.{suffix}_bank_{{{{ bank }}}}_value"},
                            "data": {"value": "{{ (((entity_state | float(0)) - number_min) / ((number_max - number_min) if number_max != number_min else 1) * 100) | round(0) | int }}"},
                        }],
                    },
                ],
            },
        ],
    }

    pivot_script_path = hass.config.path(f"pivot_{script_key}.yaml")
    scripts_path = hass.config.path("scripts.yaml")
    include_line = f"{script_key}: !include pivot_{script_key}.yaml"

    def _write():
        import shutil, datetime

        # 1. Validate our content before writing
        test_output = _yaml.dump(script_body, Dumper=_PivotDumper, default_flow_style=False, allow_unicode=True)
        try:
            _yaml.safe_load(test_output)
        except Exception as e:
            _LOGGER.error("Pivot: generated script YAML is invalid, aborting write: %s", e)
            return

        # 2. Write our own file (Pivot fully owns this — safe to overwrite)
        with open(pivot_script_path, "w") as f:
            f.write(test_output)

        # 3. Add include line to scripts.yaml only if not already present
        existing_text = ""
        if os.path.exists(scripts_path):
            with open(scripts_path, "r") as f:
                existing_text = f.read()
        if include_line not in existing_text:
            # Back up scripts.yaml before touching it
            if os.path.exists(scripts_path):
                backup_path = scripts_path + f".pivot_backup"
                shutil.copy2(scripts_path, backup_path)
                _LOGGER.info("Pivot: backed up scripts.yaml to %s", backup_path)
            with open(scripts_path, "a") as f:
                f.write(f"\n# Auto-added by Pivot integration — do not edit\n")
                f.write(f"{include_line}\n")

    await hass.async_add_executor_job(_write)

    try:
        await hass.services.async_call("script", "reload", blocking=True)
        _LOGGER.info("Pivot: created script.%s", script_key)
    except Exception as e:
        _LOGGER.warning("Pivot: could not reload scripts: %s", e)


async def _remove_bank_toggle_script(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove Pivot script files and reload."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    script_key = f"{suffix}_bank_toggle"
    pivot_script_path = hass.config.path(f"pivot_{script_key}.yaml")

    def _remove():
        # Delete our owned file
        if os.path.exists(pivot_script_path):
            os.remove(pivot_script_path)
        # Remove the include line from scripts.yaml
        scripts_path = hass.config.path("scripts.yaml")
        if not os.path.exists(scripts_path):
            return
        with open(scripts_path, "r") as f:
            lines = f.readlines()
        include_marker = f"pivot_{script_key}.yaml"
        new_lines = [l for l in lines if include_marker not in l and "Auto-added by Pivot" not in l]
        if len(new_lines) != len(lines):
            with open(scripts_path, "w") as f:
                f.writelines(new_lines)

    await hass.async_add_executor_job(_remove)

    try:
        await hass.services.async_call("script", "reload", blocking=True)
        _LOGGER.info("Pivot: removed script.%s", script_key)
    except Exception as e:
        _LOGGER.warning("Pivot: could not reload scripts after removal: %s", e)



# Written to automations.yaml if announcements is enabled and TTS/media player
# are configured. Removed on unload or when announcements is disabled.
# ---------------------------------------------------------------------------


def _get_button_event_entity(hass: HomeAssistant, device_id: str) -> str | None:
    """Find the button press event entity for a VPE device."""
    from homeassistant.helpers import entity_registry as er
    ent_reg = er.async_get(hass)
    for entity in ent_reg.entities.values():
        if (entity.device_id == device_id
                and entity.domain == "event"
                and "button" in (entity.entity_id or "").lower()):
            return entity.entity_id
    return None


async def _write_announcements_automation(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Write the announcements automation to automations.yaml if configured."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]
    device_id = entry.data.get(CONF_DEVICE_ID)

    # Get tts/media player from options first, then data
    tts_entity = (
        entry.options.get(CONF_TTS_ENTITY)
        or entry.data.get(CONF_TTS_ENTITY)
        or ""
    )
    media_player_entity = (
        entry.options.get(CONF_MEDIA_PLAYER_ENTITY)
        or entry.data.get(CONF_MEDIA_PLAYER_ENTITY)
        or ""
    )
    announcements = (
        entry.options.get(CONF_ANNOUNCEMENTS)
        if CONF_ANNOUNCEMENTS in entry.options
        else entry.data.get(CONF_ANNOUNCEMENTS, True)
    )

    automation_key = f"pivot_{suffix}_announcements"

    # Remove existing automation first
    await _remove_announcements_automation(hass, entry)

    # Only create if announcements is enabled and tts/media player are configured
    if not announcements or not tts_entity or not media_player_entity:
        _LOGGER.debug(
            "Pivot: skipping announcements automation for %s "
            "(announcements=%s tts=%s media_player=%s)",
            suffix, announcements, tts_entity, media_player_entity
        )
        return

    # Try to find the button event entity
    button_event_entity = None
    if device_id:
        button_event_entity = _get_button_event_entity(hass, device_id)
        if button_event_entity:
            _LOGGER.debug("Pivot: found button event entity %s", button_event_entity)
        else:
            _LOGGER.warning(
                "Pivot: could not find button press event entity for device %s — "
                "triple press trigger will be omitted", device_id
            )

    triggers = [
        {
            "trigger": "state",
            "entity_id": f"number.{suffix}_active_bank",
            "id": "bank_change",
        },
        {
            "trigger": "state",
            "entity_id": f"switch.{suffix}_control_mode",
            "id": "control_mode_change",
        },
    ]
    if button_event_entity:
        triggers.append({
            "trigger": "state",
            "entity_id": button_event_entity,
            "id": "button_press",
        })

    # Shared variables block — resolves active bank entity name
    bank_variables = {
        "control_mode_on": f"{{{{ is_state('switch.{suffix}_control_mode', 'on') }}}}",
        "bank": f"{{{{ states('number.{suffix}_active_bank') | int(1) - 1 }}}}",
        "bank_entity": (
            f"{{% set entities = ["
            f"states('text.{suffix}_bank_0_entity'),"
            f"states('text.{suffix}_bank_1_entity'),"
            f"states('text.{suffix}_bank_2_entity'),"
            f"states('text.{suffix}_bank_3_entity')"
            f"] %}}"
            f"{{{{ entities[bank] }}}}"
        ),
        "entity_name": "{{ state_attr(bank_entity, 'friendly_name') or bank_entity }}",
    }

    def speak(message_template: str) -> list:
        return [
            {"variables": bank_variables},
            {
                "action": "tts.speak",
                "target": {"entity_id": tts_entity},
                "data": {
                    "media_player_entity_id": media_player_entity,
                    "message": message_template,
                },
            },
        ]

    # control mode on -> "Control mode on, [entity name]"
    control_mode_on_sequence = speak("Control mode on, {{ entity_name }}")
    # control mode off -> "Control mode off"
    control_mode_off_sequence = speak("Control mode off")
    # bank change (only in control mode) -> "[entity name]"
    bank_change_sequence = speak("{{ entity_name }}")

    conditions = [
        {
            "condition": "state",
            "entity_id": f"switch.{suffix}_announcements",
            "state": "on",
        }
    ]

    choose_actions = [
        # Control mode turned on -> "Control mode on, [entity]"
        {
            "conditions": [
                {"condition": "trigger", "id": "control_mode_change"},
                {"condition": "template", "value_template": "{{ trigger.to_state.state == 'on' }}"},
            ],
            "sequence": control_mode_on_sequence,
        },
        # Control mode turned off -> "Control mode off"
        {
            "conditions": [
                {"condition": "trigger", "id": "control_mode_change"},
                {"condition": "template", "value_template": "{{ trigger.to_state.state == 'off' }}"},
            ],
            "sequence": control_mode_off_sequence,
        },
        # Bank change (only when control mode is on)
        {
            "conditions": [
                {"condition": "trigger", "id": "bank_change"},
                {"condition": "state", "entity_id": f"switch.{suffix}_control_mode", "state": "on"},
            ],
            "sequence": bank_change_sequence,
        },
    ]
    if button_event_entity:
        # Triple press in control mode -> "Control mode on, [entity]"
        # Triple press in listening mode -> "Control mode off"
        choose_actions.insert(0, {
            "conditions": [
                {"condition": "trigger", "id": "button_press"},
                {
                    "condition": "template",
                    "value_template": "{{ trigger.to_state.attributes.get('event_type') == 'triple_press' }}",
                },
            ],
            "sequence": [
                {"variables": bank_variables},
                {
                    "choose": [
                        {
                            "conditions": [{"condition": "template", "value_template": "{{ control_mode_on }}"}],
                            "sequence": [
                                {
                                    "action": "tts.speak",
                                    "target": {"entity_id": tts_entity},
                                    "data": {
                                        "media_player_entity_id": media_player_entity,
                                        "message": "{{ entity_name }}",
                                    },
                                }
                            ],
                        }
                    ],
                    "default": [
                        {
                            "action": "tts.speak",
                            "target": {"entity_id": tts_entity},
                            "data": {
                                "media_player_entity_id": media_player_entity,
                                "message": "Control mode off",
                            },
                        }
                    ],
                },
            ],
        })

    automation_config = {
        "id": automation_key,
        "alias": f"Pivot — {friendly_name} Announcements",
        "description": "Auto-created by Pivot integration. Do not edit manually.",
        "triggers": triggers,
        "conditions": conditions,
        "actions": [{"choose": choose_actions}],
        "mode": "single",
    }

    pivot_auto_path = hass.config.path(f"pivot_{automation_key}.yaml")
    automations_path = hass.config.path("automations.yaml")
    include_line = f"- !include pivot_{automation_key}.yaml"

    def _write_automation():
        import shutil

        # 1. Validate our content before writing
        test_output = _yaml.dump(automation_config, Dumper=_PivotDumper, default_flow_style=False, allow_unicode=True)
        try:
            _yaml.safe_load(test_output)
        except Exception as e:
            _LOGGER.error("Pivot: generated automation YAML is invalid, aborting write: %s", e)
            return

        # 2. Write our own file (Pivot fully owns this — safe to overwrite)
        with open(pivot_auto_path, "w") as f:
            f.write(test_output)

        # 3. Append include line to automations.yaml only if not already present
        existing_text = ""
        if os.path.exists(automations_path):
            with open(automations_path, "r") as f:
                existing_text = f.read()
        if include_line not in existing_text:
            # Back up automations.yaml before touching it
            if os.path.exists(automations_path):
                backup_path = automations_path + f".pivot_backup"
                shutil.copy2(automations_path, backup_path)
                _LOGGER.info("Pivot: backed up automations.yaml to %s", backup_path)
            with open(automations_path, "a") as f:
                f.write("\n# Auto-added by Pivot integration — do not edit\n")
                f.write(f"{include_line}\n")

    await hass.async_add_executor_job(_write_automation)

    try:
        await hass.services.async_call("automation", "reload", blocking=True)
        _LOGGER.info("Pivot: created automation %s", automation_key)
    except Exception as e:
        _LOGGER.warning("Pivot: could not reload automations: %s", e)


async def _remove_announcements_automation(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove Pivot automation file and its include line from automations.yaml."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    automation_key = f"pivot_{suffix}_announcements"
    pivot_auto_path = hass.config.path(f"pivot_{automation_key}.yaml")
    automations_path = hass.config.path("automations.yaml")

    def _remove_automation():
        # Delete our owned file
        if os.path.exists(pivot_auto_path):
            os.remove(pivot_auto_path)
        # Remove the include line from automations.yaml
        if not os.path.exists(automations_path):
            return False
        with open(automations_path, "r") as f:
            lines = f.readlines()
        include_marker = f"pivot_{automation_key}.yaml"
        new_lines = [l for l in lines if include_marker not in l and "Auto-added by Pivot" not in l]
        if len(new_lines) == len(lines):
            return False
        with open(automations_path, "w") as f:
            f.writelines(new_lines)
        return True

    removed = await hass.async_add_executor_job(_remove_automation)
    if removed:
        try:
            await hass.services.async_call("automation", "reload", blocking=True)
            _LOGGER.info("Pivot: removed automation %s", automation_key)
        except Exception as e:
            _LOGGER.warning("Pivot: could not reload automations after removal: %s", e)
