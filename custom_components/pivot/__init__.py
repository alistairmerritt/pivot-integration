"""Pivot integration.

Handles all runtime logic for Pivot devices:
- Bank control: listens for bank value changes and applies them to assigned entities
- Bank sync: when active bank changes, reads entity state and syncs value back
- Bank toggle: performed natively on single_press in control mode; also fires
  pivot_button_press events for user automations
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN, CONF_DEVICE_ID, CONF_ESPHOME_DEVICE_NAME, CONF_FRIENDLY_NAME, CONF_DEVICE_SUFFIX,
    CONF_TTS_ENTITY, CONF_MEDIA_PLAYER_ENTITY,
    CONF_SATELLITE_ENTITY, CONF_MANAGEMENT_MODE,
    MANAGEMENT_MANAGED, MANAGEMENT_BLUEPRINTS, MANAGEMENT_NEITHER,
    NUM_BANKS, entity_id as make_entity_id,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "switch", "text", "binary_sensor", "light", "select"]


# ---------------------------------------------------------------------------
# Locks used by the migration cleanup path (removing legacy managed-mode files).
# Kept to serialise concurrent reads of scripts.yaml / automations.yaml during
# upgrade from an older install that used Automatic (managed) mode.
# ---------------------------------------------------------------------------
_SCRIPTS_YAML_LOCK = asyncio.Lock()
_AUTOMATIONS_YAML_LOCK = asyncio.Lock()


def _strip_script_lines(lines: list[str], script_key: str) -> list[str]:
    """Strip all Pivot content for script_key from a scripts.yaml line list.

    Removes both the current ``!include`` style entries AND old inline-YAML
    blocks that older integration versions (or HA's automation editor) may
    have written directly into scripts.yaml.
    """
    marker = f"pivot_{script_key}.yaml"
    result: list[str] = []
    in_inline_block = False

    for line in lines:
        # Always drop include-style references and the auto-added comment.
        if marker in line or "Auto-added by Pivot" in line:
            in_inline_block = False
            continue

        # Detect the start of an old inline script block:
        #   ha_voice_grey_bank_toggle:
        # or
        #   ha_voice_grey_bank_toggle: {inline mapping}
        is_root_key = (
            not line[:1].isspace()
            and not line.startswith("#")
            and line.strip()
        )
        if is_root_key and line.startswith(f"{script_key}:"):
            rest = line[len(script_key) + 1 :]
            if not rest.strip() or rest[:1] in (" ", "\t"):
                in_inline_block = True
                continue

        if in_inline_block:
            # Stay in the block while lines are indented, blank, or comments.
            if line.strip() and not line[:1].isspace() and not line.startswith("#"):
                # Hit the next root-level key — end of the Pivot block.
                in_inline_block = False
                # Fall through: this line belongs to the next entry.
            else:
                continue  # Still inside the old Pivot block; skip it.

        result.append(line)

    return result


def _strip_automation_lines(lines: list[str], automation_key: str) -> list[str]:
    """Strip all Pivot content for automation_key from an automations.yaml line list.

    Removes both the current ``- !include`` style entry AND old inline
    automation blocks (written directly into automations.yaml by prior
    integration versions or when HA's automation editor "flattened" an
    include into the main file).
    """
    marker = f"{automation_key}.yaml"

    # First pass: find line-index ranges belonging to old inline Pivot automations.
    # A top-level list item in automations.yaml starts with "- " at column 0.
    skip_indices: set[int] = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Top-level list item (not a nested "  - ..." item).
        if line.startswith("- ") and not line[:2] == "-\t":
            block_start = i
            # Scan the block for our automation id.
            j = i + 1
            found = False
            while j < len(lines):
                next_line = lines[j]
                # End of this list item: next top-level "- " entry.
                if next_line.startswith("- ") and not next_line[:2] == "-\t":
                    break
                if (
                    f"id: {automation_key}" in next_line
                    or f'id: "{automation_key}"' in next_line
                    or f"id: '{automation_key}'" in next_line
                ):
                    found = True
                    break
                j += 1

            if found:
                # Mark every line in this block for removal.
                block_end = j  # exclusive; j is either EOF or the next "- " item
                for k in range(block_start, block_end):
                    skip_indices.add(k)
                i = block_end
                continue
        i += 1

    return [
        line
        for idx, line in enumerate(lines)
        if idx not in skip_indices
        and marker not in line
        and "Auto-added by Pivot" not in line
    ]


# ---------------------------------------------------------------------------
# Domain setup — runs once when the integration is first loaded
# ---------------------------------------------------------------------------

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Sync bundled blueprints into the user's config directory on every startup."""
    await hass.async_add_executor_job(_sync_blueprints, hass)
    return True


def _sync_blueprints(hass: HomeAssistant) -> list[str]:
    """Copy blueprints from custom_components/pivot/blueprints/ → config/blueprints/automation(script)/pivot/.

    Mirrors the directory structure used by the existing _install_blueprints so
    that blueprints always land at the same paths regardless of how they were
    first installed.  Only writes files whose content has changed, and uses an
    atomic temp-file swap so a crash mid-write never leaves a corrupt blueprint.

    Returns a list of relative paths that were actually written.
    """
    import shutil

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
                except Exception:
                    pass

    hass.async_create_task(_write_config_text_entities())

    # Set up internal listeners for bank control and bank sync
    unsubs = _setup_bank_control_listener(hass, entry)
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
        or MANAGEMENT_BLUEPRINTS
    )

    # Migration: Automatic (managed) mode has been removed.
    # Clean up any files it wrote and treat the device as Blueprint mode.
    if management_mode == MANAGEMENT_MANAGED:
        _LOGGER.info(
            "Pivot: '%s' was configured in Automatic mode (removed) — "
            "cleaning up managed files and switching to Blueprint mode",
            friendly_name,
        )
        await _cleanup_managed_files(hass, entry)
        management_mode = MANAGEMENT_BLUEPRINTS

    # Always clean up any old per-device blueprint files and backup files from managed mode
    await _cleanup_legacy_blueprint_files(hass, entry)

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
    unsub_button = _setup_button_event_listener(hass, entry)

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

