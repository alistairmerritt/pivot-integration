"""Push Pivot settings directly to the device via an ESPHome action.

The ESPHome state subscription cannot be relied on for startup correctness:
Home Assistant's ESPHome integration forwards only genuine state *changes*
to the device — entity-addition events (old_state=None) and same-state
writes are dropped. A device that connects and subscribes before Pivot's
entities are restored (typical during HA startup) therefore never receives
their values, and nothing self-heals until the user toggles a setting.

This module closes that hole by pushing all settings explicitly through the
firmware's `pivot_sync_settings` user-defined action.

Timing is the hard part. The push needs two things that are NOT guaranteed to
be true when EVENT_HOMEASSISTANT_STARTED fires:

1. The device must actually be REACHABLE. Note that the action existing proves
   nothing: Home Assistant registers ESPHome device actions from cached
   metadata during entry setup (`_setup_services`), so `has_service()` is true
   for a device that is powered off. Only awaiting the call — hence
   `blocking=True` in `_call` — distinguishes delivered from merely queued.
2. Pivot's own entities must be restored, or there is nothing to read.

A single attempt at "HA started" therefore loses the race intermittently, and
when it did, nothing retried — the device silently kept stale settings until
the user toggled one off and on again. So the push now fires on whichever
comes first: HA starting, or the device registering its action
(EVENT_SERVICE_REGISTERED), and retries on a backoff schedule until one
attempt actually goes out.

Devices that (re)connect while HA is already up are covered by the ESPHome
subscription itself, which sends current state on subscribe once the entities
exist. With firmware that predates the action the service never appears, the
retries expire, and a warning is logged.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DOMAIN,
    ATTR_SERVICE,
    EVENT_SERVICE_REGISTERED,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.start import async_at_started

from .const import (
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    NUM_BANKS,
    make_suffix,
)

_LOGGER = logging.getLogger(__name__)

SYNC_ACTION = "pivot_sync_settings"
SYNC_ACTION_V2 = "pivot_sync_settings_v2"

# The push needs BOTH the device connected (so the action exists) and Pivot's
# own entities restored. On an HA restart neither is guaranteed by the time
# EVENT_HOMEASSISTANT_STARTED fires, so a single attempt loses the race and the
# device keeps stale settings until the user toggles something. Retry on this
# schedule (seconds) until one attempt succeeds.
RETRY_DELAYS: tuple[int, ...] = (5, 10, 20, 30, 60, 120)

# The firmware declares v1 before v2, and Home Assistant registers each action
# as it goes. Reacting to v1 the instant it appears could therefore commit a
# v2-capable device to boolean-only repair forever, so a v1 registration waits
# this long for a v2 registration to follow.
V1_GRACE_SECONDS = 2


def setup_device_sync(hass: HomeAssistant, entry: ConfigEntry) -> list[CALLBACK_TYPE]:
    """Register the settings push at HA start.

    Returns a list of unsubscribe callbacks.
    """
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    esphome_name = entry.data.get(CONF_ESPHOME_DEVICE_NAME) or ""
    if not esphome_name:
        _LOGGER.debug(
            "Pivot: no ESPHome device name stored for %s — settings push disabled",
            suffix,
        )
        return []

    # ESPHome registers device actions as esphome.<device_name_slug>_<action>.
    # v2 carries the full state; v1 is the 11-argument boolean-only action kept
    # for firmware older than this integration. An ESPHome action requires every
    # declared argument, so calling the wrong one fails outright — hence the
    # explicit version probe rather than one call with optional fields.
    _slug = make_suffix(esphome_name)
    service_v1 = f"{_slug}_{SYNC_ACTION}"
    service_v2 = f"{_slug}_{SYNC_ACTION_V2}"

    def _read_bool(entity_id: str) -> bool | None:
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state.state == "on"

    def _read_float(entity_id: str) -> float | None:
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _read_color(entity_id: str) -> str | None:
        """Return a #RRGGBB string, or None if not a usable colour."""
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        value = state.state.strip()
        if len(value) != 7 or not value.startswith("#"):
            return None
        return value

    async def _call(service_name: str, data: dict) -> bool:
        _LOGGER.debug("Pivot: pushing settings via esphome.%s: %s", service_name, data)
        try:
            # blocking=True on purpose. Home Assistant registers ESPHome device
            # actions from CACHED metadata during setup, so has_service() is
            # true even when the device is offline. Fire-and-forget would let HA
            # swallow the connection error in its own log while we recorded a
            # success and cancelled the retries. Awaiting surfaces
            # HomeAssistantError so an unreachable device is retried instead.
            await hass.services.async_call(
                "esphome", service_name, data, blocking=True
            )
        except Exception as err:
            _LOGGER.debug(
                "Pivot: settings push via esphome.%s failed: %s", service_name, err
            )
            return False
        return True

    async def _push_settings() -> str | None:
        """Push all settings.

        Returns the action that was actually delivered, or None if the push
        could not go out. The caller needs to know WHICH action ran: a v1
        fallback is not a finished job if v2 has since appeared.
        """
        has_v2 = hass.services.has_service("esphome", service_v2)
        has_v1 = hass.services.has_service("esphome", service_v1)
        if not (has_v2 or has_v1):
            _LOGGER.debug(
                "Pivot: neither esphome.%s nor esphome.%s available yet (device "
                "not connected, or firmware without the sync action) — will retry",
                service_v2, service_v1,
            )
            return None

        sources = {
            "control_mode_in": f"switch.{suffix}_control_mode",
            "show_control_value_in": f"switch.{suffix}_show_control_value",
            "dim_when_idle_in": f"switch.{suffix}_dim_when_idle",
        }
        for bank in range(NUM_BANKS):
            sources[f"bank_mirror_{bank + 1}_in"] = (
                f"switch.{suffix}_bank_{bank + 1}_mirror_light"
            )
            sources[f"bank_passive_{bank + 1}_in"] = (
                f"binary_sensor.{suffix}_bank_{bank + 1}_passive"
            )

        data: dict[str, bool | float | int | str] = {}
        for key, entity_id in sources.items():
            value = _read_bool(entity_id)
            if value is None:
                # Never push partial defaults — leaving the device with its
                # cached values is safer than overwriting them with guesses.
                _LOGGER.debug(
                    "Pivot: %s not ready — will retry settings push", entity_id
                )
                return None
            data[key] = value

        if not has_v2:
            # Older firmware: boolean-only repair is still far better than none.
            _LOGGER.debug(
                "Pivot: esphome.%s not present — falling back to %s (booleans "
                "only). Update the firmware for full startup repair.",
                service_v2, SYNC_ACTION,
            )
            return service_v1 if await _call(service_v1, data) else None

        # Active bank, per-bank values and colours are fed by the same
        # change-only subscription and go stale the same way, so repair them
        # in the same push rather than leaving them to self-heal.
        numeric: dict[str, str] = {
            "active_bank_in": f"number.{suffix}_active_bank",
        }
        colors: dict[str, str] = {}
        for bank in range(NUM_BANKS):
            numeric[f"bank_value_{bank + 1}_in"] = (
                f"number.{suffix}_bank_{bank + 1}_value"
            )
            colors[f"bank_color_{bank + 1}_in"] = (
                f"text.{suffix}_bank_{bank + 1}_color"
            )
            # Identity colour used by the Bank Indicator — held separately from
            # the displayed colour, and stale after a restart in the same way.
            colors[f"bank_configured_color_{bank + 1}_in"] = (
                f"text.{suffix}_bank_{bank + 1}_configured_color"
            )

        for key, entity_id in numeric.items():
            value = _read_float(entity_id)
            if value is None:
                _LOGGER.debug(
                    "Pivot: %s not ready — will retry settings push", entity_id
                )
                return None
            data[key] = round(value) if key == "active_bank_in" else value

        for key, entity_id in colors.items():
            color = _read_color(entity_id)
            if color is None:
                _LOGGER.debug(
                    "Pivot: %s not ready — will retry settings push", entity_id
                )
                return None
            data[key] = color

        return service_v2 if await _call(service_v2, data) else None

    # --- retry/trigger plumbing -------------------------------------------
    done = False
    running = False
    attempt = 0
    pending_cancel: CALLBACK_TYPE | None = None

    @callback
    def _cancel_pending() -> None:
        nonlocal pending_cancel
        if pending_cancel is not None:
            pending_cancel()
            pending_cancel = None

    async def _attempt(reason: str) -> None:
        nonlocal done, running
        # `running` matters because two triggers can overlap — a v2 registration
        # arriving while a grace-delayed v1 attempt is already in flight would
        # otherwise push twice.
        if done or running:
            return
        running = True
        try:
            used = await _push_settings()
        finally:
            running = False

        if used is None:
            _schedule_retry()
            return

        if used == service_v1 and hass.services.has_service("esphome", service_v2):
            # v2 registered while this v1 call was in flight. The `running`
            # guard dropped that trigger, so without this recheck a device that
            # supports the full repair would be stuck on booleans until the next
            # restart. Not marking done: go again, now that v2 exists.
            _LOGGER.debug(
                "Pivot: esphome.%s appeared during the v1 push — upgrading",
                service_v2,
            )
            # Straight to a task, not a timer: this is a correction to a push
            # that already happened, so there is nothing to wait for.
            entry.async_create_background_task(
                hass,
                _attempt("v2 appeared during v1 push"),
                name="pivot_push_settings",
            )
            return

        done = True
        _cancel_pending()
        _LOGGER.debug("Pivot: settings push succeeded via %s (%s)", used, reason)

    @callback
    def _schedule_attempt(delay: float, reason: str) -> None:
        nonlocal pending_cancel
        if done:
            return
        _cancel_pending()

        @callback
        def _fire(_now) -> None:
            nonlocal pending_cancel
            pending_cancel = None
            entry.async_create_background_task(
                hass, _attempt(reason), name="pivot_push_settings"
            )

        pending_cancel = async_call_later(hass, delay, _fire)

    @callback
    def _schedule_retry() -> None:
        nonlocal attempt
        if done:
            return
        if attempt >= len(RETRY_DELAYS):
            _LOGGER.warning(
                "Pivot: could not deliver settings to %s after %d attempts — the "
                "device may be offline, or running firmware without %s. Its "
                "settings may not match Home Assistant until it reconnects or a "
                "setting is toggled.",
                suffix, len(RETRY_DELAYS), SYNC_ACTION_V2,
            )
            return
        delay = RETRY_DELAYS[attempt]
        attempt += 1
        _schedule_attempt(delay, f"retry after {delay}s")

    @callback
    def _on_started(_hass: HomeAssistant) -> None:
        entry.async_create_background_task(
            hass, _attempt("HA started"), name="pivot_push_settings"
        )

    @callback
    def _on_service_registered(event: Event) -> None:
        """Push when the device registers its sync action.

        Home Assistant registers these from cached metadata during setup, so
        this firing does NOT prove the device is reachable — that is what the
        blocking call in _call() establishes.
        """
        if done or event.data.get(ATTR_DOMAIN) != "esphome":
            return
        service = event.data.get(ATTR_SERVICE)
        if service == service_v2:
            entry.async_create_background_task(
                hass, _attempt("v2 action registered"), name="pivot_push_settings"
            )
        elif service == service_v1:
            # Deliberately delayed. The firmware declares v1 first, so acting on
            # it immediately would pick the boolean-only path on firmware that
            # registers v2 a moment later — and `done` would make that
            # permanent. Waiting lets v2 arrive first if it is coming.
            _schedule_attempt(V1_GRACE_SECONDS, "v1 action registered")

    # Fires once HA has fully started, or immediately if it already has
    # (e.g. on entry reload).
    return [
        async_at_started(hass, _on_started),
        hass.bus.async_listen(EVENT_SERVICE_REGISTERED, _on_service_registered),
        _cancel_pending,
    ]
