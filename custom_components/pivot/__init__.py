"""Pivot integration.

Handles all runtime logic for Pivot devices:
- Bank control: listens for bank value changes and applies them to assigned entities
- Bank sync: when active bank changes, reads entity state and syncs value back
- Bank toggle: performed natively on single_press in control mode; also fires
  pivot_button_press events for user automations
"""
from __future__ import annotations

import logging
import math
import os
import shutil
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_call_later

from .const import (
    DOMAIN, CONF_DEVICE_ID, CONF_ESPHOME_DEVICE_NAME, CONF_FRIENDLY_NAME, CONF_DEVICE_SUFFIX,
    CONF_ANNOUNCEMENTS, CONF_TTS_ENTITY, CONF_MEDIA_PLAYER_ENTITY,
    CONF_MANAGEMENT_MODE,
    MANAGEMENT_BLUEPRINTS, MANAGEMENT_NEITHER,
    NUM_BANKS, BANK_COLORS_HEX, entity_id as make_entity_id,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "switch", "text", "binary_sensor", "light", "select"]



def _sync_blueprints(hass: HomeAssistant) -> list[str]:
    """Copy blueprints from custom_components/pivot/blueprints/ → config/blueprints/automation(script)/pivot/.

    Mirrors the directory structure used by the existing _install_blueprints so
    that blueprints always land at the same paths regardless of how they were
    first installed.  Only writes files whose content has changed, and uses an
    atomic temp-file swap so a crash mid-write never leaves a corrupt blueprint.

    Returns a list of relative paths that were actually written.
    """
    integration_dir = os.path.dirname(__file__)
    updated: list[str] = []

    for domain in ("automation", "script"):
        src_dir = os.path.join(integration_dir, "blueprints", domain)
        dst_dir = hass.config.path("blueprints", domain, "pivot")

        if not os.path.isdir(src_dir):
            continue

        os.makedirs(dst_dir, exist_ok=True)

        for fname in os.listdir(src_dir):
            if not fname.endswith(".yaml"):
                continue

            src_file = os.path.join(src_dir, fname)
            dst_file = os.path.join(dst_dir, fname)

            with open(src_file, "rb") as f:
                src_bytes = f.read()

            # Skip if destination is already identical
            if os.path.exists(dst_file):
                with open(dst_file, "rb") as f:
                    if f.read() == src_bytes:
                        continue

            # Atomic write via temp file
            tmp_file = dst_file + ".pivot_tmp"
            with open(tmp_file, "wb") as f:
                f.write(src_bytes)
            shutil.move(tmp_file, dst_file)

            rel = f"{domain}/pivot/{fname}"
            _LOGGER.info("Pivot: installed/updated blueprint %s", rel)
            updated.append(rel)

    return updated


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

    # Write configured TTS and media player entity IDs to their text entities so
    # the Announce and Timer blueprints can read them without needing manual input.
    _tts = entry.options.get(CONF_TTS_ENTITY) or entry.data.get(CONF_TTS_ENTITY) or ""
    _mp = entry.options.get(CONF_MEDIA_PLAYER_ENTITY) or entry.data.get(CONF_MEDIA_PLAYER_ENTITY) or ""
    _announce_enabled = bool(
        entry.options.get(CONF_ANNOUNCEMENTS, entry.data.get(CONF_ANNOUNCEMENTS, True))
    )

    async def _write_config_text_entities() -> None:
        for _key, _val in [("tts_entity", _tts), ("media_player_entity", _mp)]:
            _eid = make_entity_id("text", suffix, _key)
            if hass.states.get(_eid) is not None:
                try:
                    await hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": _eid, "value": _val},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Pivot: could not write config text entity %s: %s", _eid, err)

    hass.async_create_task(_write_config_text_entities())

    # Debounce cancel handles for native value announcements (bank_idx -> cancel callable)
    _announce_cancels: dict[int, object] = {}
    hass.data[DOMAIN][entry.entry_id + "_announce_cancels"] = _announce_cancels

    # Set up internal listeners for bank control and bank sync
    unsubs = _setup_bank_control_listener(
        hass, entry,
        tts_entity=_tts,
        media_player=_mp,
        announce_enabled=_announce_enabled,
        announce_cancels=_announce_cancels,
    )
    hass.data[DOMAIN][entry.entry_id + "_unsub"] = unsubs

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
                except Exception as err:
                    _LOGGER.debug("Pivot: could not zero passive bank value %s: %s", v_eid, err)

        hass.async_create_task(_zero_if_passive())

    # Set up mirror light listeners — watches assigned lights and mirror switches,
    # writes hex colour to the bank colour text entity when mirror is enabled
    unsubs_mirror = _setup_mirror_listeners(hass, entry)
    hass.data[DOMAIN][entry.entry_id + "_unsub_mirror"] = unsubs_mirror

    management_mode = (
        entry.options.get(CONF_MANAGEMENT_MODE)
        or entry.data.get(CONF_MANAGEMENT_MODE)
        or MANAGEMENT_BLUEPRINTS
    )

    if management_mode == MANAGEMENT_BLUEPRINTS:
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

    # Cancel any pending value-announcement debounce timers
    for cancel in hass.data[DOMAIN].pop(entry.entry_id + "_announce_cancels", {}).values():
        cancel()

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


