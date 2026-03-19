"""
Timer entities for Pivot — NOT USED.

HA's `timer` domain is a helper integration that does not support the standard
entity-platform forwarding mechanism used by custom integrations.  Attempting to
list "timer" in PLATFORMS causes HA to silently skip the platform setup, so the
timer.{suffix}_timer entity is never created.

The timer feature is instead implemented entirely within the pivot_timer blueprint:
  - number.{suffix}_timer_duration  — duration in minutes
  - select.{suffix}_timer_state     — idle / running / paused state mirror
  - text.{suffix}_timer_end         — ISO end-time while running, P{secs} while paused

This file is retained for reference only.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_DEVICE_SUFFIX, get_timer_definitions
from .entity_base import PivotEntity

_LOGGER = logging.getLogger(__name__)

STATUS_IDLE = "idle"
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"

ATTR_DURATION = "duration"
ATTR_REMAINING = "remaining"
ATTR_FINISHES_AT = "finishes_at"

_DEFAULT_DURATION = timedelta(minutes=25)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pivot timer entities."""
    suffix: str = config_entry.data[CONF_DEVICE_SUFFIX]
    async_add_entities([
        PivotTimer(defn, config_entry)
        for defn in get_timer_definitions(suffix)
    ])


def _timedelta_to_str(td: timedelta) -> str:
    """Format a timedelta as HH:MM:SS."""
    total = max(0, int(td.total_seconds()))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _str_to_timedelta(s: str) -> timedelta:
    """Parse HH:MM:SS string to timedelta."""
    try:
        parts = s.split(":")
        return timedelta(
            hours=int(parts[0]),
            minutes=int(parts[1]),
            seconds=int(parts[2]) if len(parts) > 2 else 0,
        )
    except (ValueError, IndexError):
        return _DEFAULT_DURATION


class PivotTimer(PivotEntity):
    """
    Timer entity for Pivot.

    Registers under the timer domain so HA's timer services (timer.start,
    timer.pause, timer.cancel, timer.finish) work natively on this entity.
    State: idle | active | paused
    Attributes: duration (HH:MM:SS), remaining (HH:MM:SS), finishes_at (ISO)
    """

    def __init__(self, definition: dict, config_entry: ConfigEntry) -> None:
        super().__init__(definition, config_entry)
        self._status: str = STATUS_IDLE
        self._duration: timedelta = _DEFAULT_DURATION
        self._remaining: timedelta = _DEFAULT_DURATION
        self._end_time: datetime | None = None
        self._unsub: Callable | None = None

    @property
    def state(self) -> str:
        return self._status

    @property
    def extra_state_attributes(self) -> dict:
        # Compute remaining dynamically when active so it's accurate on each read
        if self._status == STATUS_ACTIVE and self._end_time:
            remaining = max(timedelta(0), self._end_time - datetime.now(timezone.utc))
        else:
            remaining = self._remaining

        attrs: dict = {
            ATTR_DURATION: _timedelta_to_str(self._duration),
            ATTR_REMAINING: _timedelta_to_str(remaining),
        }
        if self._end_time:
            attrs[ATTR_FINISHES_AT] = self._end_time.isoformat()
        return attrs

    # ------------------------------------------------------------------
    # Service handlers (called by HA's timer.* services)
    # ------------------------------------------------------------------

    async def async_start(self, duration: timedelta = timedelta()) -> None:
        """Start or resume the timer."""
        if self._status == STATUS_PAUSED and not duration.total_seconds():
            # Resume: use stored remaining time
            start_remaining = self._remaining
        else:
            # Fresh start or explicit duration override
            if duration.total_seconds() > 0:
                self._duration = duration
                self._remaining = duration
            start_remaining = self._remaining

        self._end_time = datetime.now(timezone.utc) + start_remaining
        self._status = STATUS_ACTIVE
        self._cancel_unsub()
        self._unsub = async_track_point_in_time(
            self.hass, self._async_finished_callback, self._end_time
        )
        self.async_write_ha_state()

    async def async_pause(self) -> None:
        """Pause the timer."""
        if self._status != STATUS_ACTIVE:
            return
        self._remaining = max(timedelta(0), self._end_time - datetime.now(timezone.utc))
        self._end_time = None
        self._status = STATUS_PAUSED
        self._cancel_unsub()
        self.async_write_ha_state()

    async def async_cancel(self) -> None:
        """Cancel and reset the timer."""
        self._cancel_unsub()
        self._status = STATUS_IDLE
        self._remaining = self._duration
        self._end_time = None
        self.async_write_ha_state()

    async def async_finish(self) -> None:
        """Mark the timer as finished and fire the timer.finished event."""
        self._cancel_unsub()
        self._status = STATUS_IDLE
        self._remaining = timedelta(0)
        self._end_time = None
        self.async_write_ha_state()
        self.hass.bus.async_fire(
            "timer.finished",
            {"entity_id": self.entity_id, "name": self.name},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @callback
    def _async_finished_callback(self, _now: datetime) -> None:
        self.hass.async_create_task(self.async_finish())

    def _cancel_unsub(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_unsub()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            self.async_write_ha_state()
            return

        status = last_state.state
        if status not in (STATUS_IDLE, STATUS_ACTIVE, STATUS_PAUSED):
            status = STATUS_IDLE

        duration_str = last_state.attributes.get(ATTR_DURATION, "")
        if duration_str:
            self._duration = _str_to_timedelta(duration_str)

        if status == STATUS_ACTIVE:
            finishes_at_str = last_state.attributes.get(ATTR_FINISHES_AT)
            if finishes_at_str:
                try:
                    finishes_at = datetime.fromisoformat(finishes_at_str)
                    now = datetime.now(timezone.utc)
                    if finishes_at <= now:
                        # Would have already finished during HA downtime
                        self._status = STATUS_IDLE
                        self._remaining = timedelta(0)
                    else:
                        self._remaining = finishes_at - now
                        self._end_time = finishes_at
                        self._status = STATUS_ACTIVE
                        self._unsub = async_track_point_in_time(
                            self.hass, self._async_finished_callback, finishes_at
                        )
                except (ValueError, TypeError):
                    self._status = STATUS_IDLE
            else:
                self._status = STATUS_IDLE

        elif status == STATUS_PAUSED:
            remaining_str = last_state.attributes.get(ATTR_REMAINING, "")
            self._status = STATUS_PAUSED
            if remaining_str:
                self._remaining = _str_to_timedelta(remaining_str)

        else:
            self._status = STATUS_IDLE
            self._remaining = self._duration

        self.async_write_ha_state()
