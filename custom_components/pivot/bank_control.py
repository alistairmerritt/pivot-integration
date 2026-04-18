"""Bank control listeners: knob turns, bank switching, entity sync, and assignment changes."""
from __future__ import annotations

import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Context, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .announcements import ANNOUNCEABLE_DOMAINS, do_tts, format_value_announcement
from .const import CONF_DEVICE_SUFFIX, NUM_BANKS, PASSIVE_DOMAINS
from .entity_mappings import apply_value_to_entity, sync_value_from_entity

_LOGGER = logging.getLogger(__name__)

# How long (seconds) to ignore entity state changes after Pivot applied a value.
# Covers the transition period during which the entity reports intermediate values,
# which would otherwise sync back and cause an oscillation loop.
_SYNC_COOLDOWN_SECS = 2.0

# Domains that receive a debounced service call rather than an immediate one.
# Cloud-connected and protocol-limited devices (climate, cover, media_player) can
# become unresponsive or drop commands if flooded with rapid updates while the
# knob is being turned quickly. The debounce fires only after the knob settles.
# Lights and fans are kept immediate so dimming and fan-speed feel real-time.
_DEBOUNCE_DOMAINS: frozenset[str] = frozenset({"climate", "cover", "media_player"})
_DEBOUNCE_DELAY_SECS: float = 0.4