def _setup_mirror_listeners(hass: HomeAssistant, entry: ConfigEntry) -> list:
    """Register state listeners for mirror light feature. Returns unsub list."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    unsubs = []

    def _apply_mirror_for_bank(bank: int) -> None:
        """Check mirror state for one bank and write hex to color text entity."""
        mirror_switch_id = make_entity_id("switch", suffix, f"bank_{bank}_mirror_light")
        bank_entity_id = make_entity_id("text", suffix, f"bank_{bank}_entity")
        color_text_id = make_entity_id("text", suffix, f"bank_{bank}_color")
        configured_text_id = make_entity_id("text", suffix, f"bank_{bank}_configured_color")

        # Always compute the user's configured color from the color picker light.
        # Write it to bank_N_configured_color regardless of mirror state — this entity
        # is never overwritten by the mirror listener, so the firmware can always read
        # the user's chosen color from it (used for Bank Indicator identity colors).
        color_light_id = make_entity_id("light", suffix, f"bank_{bank}_color_light")
        color_light_state = hass.states.get(color_light_id)
        rgb = color_light_state.attributes.get("rgb_color") if color_light_state else None
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
            # Mirror turned off — restore the configured color to the display entity too
            current = hass.states.get(color_text_id)
            if not current or current.state.upper() != configured_hex.upper():
                _LOGGER.debug("Pivot mirror: bank %d mirror off, restoring user color %s", bank, configured_hex)
                hass.async_create_task(
                    hass.services.async_call(
                        "text", "set_value",
                        {"entity_id": color_text_id, "value": configured_hex},
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
            return  # light is off — leave bank color as-is

        rgb = light_state.attributes.get("rgb_color")
        if not rgb or len(rgb) != 3:
            return  # no RGB color available

        hex_color = _rgb_to_hex(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        # Check if color text entity already has this value to avoid loops
        current = hass.states.get(color_text_id)
        if current and current.state.upper() == hex_color.upper():
            return

        _LOGGER.debug("Pivot mirror: bank %d writing %s to %s", bank, hex_color, color_text_id)
        hass.async_create_task(
            hass.services.async_call(
                "text", "set_value",
                {"entity_id": color_text_id, "value": hex_color},
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
# Announcement helpers
# ---------------------------------------------------------------------------

def _format_value_announcement(hass: HomeAssistant, bank_entity: str, bank_value: float) -> str | None:
    """Build a TTS message string for a value announcement.

    Reads the current entity state at call time (post-debounce) so climate and
    cover report their actual attribute values rather than the knob percentage.
    """
    if not bank_entity or "." not in bank_entity:
        return None
    domain = bank_entity.split(".")[0]
    if domain not in ("light", "fan", "climate", "media_player", "cover", "number", "input_number"):
        return None
    entity_state = hass.states.get(bank_entity)
    if entity_state is None or entity_state.state in ("unavailable", "unknown"):
        return None
    if domain == "climate":
        temp = entity_state.attributes.get("temperature")
        if temp is None:
            return None
        return f"Temperature {round(float(temp))} degrees."
    if domain == "cover":
        pos = entity_state.attributes.get("current_position")
        if pos is None:
            return None
        return f"{round(float(pos))} percent open."
    if domain == "light":
        return f"Brightness {round(bank_value)} percent."
    if domain == "media_player":
        return f"Volume {round(bank_value)} percent."
    if domain == "fan":
        return f"Speed {round(bank_value)} percent."
    if domain in ("number", "input_number"):
        unit = entity_state.attributes.get("unit_of_measurement") or ""
        return f"Set to {entity_state.state}{' ' + unit if unit else ''}."
    return None


async def _do_tts(hass: HomeAssistant, tts_entity: str, media_player: str, message: str) -> None:
    """Call tts.speak with the given message."""
    if not tts_entity or not media_player or not message:
        return
    try:
        await hass.services.async_call(
            "tts", "speak",
            {
                "entity_id": tts_entity,
                "media_player_entity_id": media_player,
                "message": message.strip(),
            },
            blocking=False,
        )
    except Exception as err:
        _LOGGER.debug("Pivot: TTS call failed (entity=%s message=%r): %s", tts_entity, message, err)


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
    hass: HomeAssistant, entry: ConfigEntry,
    tts_entity: str = "",
    media_player: str = "",
    announce_enabled: bool = False,
    announce_cancels: dict | None = None,
) -> list:
    """Register state change listeners. Returns list of unsubscribe callbacks."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    if announce_cancels is None:
        announce_cancels = {}

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

        # Only respond to genuine device pushes (physical knob turns).
        # Bank value changes from live-entity sync (_sync_value_from_entity) and
        # bank-switch sync are issued as HA service calls, so their state change
        # carries a non-None context.parent_id. Ignoring those prevents
        # pivot_knob_turn from firing when an external source (e.g. a motion
        # trigger turning on a light) causes a sync update, and also stops the
        # value being needlessly re-applied to the entity a second time.
        if new_state.context.parent_id is not None:
            return

        # Look up assigned entity
        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        if text_state is None or text_state.state in ("", "unknown", "unavailable"):
            return

        bank_entity = text_state.state

        # Timer bank: map knob value (0-100) to timer_duration when idle
        if bank_entity == "timer":
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

        # Native value announcement — debounced 600 ms (matches blueprint behaviour).
        # Cancels and restarts on each knob turn so only the settled value is spoken.
        if announce_enabled and tts_entity and media_player and "." in bank_entity:
            ann_domain = bank_entity.split(".")[0]
            if ann_domain in ("light", "fan", "climate", "media_player", "cover", "number", "input_number"):
                ann_switch = hass.states.get(f"switch.{suffix}_bank_{bank_idx}_announce_value")
                if ann_switch and ann_switch.state == "on":
                    # Cancel any existing debounce for this bank
                    existing = announce_cancels.pop(bank_idx, None)
                    if existing:
                        existing()

                    _be = bank_entity
                    _bv = value
                    _bi = bank_idx

                    @callback
                    def _fire_value_announce(_now=None, be=_be, bv=_bv, bi=_bi):
                        announce_cancels.pop(bi, None)
                        mute = hass.states.get(f"switch.{suffix}_mute_announcements")
                        if mute and mute.state == "on":
                            return
                        msg = _format_value_announcement(hass, be, bv)
                        if msg:
                            hass.async_create_task(_do_tts(hass, tts_entity, media_player, msg))

                    announce_cancels[bank_idx] = async_call_later(hass, 0.6, _fire_value_announce)

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
        bank_entity = (
            text_state.state
            if text_state and text_state.state not in ("", "unknown", "unavailable")
            else ""
        )

        # Fire event for blueprints and user automations
        hass.bus.async_fire(
            "pivot_bank_changed",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,  # 1-based
                "bank_entity": bank_entity,
            },
        )

        # Cancel any pending value-announcement debounces on bank switch
        # (mirrors mode: restart behaviour in the blueprint)
        for _bi, _cancel in list(announce_cancels.items()):
            announce_cancels.pop(_bi, None)
            _cancel()

        # Native bank change announcement
        if announce_enabled and tts_entity and media_player and bank_entity:
            _cm = hass.states.get(f"switch.{suffix}_control_mode")
            _ann = hass.states.get(f"switch.{suffix}_announcements")
            _mute = hass.states.get(f"switch.{suffix}_mute_announcements")
            if (_cm and _cm.state == "on"
                    and _ann and _ann.state == "on"
                    and not (_mute and _mute.state == "on")):
                if bank_entity == "timer":
                    _name = "Timer"
                else:
                    _es = hass.states.get(bank_entity)
                    _name = (_es.attributes.get("friendly_name") if _es else None) or bank_entity
                hass.async_create_task(_do_tts(hass, tts_entity, media_player, _name))

        if not bank_entity:
            return

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
                    context=Context(parent_id="pivot_sync"),
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

    # Button event listener — performs toggle natively and fires pivot_button_press
    unsub_button = _setup_button_event_listener(
        hass, entry,
        tts_entity=tts_entity,
        media_player=media_player,
        announce_enabled=announce_enabled,
    )

    return (
        [unsub_values, unsub_active, unsub_assignments]
        + ([unsub_button] if unsub_button else [])
        + [lambda: [u() for u in _assigned_entity_unsubs]]
    )