def _setup_button_event_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Listen for VPE button press events and fire pivot_button_press on the HA bus."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    device_id = entry.data.get(CONF_DEVICE_ID)

    # Older config entries may not have device_id stored — look it up by ESPHome device name.
    if not device_id:
        esphome_name = entry.data.get(CONF_ESPHOME_DEVICE_NAME)
        if esphome_name:
            from homeassistant.helpers import device_registry as dr
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

    return async_track_state_change_event(hass, [button_entity_id], _on_button_press)


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


async def _cleanup_legacy_blueprint_files(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove old per-device blueprint files and backup files left by managed mode."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]

    def _remove():
        removed = []
        # Remove old per-device blueprint files (e.g. pivot_ha_voice_orange_announcements.yaml)
        for bp_dir in [
            hass.config.path("blueprints", "automation", "pivot"),
            hass.config.path("blueprints", "script", "pivot"),
        ]:
            if not os.path.isdir(bp_dir):
                continue
            for fname in os.listdir(bp_dir):
                if suffix in fname and fname.endswith(".yaml"):
                    try:
                        os.remove(os.path.join(bp_dir, fname))
                        removed.append(fname)
                    except OSError:
                        pass
        # Remove backup files created during managed-mode file writes
        for backup in [
            hass.config.path("automations.yaml.pivot_backup"),
            hass.config.path("scripts.yaml.pivot_backup"),
        ]:
            if os.path.exists(backup):
                try:
                    os.remove(backup)
                    removed.append(os.path.basename(backup))
                except OSError:
                    pass
        return removed

    removed = await hass.async_add_executor_job(_remove)
    if removed:
        _LOGGER.info("Pivot: removed legacy managed-mode files for %s: %s", suffix, removed)


async def _cleanup_managed_files(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove Pivot-managed files when switching away from Managed mode."""
    await _remove_bank_toggle_script(hass, entry)
    await _remove_announcements_automation(hass, entry)
    _LOGGER.info("Pivot: cleaned up managed files for %s", entry.data[CONF_DEVICE_SUFFIX])


async def _remove_bank_toggle_script(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove Pivot script files and reload."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    script_key = f"{suffix}_bank_toggle"
    pivot_script_path = hass.config.path("pivot", f"pivot_{script_key}.yaml")

    def _remove():
        # Delete our owned file (check both new subdir and old flat path)
        for path in [pivot_script_path, hass.config.path(f"pivot_{script_key}.yaml")]:
            if os.path.exists(path):
                os.remove(path)
        # Remove all Pivot content for this key from scripts.yaml
        scripts_path = hass.config.path("scripts.yaml")
        if not os.path.exists(scripts_path):
            return
        with open(scripts_path, "r") as f:
            lines = f.readlines()
        new_lines = _strip_script_lines(lines, script_key)
        if len(new_lines) != len(lines):
            with open(scripts_path, "w") as f:
                f.writelines(new_lines)

    async with _SCRIPTS_YAML_LOCK:
        await hass.async_add_executor_job(_remove)

    try:
        await hass.services.async_call("script", "reload", blocking=True)
        _LOGGER.info("Pivot: removed script.%s", script_key)
    except Exception as e:
        _LOGGER.warning("Pivot: could not reload scripts after removal: %s", e)



def _get_button_event_entity(hass: HomeAssistant, device_id: str) -> str | None:
    """Find the button press event entity for a VPE device.

    Matches the event entity with device_class 'button' on the ESPHome device.
    Falls back to any event-domain entity on the device if device_class is absent.
    """
    from homeassistant.helpers import entity_registry as er
    ent_reg = er.async_get(hass)
    fallback = None
    for entity in ent_reg.entities.values():
        if entity.device_id != device_id or entity.domain != "event":
            continue
        if (entity.original_device_class or entity.device_class) == "button":
            return entity.entity_id
        fallback = entity.entity_id  # any event entity on this device
    return fallback


async def _remove_announcements_automation(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove legacy managed-mode automation file and its include line from automations.yaml."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    automation_key = f"pivot_{suffix}_announcements"
    pivot_auto_path = hass.config.path("pivot", f"{automation_key}.yaml")
    automations_path = hass.config.path("automations.yaml")

    def _remove_automation():
        # Delete our owned file — check all known paths (current + legacy names)
        for path in [
            pivot_auto_path,
            hass.config.path("pivot", f"pivot_{automation_key}.yaml"),  # old double-prefix subdir
            hass.config.path(f"pivot_{automation_key}.yaml"),            # old double-prefix flat
        ]:
            if os.path.exists(path):
                os.remove(path)
        # Remove all Pivot content for this key from automations.yaml
        if not os.path.exists(automations_path):
            return False
        with open(automations_path, "r") as f:
            lines = f.readlines()
        new_lines = _strip_automation_lines(lines, automation_key)
        if len(new_lines) == len(lines):
            return False
        with open(automations_path, "w") as f:
            f.writelines(new_lines)
        return True

    async with _AUTOMATIONS_YAML_LOCK:
        removed = await hass.async_add_executor_job(_remove_automation)
    if removed:
        try:
            await hass.services.async_call("automation", "reload", blocking=True)
            _LOGGER.info("Pivot: removed automation %s", automation_key)
        except Exception as e:
            _LOGGER.warning("Pivot: could not reload automations after removal: %s", e)