def setup_bank_control_listener(
    hass: HomeAssistant, entry: ConfigEntry,
    tts_entity: str = "",
    media_player: str = "",
    announce_enabled: bool = False,
    announce_cancels: dict[int, CALLBACK_TYPE] | None = None,
) -> list:
    """Register state change listeners for bank control and sync.

    Two triggers handled internally:

    1. Knob turn — number.{suffix}_bank_X_value changes
       -> read assigned entity from text.{suffix}_bank_X_entity
       -> call the appropriate service to apply the value

    2. Bank switch — number.{suffix}_active_bank changes
       -> read the newly active bank's assigned entity
       -> read that entity's current state
       -> sync the value back to number.{suffix}_bank_X_value
       so the knob always starts from the real current value

    Returns list of unsubscribe callbacks.
    """
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    if announce_cancels is None:
        announce_cancels = {}

    bank_value_entity_ids = [
        f"number.{suffix}_bank_{bank + 1}_value" for bank in range(NUM_BANKS)
    ]
    active_bank_entity_id = f"number.{suffix}_active_bank"

    # monotonic timestamp of the last time Pivot applied a value to each bank's entity.
    # Used alongside the parent_id context guard:
    # - parent_id guard: prevents re-applying the value when a sync write triggers
    #   _on_bank_value_changed (the write carries parent_id="pivot_sync").
    # - cooldown: prevents syncing intermediate transition values back to the gauge
    #   during the period after Pivot issues a service call (e.g. a light fading).
    # Both guards are needed — they protect against different feedback paths.
    _entity_apply_cooldown: dict[int, float] = {}

    # Pending debounce cancel handles for slow domains (climate, cover, media_player).
    # Each entry is the cancel callback returned by async_call_later.
    # Replaced on every knob tick and fired once the knob settles.
    _apply_debounce_cancels: dict[int, CALLBACK_TYPE] = {}

    @callback
    def _on_bank_value_changed(event) -> None:
        """Apply bank value to the assigned entity when knob is turned."""
        changed_entity_id = event.data.get("entity_id", "")
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state in ("unknown", "unavailable", ""):
            return
        if old_state is not None and old_state.state == new_state.state:
            return

        bank_idx = None
        for bank in range(NUM_BANKS):
            if changed_entity_id == f"number.{suffix}_bank_{bank + 1}_value":
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
        # Bank value changes from sync_value_from_entity and bank-switch syncs are
        # issued as HA service calls, so their state change carries a non-None
        # context.parent_id. Ignoring those prevents pivot_knob_turn from firing
        # when an external source causes a sync update, and stops the value being
        # needlessly re-applied to the entity a second time.
        if new_state.context.parent_id is not None:
            return

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx + 1}_entity")
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

        # Skip passive domains — knob does nothing for scenes/scripts/switches
        if domain in PASSIVE_DOMAINS:
            return

        try:
            value = float(new_state.state)
        except ValueError:
            return

        if domain in _DEBOUNCE_DOMAINS:
            # Cancel any pending call for this bank and reschedule.
            # The actual service call fires once the knob settles (_DEBOUNCE_DELAY_SECS
            # after the last tick). This prevents flooding cloud-connected devices
            # (climate, cover, media_player) with rapid commands while turning quickly.
            existing = _apply_debounce_cancels.pop(bank_idx, None)
            if existing:
                existing()

            _bd = bank_entity
            _bv = value
            _bi = bank_idx

            @callback
            def _fire_apply(_now=None, bd=_bd, bv=_bv, bi=_bi) -> None:
                _apply_debounce_cancels.pop(bi, None)
                _entity_apply_cooldown[bi] = time.monotonic()
                hass.async_create_task(
                    apply_value_to_entity(hass, domain, bd, bv)
                )

            _apply_debounce_cancels[bank_idx] = async_call_later(
                hass, _DEBOUNCE_DELAY_SECS, _fire_apply
            )
        else:
            # Lights, fans, and other fast-response domains: apply immediately
            # so dimming and speed control feel real-time.
            _entity_apply_cooldown[bank_idx] = time.monotonic()
            hass.async_create_task(
                apply_value_to_entity(hass, domain, bank_entity, value)
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
        # Note: uses the knob position for the announcement message, not the entity's
        # actual attribute value, because the entity may still be transitioning.
        # System announcements (switch.{suffix}_announcements) are independent of this —
        # value announcements are gated only by switch.{suffix}_bank_N_announce_value
        # and switch.{suffix}_mute_announcements.
        if announce_enabled and tts_entity and media_player and "." in bank_entity:
            ann_domain = bank_entity.split(".")[0]
            if ann_domain in ANNOUNCEABLE_DOMAINS:
                ann_switch = hass.states.get(f"switch.{suffix}_bank_{bank_idx + 1}_announce_value")
                if ann_switch and ann_switch.state == "on":
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
                        msg = format_value_announcement(hass, be, bv)
                        if msg:
                            hass.async_create_task(do_tts(hass, tts_entity, media_player, msg))

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

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx + 1}_entity")
        bank_entity = (
            text_state.state
            if text_state and text_state.state not in ("", "unknown", "unavailable")
            else ""
        )

        hass.bus.async_fire(
            "pivot_bank_changed",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,  # 1-based
                "bank_entity": bank_entity,
            },
        )

        # Cancel any pending value-announcement debounces on bank switch
        for _bi, _cancel in list(announce_cancels.items()):
            announce_cancels.pop(_bi, None)
            _cancel()

        # Native bank change announcement (system announcement, not value announcement)
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
                hass.async_create_task(do_tts(hass, tts_entity, media_player, _name))

        if not bank_entity:
            return

        # Timer bank: sync current duration to gauge when idle
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
            value_entity_id = f"number.{suffix}_bank_{bank_idx + 1}_value"
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
        value_entity_id = f"number.{suffix}_bank_{bank_idx + 1}_value"

        # Passive banks (scene/script/switch) have no controllable value — zero the gauge
        if domain in PASSIVE_DOMAINS:
            hass.async_create_task(
                hass.services.async_call(
                    "number", "set_value",
                    {"entity_id": value_entity_id, "value": 0},
                    blocking=False,
                )
            )
            return

        hass.async_create_task(
            sync_value_from_entity(hass, domain, bank_entity, value_entity_id)
        )

    # ── Live entity sync ────────────────────────────────────────────────────
    # Keeps the LED gauge in sync when an assigned entity is changed externally
    # (e.g. voice command, another dashboard, or a physical switch).

    @callback
    def _on_assigned_entity_changed(event) -> None:
        """Sync bank value when an assigned entity changes externally."""
        changed_entity_id = event.data.get("entity_id", "")
        new_state = event.data.get("new_state")

        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return

        for bank in range(NUM_BANKS):
            text_state = hass.states.get(f"text.{suffix}_bank_{bank + 1}_entity")
            if text_state is None or text_state.state != changed_entity_id:
                continue
            domain = changed_entity_id.split(".")[0]
            if domain not in ANNOUNCEABLE_DOMAINS:
                continue

            # Skip if Pivot just applied a value to this entity — the entity
            # is still transitioning and these are not external changes.
            if time.monotonic() - _entity_apply_cooldown.get(bank, 0) < _SYNC_COOLDOWN_SECS:
                continue

            value_entity_id = f"number.{suffix}_bank_{bank + 1}_value"
            hass.async_create_task(
                sync_value_from_entity(hass, domain, changed_entity_id, value_entity_id)
            )

    _assigned_entity_unsubs: list = []

    def _register_assigned_entity_watchers() -> None:
        """(Re-)register state watchers for all currently assigned entities."""
        for u in _assigned_entity_unsubs:
            u()
        _assigned_entity_unsubs.clear()
        entities = []
        for bank in range(NUM_BANKS):
            text_state = hass.states.get(f"text.{suffix}_bank_{bank + 1}_entity")
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

        # If the active bank was just reassigned to a passive entity, zero the gauge.
        # Non-active banks are handled lazily when the user next switches to them.
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("", "unknown", "unavailable"):
            return
        changed_entity_text_id = event.data.get("entity_id", "")
        bank_idx = None
        for bank in range(NUM_BANKS):
            if changed_entity_text_id == f"text.{suffix}_bank_{bank + 1}_entity":
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
        if domain in PASSIVE_DOMAINS:
            value_entity_id = f"number.{suffix}_bank_{bank_idx + 1}_value"
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
        [f"text.{suffix}_bank_{bank + 1}_entity" for bank in range(NUM_BANKS)],
        _on_bank_assignment_changed,
    )

    return (
        [unsub_values, unsub_active, unsub_assignments]
        + [lambda: [u() for u in _assigned_entity_unsubs]]
    )