# ---------------------------------------------------------------------------
# Native bank toggle — called on single_press in control mode
# ---------------------------------------------------------------------------

async def _do_bank_toggle(hass: HomeAssistant, suffix: str, bank_entity: str) -> None:
    """Toggle the entity assigned to the active bank."""
    if not bank_entity or bank_entity in ("unknown", "unavailable", "timer"):
        return
    domain = bank_entity.split(".")[0] if "." in bank_entity else ""
    try:
        if domain == "scene":
            await hass.services.async_call("scene", "turn_on", {"entity_id": bank_entity})
        elif domain == "script":
            await hass.services.async_call("script", "turn_on", {"entity_id": bank_entity})
        elif domain == "media_player":
            await hass.services.async_call("media_player", "media_play_pause", {"entity_id": bank_entity})
        elif domain == "cover":
            await hass.services.async_call("cover", "toggle", {"entity_id": bank_entity})
        else:
            await hass.services.async_call("homeassistant", "toggle", {"entity_id": bank_entity})
    except Exception:
        _LOGGER.exception("Pivot: error toggling %s for %s", bank_entity, suffix)


# ---------------------------------------------------------------------------
# Button event listener — fires pivot_button_press for user automations
# ---------------------------------------------------------------------------

def _setup_button_event_listener(
    hass: HomeAssistant, entry: ConfigEntry,
    tts_entity: str = "",
    media_player: str = "",
    announce_enabled: bool = False,
) -> object | None:
    """Listen for VPE button press events and fire pivot_button_press on the HA bus."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    device_id = entry.data.get(CONF_DEVICE_ID)

    # Older config entries may not have device_id stored — look it up by ESPHome device name.
    if not device_id:
        esphome_name = entry.data.get(CONF_ESPHOME_DEVICE_NAME)
        if esphome_name:
            dev_reg = dr.async_get(hass)
            for device in dev_reg.devices.values():
                for eid in device.config_entries:
                    cfg = hass.config_entries.async_get_entry(eid)
                    if cfg and cfg.domain == "esphome":
                        host = (cfg.data.get("name") or cfg.data.get("host") or "").removesuffix(".local").strip()
                        if host == esphome_name:
                            device_id = device.id
                            break
                if device_id:
                    break
        if not device_id:
            _LOGGER.warning(
                "Pivot: no device_id for %s — button toggle will not work. "
                "Re-add the integration entry to fix this.",
                suffix,
            )
            return None

    button_entity_id = _get_button_event_entity(hass, device_id)
    if not button_entity_id:
        _LOGGER.warning(
            "Pivot: no button press event entity found for %s (device_id=%s) — "
            "button toggle will not work. Ensure the device is running Pivot firmware v0.0.15+.",
            suffix, device_id,
        )
        return None

    _LOGGER.debug("Pivot: watching %s for button presses on %s", button_entity_id, suffix)

    @callback
    def _on_button_press(event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Skip reconnect transitions — entity restores last state when the
        # ESPHome device comes back online, which would look like a real press.
        old_state = event.data.get("old_state")
        if old_state is None or old_state.state in ("unavailable", "unknown"):
            _LOGGER.debug(
                "Pivot: skipping %s button event for %s — reconnect transition "
                "(old_state=%s)",
                button_entity_id, suffix,
                old_state.state if old_state else None,
            )
            return

        press_type = new_state.attributes.get("event_type")
        if not press_type:
            _LOGGER.debug("Pivot: %s fired with no event_type — ignoring", button_entity_id)
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

        _LOGGER.debug(
            "Pivot: %s press_type=%s control_mode=%s bank=%s bank_entity=%s",
            suffix, press_type, control_mode, bank_idx + 1, bank_entity or "(none)",
        )

        # Perform toggle natively — no blueprint required.
        if press_type == "single_press" and control_mode and bank_entity:
            hass.async_create_task(_do_bank_toggle(hass, suffix, bank_entity))

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

        # Native triple press re-announcement
        if (press_type == "triple_press"
                and announce_enabled and tts_entity and media_player
                and bank_entity and "." in bank_entity):
            _ann = hass.states.get(f"switch.{suffix}_announcements")
            _mute = hass.states.get(f"switch.{suffix}_mute_announcements")
            if (_ann and _ann.state == "on"
                    and not (_mute and _mute.state == "on")):
                _es = hass.states.get(bank_entity)
                _name = (_es.attributes.get("friendly_name") if _es else None) or bank_entity
                hass.async_create_task(_do_tts(hass, tts_entity, media_player, _name))

    return async_track_state_change_event(hass, [button_entity_id], _on_button_press)


# ---------------------------------------------------------------------------
# Helper: apply 0-100 value to an entity
# ---------------------------------------------------------------------------

async def _apply_value_to_entity(
    hass: HomeAssistant, domain: str, entity_id: str, value: float
) -> None:
    """Call the appropriate service to apply a 0-100 value to an entity."""
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
        state = hass.states.get(entity_id)
        if state is None:
            return
        try:
            min_temp = float(state.attributes.get("min_temp", 16))
            max_temp = float(state.attributes.get("max_temp", 30))
            step = float(state.attributes.get("target_temp_step", 0.5))
        except (ValueError, TypeError):
            return
        if max_temp <= min_temp:
            return
        temp = min_temp + (value / 100.0) * (max_temp - min_temp)
        temp = round(round(temp / step) * step, 10)  # snap to step
        temp = round(max(min_temp, min(max_temp, temp)), 2)
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
            try:
                min_temp = float(state.attributes.get("min_temp", 16))
                max_temp = float(state.attributes.get("max_temp", 30))
            except (ValueError, TypeError):
                min_temp, max_temp = 16.0, 30.0
            if max_temp > min_temp:
                synced_value = round((float(temp) - min_temp) / (max_temp - min_temp) * 100)
            else:
                synced_value = 0.0
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
        if math.isnan(synced_value) or math.isinf(synced_value):
            _LOGGER.warning("Pivot sync: NaN/inf synced_value for %s, skipping", entity_id)
            return
        synced_value = max(0.0, min(100.0, synced_value))
        # Pass a context with a parent_id so _on_bank_value_changed's
        # parent_id guard treats this as a non-physical change and does
        # not fire pivot_knob_turn (which would trigger value announcements).
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": value_entity_id, "value": synced_value},
            context=Context(parent_id="pivot_sync"),
        )


# ---------------------------------------------------------------------------
# Blueprint installation
# ---------------------------------------------------------------------------

async def _install_blueprints(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Sync bundled blueprints and show a first-run persistent notification."""
    copied = await hass.async_add_executor_job(_sync_blueprints, hass)
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
                    f"Pivot blueprints have been installed for **{friendly_name}**.\n\n"
                    f"Button toggle works automatically — no script needed.\n\n"
                    f"**Optional automations:**\n"
                    f"Go to [Automations](/config/automation/dashboard) → Create → Search blueprints → **Pivot — Announce** "
                    f"to enable spoken announcements (requires a TTS provider).\n\n"
                    f"If you use the timer feature, also create an automation from **Pivot — Timer**."
                ),
                "notification_id": f"pivot_blueprints_{suffix}",
            },
            blocking=False,
        )



def _get_button_event_entity(hass: HomeAssistant, device_id: str) -> str | None:
    """Find the button press event entity for a VPE device.

    Matches the event entity with device_class 'button' on the ESPHome device.
    Falls back to any event-domain entity on the device if device_class is absent.
    """
    ent_reg = er.async_get(hass)
    fallback = None
    for entity in ent_reg.entities.values():
        if entity.device_id != device_id or entity.domain != "event":
            continue
        if (entity.original_device_class or entity.device_class) == "button":
            return entity.entity_id
        fallback = entity.entity_id  # any event entity on this device
    return fallback


